from django.contrib import messages as flash
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.core import models
from apps.core.mail import send_test_email as send_test_email_message

from .forms import (
    DashboardLoginForm,
    MessageStatusForm,
    ProjectForm,
    ProjectImageFormSet,
    ProjectMetricFormSet,
)
from .registry import COLLECTIONS, NAVIGATION, SINGLETONS


def staff_required(view):
    return user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url="dashboard:login",
    )(view)


class DashboardLoginView(LoginView):
    template_name = "dashboard/login.html"
    form_class = DashboardLoginForm
    redirect_authenticated_user = True


@require_POST
def dashboard_logout(request):
    logout(request)
    return redirect("dashboard:login")


def _base_context(request, active=None, title=""):
    return {
        "navigation": NAVIGATION,
        "singletons": SINGLETONS,
        "collections": COLLECTIONS,
        "active": active,
        "page_title": title,
        "unread_count": models.ContactMessage.objects.filter(status="new").count(),
    }


# --------------------------------------------------------------------------- #
# Overview
# --------------------------------------------------------------------------- #
@staff_required
def index(request):
    context = _base_context(request, active="dashboard:index", title="Dashboard")
    context.update(
        {
            "counts": [
                ("Services", models.Service.objects.filter(is_active=True).count(), "services"),
                ("Projects", models.Project.objects.filter(is_active=True).count(), "projects"),
                ("Testimonials", models.Testimonial.objects.filter(is_active=True).count(), "testimonials"),
                ("Statistics", models.Stat.objects.filter(is_active=True).count(), "stats"),
            ],
            "new_messages": models.ContactMessage.objects.filter(status="new").count(),
            "total_messages": models.ContactMessage.objects.count(),
            "recent_messages": models.ContactMessage.objects.all()[:6],
            "missing_images": _missing_images(),
        }
    )
    return render(request, "dashboard/index.html", context)


def _missing_images():
    """Content that still shows a placeholder instead of a real image."""
    gaps = []
    about = models.AboutSection.load()
    if not about.image:
        gaps.append(("About section photo", reverse("dashboard:singleton", args=["about"])))
    for project in models.Project.objects.filter(is_active=True):
        if not project.image:
            gaps.append(
                (
                    f"Project image — {project.title}",
                    reverse("dashboard:project_edit", args=[project.pk]),
                )
            )
    for testimonial in models.Testimonial.objects.filter(is_active=True):
        if not testimonial.avatar:
            gaps.append(
                (
                    f"Avatar — {testimonial.author_name}",
                    reverse("dashboard:collection_edit", args=["testimonials", testimonial.pk]),
                )
            )
    settings_obj = models.SiteSettings.load()
    if not settings_obj.logo_mark:
        gaps.append(("Logo mark", reverse("dashboard:singleton", args=["site"])))
    return gaps


# --------------------------------------------------------------------------- #
# Singleton sections
# --------------------------------------------------------------------------- #
@staff_required
def singleton(request, key):
    spec = SINGLETONS.get(key)
    if not spec:
        raise Http404
    instance = spec["model"].load()
    form_class = spec["form"]

    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            flash.success(request, f"{spec['label']} saved.")
            return redirect("dashboard:singleton", key=key)
        flash.error(request, "Please fix the highlighted fields.")
    else:
        form = form_class(instance=instance)

    context = _base_context(request, active=f"singleton:{key}", title=spec["label"])
    context.update(
        {
            "form": form,
            "spec": spec,
            "key": key,
            "instance": instance,
            "field_groups": _grouped_fields(form, spec.get("groups")),
        }
    )
    return render(request, spec.get("template", "dashboard/singleton_form.html"), context)


