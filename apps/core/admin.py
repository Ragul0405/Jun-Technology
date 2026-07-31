"""
Django admin registrations.

The custom super-admin dashboard at /dashboard/ is the intended editing
surface; these registrations exist as a technical fallback for developers.
"""

from django.contrib import admin

from . import models


class MetricInline(admin.TabularInline):
    model = models.ProjectMetric
    extra = 1


class GalleryInline(admin.TabularInline):
    model = models.ProjectImage
    extra = 1


class FooterLinkInline(admin.TabularInline):
    model = models.FooterLink
    extra = 1


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "stack", "order", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("title", "stack", "short_description")
    inlines = [MetricInline, GalleryInline]


@admin.register(models.FooterColumn)
class FooterColumnAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active")
    inlines = [FooterLinkInline]


@admin.register(models.ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "phone", "subject", "message",
                       "ip_address", "user_agent", "created_at")


for model in (
    models.SiteSettings,
    models.NavLink,
    models.HeroSection,
    models.HeroHighlight,
    models.Stat,
    models.AboutSection,
    models.AboutCard,
    models.ServicesSection,
    models.Service,
    models.PortfolioSection,
    models.ProjectCategory,
    models.TestimonialsSection,
    models.Testimonial,
    models.ContactSection,
    models.ContactDetail,
    models.EmailSettings,
    models.FooterSettings,
    models.SocialLink,
):
    admin.site.register(model)

admin.site.site_header = "Jun Technology"
admin.site.site_title = "Jun Technology"
admin.site.index_title = "Technical administration"
