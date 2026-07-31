import logging

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import ContactForm
from .mail import send_enquiry_notification
from .models import (
    AboutCard,
    AboutSection,
    ContactDetail,
    ContactSection,
    FooterColumn,
    FooterSettings,
    HeroHighlight,
    HeroSection,
    NavLink,
    PortfolioSection,
    Project,
    ProjectCategory,
    Service,
    ServicesSection,
    SocialLink,
    Stat,
    Testimonial,
    TestimonialsSection,
)

logger = logging.getLogger(__name__)


def _projects_payload(projects):
    """Data the pop-up needs, serialised once for the client-side modal."""
    payload = []
    for project in projects:
        payload.append(
            {
                "title": project.title,
                "category": project.category.name if project.category_id else "",
                "stack": project.stack,
                "description": project.description or project.short_description,
                "image": project.hero_image.url if project.hero_image else "",
                "url": project.external_url,
                "metrics": [
                    {"value": m.value, "label": m.label}
                    for m in project.metrics.filter(is_active=True)
                ],
                "gallery": [
                    {"image": g.image.url, "caption": g.caption}
                    for g in project.gallery.filter(is_active=True)
                    if g.image
                ],
            }
        )
    return payload


def home(request):
    projects = (
        Project.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("metrics", "gallery")
    )

    context = {
        # `site` (the SiteSettings row) is supplied by the context processor.
        "nav_links": NavLink.objects.filter(is_active=True),
        "hero": HeroSection.load(),
        "hero_highlights": HeroHighlight.objects.filter(is_active=True),
        "stats": Stat.objects.filter(is_active=True),
        "about": AboutSection.load(),
        "about_cards": AboutCard.objects.filter(is_active=True),
        "services_section": ServicesSection.load(),
        "services": Service.objects.filter(is_active=True),
        "portfolio_section": PortfolioSection.load(),
        "categories": ProjectCategory.objects.filter(is_active=True),
        "projects": projects,
        "projects_data": _projects_payload(projects),
        "testimonials_section": TestimonialsSection.load(),
        "testimonials": Testimonial.objects.filter(is_active=True),
        "contact": ContactSection.load(),
        "contact_details": ContactDetail.objects.filter(is_active=True),
        "footer": FooterSettings.load(),
        "footer_columns": FooterColumn.objects.filter(is_active=True).prefetch_related(
            "links"
        ),
        "social_links": SocialLink.objects.filter(is_active=True),
    }
    return render(request, "site/index.html", context)


@require_POST
def contact_submit(request):
    form = ContactForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    message = form.save(commit=False)
    message.ip_address = _client_ip(request)
    message.user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]
    message.save()

    # Never let a mail problem affect the visitor — the enquiry is already saved.
    send_enquiry_notification(message)

    return JsonResponse({"ok": True})


def robots_txt(request):
    """Let crawlers index the site but keep them out of the admin areas."""
    sitemap_url = request.build_absolute_uri(reverse("sitemap"))
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /dashboard/",
        "Disallow: /django-admin/",
        "Disallow: /contact/submit/",
        "",
        f"Sitemap: {sitemap_url}",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def handler404(request, exception=None):  # pragma: no cover - trivial
    return render(request, "site/404.html", status=404)


def handler500(request):  # pragma: no cover - trivial
    return render(request, "site/500.html", status=500)