@staff_required
@require_POST
def send_test_email(request):
    """Prove the saved SMTP settings actually deliver."""
    config = models.EmailSettings.load()
    recipient = (
        request.POST.get("recipient", "").strip()
        or config.notify_email
        or (request.user.email or "")
    )
    if not recipient:
        flash.error(
            request,
            "Add an address to send the test to (or fill in “Send enquiries to”).",
        )
        return redirect("dashboard:singleton", key="email")

    ok, error = send_test_email_message(recipient)
    if ok:
        flash.success(request, f"Test email sent to {recipient}. Check the inbox.")
    else:
        flash.error(request, f"Could not send: {error}")
    return redirect("dashboard:singleton", key="email")


def _grouped_fields(form, groups):
    """Split a form's fields into the labelled groups declared in the registry."""
    if not groups:
        return [(None, list(form))]
    by_name = {field.name: field for field in form}
    result, used = [], set()
    for title, names in groups:
        fields = [by_name[name] for name in names if name in by_name]
        used.update(name for name in names if name in by_name)
        if fields:
            result.append((title, fields))
    leftovers = [field for name, field in by_name.items() if name not in used]
    if leftovers:
        result.append(("Other", leftovers))
    return result


# --------------------------------------------------------------------------- #
# Collections
# --------------------------------------------------------------------------- #
def _get_collection(key):
    spec = COLLECTIONS.get(key)
    if not spec:
        raise Http404
    return spec


@staff_required
def collection_list(request, key):
    spec = _get_collection(key)
    queryset = spec["model"].objects.all()
    if spec.get("select_related"):
        queryset = queryset.select_related(*spec["select_related"])

    search = request.GET.get("q", "").strip()
    if search:
        first_field = spec["columns"][0][0]
        queryset = queryset.filter(**{f"{first_field}__icontains": search})

    paginator = Paginator(queryset, 25)
    page = paginator.get_page(request.GET.get("page"))

    rows = []
    for obj in page.object_list:
        rows.append(
            {
                "obj": obj,
                "values": [_display(obj, name) for name, _ in spec["columns"]],
                "image": getattr(obj, spec["image_field"], None)
                if spec.get("image_field")
                else None,
                "edit_url": reverse(
                    spec.get("detail_view", "dashboard:collection_edit"),
                    args=[obj.pk] if spec.get("detail_view") else [key, obj.pk],
                ),
            }
        )

    context = _base_context(request, active=f"collection:{key}", title=spec["label"])
    context.update({"spec": spec, "key": key, "rows": rows, "page": page, "search": search})
    return render(request, "dashboard/collection_list.html", context)


def _display(obj, name):
    value = getattr(obj, name, "")
    display = getattr(obj, f"get_{name}_display", None)
    if callable(display):
        value = display()
    return value


@staff_required
def collection_create(request, key):
    spec = _get_collection(key)
    form_class = spec["form"]
    if request.method == "POST":
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            flash.success(request, f"{spec['singular'].capitalize()} added.")
            if spec.get("detail_view"):
                return redirect(spec["detail_view"], pk=obj.pk)
            return redirect("dashboard:collection_list", key=key)
        flash.error(request, "Please fix the highlighted fields.")
    else:
        form = form_class(initial={"order": _next_order(spec["model"])})

    context = _base_context(
        request, active=f"collection:{key}", title=f"New {spec['singular']}"
    )
    context.update({"form": form, "spec": spec, "key": key, "object": None})
    return render(request, "dashboard/collection_form.html", context)


def _next_order(model_cls):
    last = model_cls.objects.order_by("-order").first()
    return (last.order + 1) if last else 0


@staff_required
def collection_edit(request, key, pk):
    spec = _get_collection(key)
    obj = get_object_or_404(spec["model"], pk=pk)
    form_class = spec["form"]
    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            flash.success(request, f"{spec['singular'].capitalize()} saved.")
            return redirect("dashboard:collection_list", key=key)
        flash.error(request, "Please fix the highlighted fields.")
    else:
        form = form_class(instance=obj)

    context = _base_context(request, active=f"collection:{key}", title=str(obj))
    context.update({"form": form, "spec": spec, "key": key, "object": obj})
    return render(request, "dashboard/collection_form.html", context)


