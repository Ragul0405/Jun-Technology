import logging

from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import ContactForm
from .mail import send_enquiry_notification
from .models import (
    AboutCard,
    AboutImage,
    AboutSection,
    BlogCategory,
    BlogPost,
    BlogSection,
    ContactDetail,
    ContactSection,
    ContentPage,
    FaqItem,
    FaqSection,
    FooterColumn,
    FooterSettings,
    HeroHighlight,
    HeroSection,
    MAX_ABOUT_IMAGES,
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


#: How many projects the home page shows before sending visitors to the
#: full listing page.
HOME_PROJECT_LIMIT = 6

#: Same idea for the home page's blog section.
HOME_BLOG_LIMIT = 6


def _visible_projects():
    return (
        Project.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("metrics", "gallery")
    )


def home(request):
    total = _visible_projects().count()
    projects = list(_visible_projects()[:HOME_PROJECT_LIMIT])

    published = BlogPost.objects.filter(is_active=True).select_related("category")
    post_total = published.count()
    posts = list(published[:HOME_BLOG_LIMIT])

    context = {
        "is_home": True,
        "project_total": total,
        "more_projects": total > len(projects),
        # `site` (the SiteSettings row) is supplied by the context processor.
        "nav_links": NavLink.objects.filter(is_active=True),
        "hero": HeroSection.load(),
        "hero_highlights": HeroHighlight.objects.filter(is_active=True),
        "featured_projects": Project.featured(),
        "stats": Stat.objects.filter(is_active=True),
        "about": AboutSection.load(),
        "about_images": AboutImage.objects.filter(is_active=True)[:MAX_ABOUT_IMAGES],
        "about_cards": AboutCard.objects.filter(is_active=True),
        "services_section": ServicesSection.load(),
        "services": Service.objects.filter(is_active=True),
        "footer_services": Service.objects.filter(is_active=True, show_in_footer=True),
        "portfolio_section": PortfolioSection.load(),
        "categories": ProjectCategory.objects.filter(is_active=True),
        "projects": projects,
        "projects_data": _projects_payload(projects),
        "blog_section": BlogSection.load(),
        "blog_posts": posts,
        "blog_total": post_total,
        "more_blog_posts": post_total > len(posts),
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


def projects(request):
    """Every project, optionally narrowed to one category via `?category=`."""
    categories = ProjectCategory.objects.filter(is_active=True)
    wanted = (request.GET.get("category") or "").strip()
    active = categories.filter(slug=wanted).first() if wanted else None

    visible = _visible_projects()
    if active:
        visible = visible.filter(category=active)
    visible = list(visible)

    context = {
        "is_home": False,
        "footer_services": Service.objects.filter(is_active=True, show_in_footer=True),
        "portfolio_section": PortfolioSection.load(),
        "categories": categories,
        "active_category": active,
        "projects": visible,
        "projects_data": _projects_payload(visible),
        "nav_links": NavLink.objects.filter(is_active=True),
        "contact": ContactSection.load(),
        "footer": FooterSettings.load(),
        "footer_columns": FooterColumn.objects.filter(is_active=True).prefetch_related(
            "links"
        ),
        "social_links": SocialLink.objects.filter(is_active=True),
    }
    return render(request, "site/projects.html", context)


#: Posts per page on the blog list.
BLOG_PAGE_SIZE = 9


def _chrome(**extra):
    """Header, footer and cursor context every standalone page needs."""
    context = {
        "is_home": False,
        "footer_services": Service.objects.filter(is_active=True, show_in_footer=True),
        "nav_links": NavLink.objects.filter(is_active=True),
        "contact": ContactSection.load(),
        "footer": FooterSettings.load(),
        "footer_columns": FooterColumn.objects.filter(is_active=True).prefetch_related(
            "links"
        ),
        "social_links": SocialLink.objects.filter(is_active=True),
    }
    context.update(extra)
    return context


def blog(request):
    categories = BlogCategory.objects.filter(is_active=True)
    wanted = (request.GET.get("category") or "").strip()
    active = categories.filter(slug=wanted).first() if wanted else None

    posts = BlogPost.objects.filter(is_active=True).select_related("category")
    if active:
        posts = posts.filter(category=active)

    page = Paginator(posts, BLOG_PAGE_SIZE).get_page(request.GET.get("page"))
    return render(
        request,
        "site/blog.html",
        _chrome(
            blog_section=BlogSection.load(),
            blog_categories=categories,
            active_category=active,
            page=page,
            posts=page.object_list,
        ),
    )


def blog_post(request, slug):
    post = get_object_or_404(
        BlogPost.objects.select_related("category"), slug=slug, is_active=True
    )
    # Prefer more from the same category, then fall back to anything recent.
    others = list(
        BlogPost.objects.filter(is_active=True, category=post.category)
        .exclude(pk=post.pk)[:3]
        if post.category_id
        else []
    )
    if len(others) < 3:
        seen = [post.pk] + [o.pk for o in others]
        others += list(
            BlogPost.objects.filter(is_active=True).exclude(pk__in=seen)[: 3 - len(others)]
        )
    return render(
        request,
        "site/blog_post.html",
        _chrome(blog_section=BlogSection.load(), post=post, more_posts=others),
    )


def content_page(request, slug):
    """Terms, privacy policy — any plain prose page."""
    page = get_object_or_404(ContentPage, slug=slug, is_active=True)
    return render(request, "site/content_page.html", _chrome(page=page))


def services(request):
    """Every service, one page — linked from the footer's "Services" link."""
    return render(
        request,
        "site/services.html",
        _chrome(
            services_section=ServicesSection.load(),
            services=Service.objects.filter(is_active=True),
        ),
    )


def service_detail(request, slug):
    """One service's own page, linked from the "Our core services" cards."""
    service = get_object_or_404(Service, slug=slug, is_active=True)
    others = Service.objects.filter(is_active=True).exclude(pk=service.pk)[:3]
    return render(
        request,
        "site/service_detail.html",
        _chrome(
            services_section=ServicesSection.load(),
            service=service,
            other_services=others,
        ),
    )


def faq(request):
    return render(
        request,
        "site/faq.html",
        _chrome(
            faq_section=FaqSection.load(),
            faqs=FaqItem.objects.filter(is_active=True),
        ),
    )


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