@staff_required
@require_POST
def collection_delete(request, key, pk):
    spec = _get_collection(key)
    obj = get_object_or_404(spec["model"], pk=pk)
    try:
        obj.delete()
        flash.success(request, f"{spec['singular'].capitalize()} deleted.")
    except Exception:
        flash.error(
            request,
            f"This {spec['singular']} is still used elsewhere and cannot be deleted.",
        )
    return redirect("dashboard:collection_list", key=key)


@staff_required
@require_POST
def collection_toggle(request, key, pk):
    """Show/hide an item straight from the list."""
    spec = _get_collection(key)
    obj = get_object_or_404(spec["model"], pk=pk)
    obj.is_active = not obj.is_active
    obj.save(update_fields=["is_active"])
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "is_active": obj.is_active})
    return redirect("dashboard:collection_list", key=key)


# --------------------------------------------------------------------------- #
# Projects (with metrics + gallery)
# --------------------------------------------------------------------------- #
@staff_required
def project_edit(request, pk):
    project = get_object_or_404(models.Project, pk=pk)
    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES, instance=project)
        metrics = ProjectMetricFormSet(request.POST, instance=project, prefix="metrics")
        gallery = ProjectImageFormSet(
            request.POST, request.FILES, instance=project, prefix="gallery"
        )
        if form.is_valid() and metrics.is_valid() and gallery.is_valid():
            form.save()
            metrics.save()
            gallery.save()
            flash.success(request, "Project saved.")
            return redirect("dashboard:collection_list", key="projects")
        flash.error(request, "Please fix the highlighted fields.")
    else:
        form = ProjectForm(instance=project)
        metrics = ProjectMetricFormSet(instance=project, prefix="metrics")
        gallery = ProjectImageFormSet(instance=project, prefix="gallery")

    context = _base_context(request, active="collection:projects", title=project.title)
    context.update(
        {
            "form": form,
            "metrics": metrics,
            "gallery": gallery,
            "object": project,
            "spec": COLLECTIONS["projects"],
            "key": "projects",
        }
    )
    return render(request, "dashboard/project_form.html", context)


# --------------------------------------------------------------------------- #
# Enquiries
# --------------------------------------------------------------------------- #
@staff_required
def message_list(request):
    queryset = models.ContactMessage.objects.all()
    status = request.GET.get("status", "")
    if status in dict(models.ContactMessage.STATUS_CHOICES):
        queryset = queryset.filter(status=status)
    search = request.GET.get("q", "").strip()
    if search:
        queryset = queryset.filter(name__icontains=search)

    paginator = Paginator(queryset, 20)
    page = paginator.get_page(request.GET.get("page"))

    context = _base_context(request, active="dashboard:messages", title="Enquiries")
    context.update(
        {
            "page": page,
            "status": status,
            "search": search,
            "status_choices": models.ContactMessage.STATUS_CHOICES,
        }
    )
    return render(request, "dashboard/messages.html", context)


@staff_required
def message_detail(request, pk):
    message = get_object_or_404(models.ContactMessage, pk=pk)
    if message.status == "new":
        message.status = "read"
        message.save(update_fields=["status"])

    if request.method == "POST":
        form = MessageStatusForm(request.POST, instance=message)
        if form.is_valid():
            form.save()
            flash.success(request, "Status updated.")
            return redirect("dashboard:message_detail", pk=pk)
    else:
        form = MessageStatusForm(instance=message)

    context = _base_context(request, active="dashboard:messages", title=message.subject)
    context.update({"message": message, "form": form})
    return render(request, "dashboard/message_detail.html", context)


@staff_required
@require_POST
def message_delete(request, pk):
    message = get_object_or_404(models.ContactMessage, pk=pk)
    message.delete()
    flash.success(request, "Enquiry deleted.")
    return redirect("dashboard:messages")
