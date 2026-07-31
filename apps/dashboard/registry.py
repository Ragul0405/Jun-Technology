"""
Declarative map of every editable piece of the website.

Adding a new section to the dashboard means adding one entry here — the views,
navigation and templates are generic.
"""

from apps.core import models

from . import forms

# --------------------------------------------------------------------------- #
# One-row sections (page copy)
# --------------------------------------------------------------------------- #
SINGLETONS = {
    "site": {
        "label": "Brand & SEO",
        "model": models.SiteSettings,
        "form": forms.SiteSettingsForm,
        "description": "Logo, brand name, colours, theme defaults and meta tags.",
        "groups": [
            ("Brand", ["brand_prefix", "brand_suffix", "brand_tagline", "logo_mark", "favicon"]),
            ("Header call to action", ["nav_cta_label", "nav_cta_url"]),
            (
                "Appearance",
                [
                    "default_theme",
                    "accent_primary",
                    "accent_secondary",
                    "show_loader",
                    "custom_cursor",
                    "show_particles",
                ],
            ),
            (
                "Search engines & sharing",
                [
                    "meta_title",
                    "meta_description",
                    "meta_keywords",
                    "og_image",
                    "canonical_url",
                    "google_analytics_id",
                ],
            ),
        ],
    },
    "hero": {
        "label": "Hero section",
        "model": models.HeroSection,
        "form": forms.HeroSectionForm,
        "description": "Headline, badge, buttons and the floating build-health panel.",
        "groups": [
            ("Badge", ["show_badge", "badge_text"]),
            ("Headline", ["title_line_1", "title_line_2", "title_line_3", "subtitle"]),
            (
                "Buttons",
                [
                    "primary_cta_label",
                    "primary_cta_url",
                    "secondary_cta_label",
                    "secondary_cta_url",
                ],
            ),
            (
                "Floating panel",
                [
                    "panel_label",
                    "panel_value",
                    "panel_value_suffix",
                    "panel_caption",
                    "panel_metric_1_value",
                    "panel_metric_1_label",
                    "panel_metric_2_value",
                    "panel_metric_2_label",
                ],
            ),
            ("Floating badge", ["badge_title", "badge_subtitle"]),
        ],
    },
    "about": {
        "label": "About section",
        "model": models.AboutSection,
        "form": forms.AboutSectionForm,
        "description": "Studio photo, heading and the floating “since” badge.",
        "groups": [
            ("Copy", ["eyebrow", "heading", "body"]),
            ("Image", ["image", "image_alt"]),
            ("Floating badge", ["badge_title", "badge_subtitle"]),
        ],
    },
    "services-section": {
        "label": "Services heading",
        "model": models.ServicesSection,
        "form": forms.ServicesSectionForm,
        "description": "Intro copy above the services grid.",
    },
    "portfolio-section": {
        "label": "Portfolio heading",
        "model": models.PortfolioSection,
        "form": forms.PortfolioSectionForm,
        "description": "Intro copy above the project grid and filters.",
    },
    "testimonials-section": {
        "label": "Testimonials heading",
        "model": models.TestimonialsSection,
        "form": forms.TestimonialsSectionForm,
        "description": "Intro copy and the speed of the scrolling row.",
    },
    "contact-section": {
        "label": "Contact & map",
        "model": models.ContactSection,
        "form": forms.ContactSectionForm,
        "description": "Contact copy, map labels and the form's button text.",
        "groups": [
            ("Copy", ["eyebrow", "heading", "subheading"]),
            (
                "Map",
                [
                    "show_map",
                    "map_address",
                    "map_zoom",
                    "map_label",
                    "map_embed_url",
                    "map_street_label",
                    "map_area_label",
                ],
            ),
            ("Form", ["submit_label", "success_message"]),
        ],
    },
    "footer": {
        "label": "Footer",
        "model": models.FooterSettings,
        "form": forms.FooterSettingsForm,
        "description": "Footer blurb, copyright line and back-to-top label.",
    },
    "email": {
        "label": "Email / SMTP",
        "model": models.EmailSettings,
        "form": forms.EmailSettingsForm,
        "description": (
            "Where contact-form enquiries are emailed, and the mail server "
            "used to send them. Save first, then send a test."
        ),
        "template": "dashboard/email_form.html",
        "groups": [
            ("Delivery", ["is_enabled", "notify_email", "from_email"]),
            (
                "Mail server",
                ["host", "port", "username", "password", "use_tls", "use_ssl", "timeout"],
            ),
            ("Message", ["subject_prefix", "reply_to_sender"]),
        ],
    },
}

# --------------------------------------------------------------------------- #
# Repeatable content
# --------------------------------------------------------------------------- #
COLLECTIONS = {
    "nav": {
        "label": "Navigation links",
        "singular": "navigation link",
        "model": models.NavLink,
        "form": forms.NavLinkForm,
        "columns": [("label", "Label"), ("target", "Target")],
    },
    "hero-highlights": {
        "label": "Hero highlights",
        "singular": "highlight",
        "model": models.HeroHighlight,
        "form": forms.HeroHighlightForm,
        "columns": [("label", "Label"), ("accent", "Accent")],
    },
    "stats": {
        "label": "Statistics",
        "singular": "statistic",
        "model": models.Stat,
        "form": forms.StatForm,
        "columns": [("label", "Label"), ("value", "Value"), ("suffix", "Suffix"), ("icon", "Icon")],
    },
    "about-cards": {
        "label": "About cards",
        "singular": "about card",
        "model": models.AboutCard,
        "form": forms.AboutCardForm,
        "columns": [("title", "Title"), ("accent", "Accent")],
    },
    "services": {
        "label": "Services",
        "singular": "service",
        "model": models.Service,
        "form": forms.ServiceForm,
        "columns": [("title", "Title"), ("icon", "Icon")],
    },
    "categories": {
        "label": "Project categories",
        "singular": "category",
        "model": models.ProjectCategory,
        "form": forms.ProjectCategoryForm,
        "columns": [("name", "Name"), ("slug", "Slug")],
    },
    "projects": {
        "label": "Projects",
        "singular": "project",
        "model": models.Project,
        "form": forms.ProjectForm,
        "columns": [("title", "Title"), ("category", "Category"), ("stack", "Stack")],
        "image_field": "image",
        "detail_view": "dashboard:project_edit",
    },
    "testimonials": {
        "label": "Testimonials",
        "singular": "testimonial",
        "model": models.Testimonial,
        "form": forms.TestimonialForm,
        "columns": [("author_name", "Name"), ("author_role", "Role")],
        "image_field": "avatar",
    },
    "contact-details": {
        "label": "Contact details",
        "singular": "contact detail",
        "model": models.ContactDetail,
        "form": forms.ContactDetailForm,
        "columns": [("label", "Label"), ("value", "Value")],
    },
    "footer-columns": {
        "label": "Footer columns",
        "singular": "footer column",
        "model": models.FooterColumn,
        "form": forms.FooterColumnForm,
        "columns": [("title", "Title")],
    },
    "footer-links": {
        "label": "Footer links",
        "singular": "footer link",
        "model": models.FooterLink,
        "form": forms.FooterLinkForm,
        "columns": [("label", "Label"), ("column", "Column"), ("url", "URL")],
        "select_related": ["column"],
    },
    "social": {
        "label": "Social links",
        "singular": "social link",
        "model": models.SocialLink,
        "form": forms.SocialLinkForm,
        "columns": [("label", "Label"), ("icon", "Icon"), ("url", "URL")],
    },
}

# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
NAVIGATION = [
    {
        "title": "Overview",
        "items": [
            {"kind": "url", "route": "dashboard:index", "label": "Dashboard"},
            {"kind": "url", "route": "dashboard:messages", "label": "Enquiries"},
        ],
    },
    {
        "title": "Global",
        "items": [
            {"kind": "singleton", "key": "site", "label": "Brand & SEO"},
            {"kind": "collection", "key": "nav", "label": "Navigation"},
            {"kind": "singleton", "key": "email", "label": "Email / SMTP"},
        ],
    },
    {
        "title": "Home page",
        "items": [
            {"kind": "singleton", "key": "hero", "label": "Hero"},
            {"kind": "collection", "key": "hero-highlights", "label": "Hero highlights"},
            {"kind": "collection", "key": "stats", "label": "Statistics"},
            {"kind": "singleton", "key": "about", "label": "About"},
            {"kind": "collection", "key": "about-cards", "label": "About cards"},
        ],
    },
    {
        "title": "Services",
        "items": [
            {"kind": "singleton", "key": "services-section", "label": "Section heading"},
            {"kind": "collection", "key": "services", "label": "Services"},
        ],
    },
    {
        "title": "Portfolio",
        "items": [
            {"kind": "singleton", "key": "portfolio-section", "label": "Section heading"},
            {"kind": "collection", "key": "categories", "label": "Categories"},
            {"kind": "collection", "key": "projects", "label": "Projects"},
        ],
    },
    {
        "title": "Testimonials",
        "items": [
            {"kind": "singleton", "key": "testimonials-section", "label": "Section heading"},
            {"kind": "collection", "key": "testimonials", "label": "Testimonials"},
        ],
    },
    {
        "title": "Contact",
        "items": [
            {"kind": "singleton", "key": "contact-section", "label": "Section & map"},
            {"kind": "collection", "key": "contact-details", "label": "Contact details"},
        ],
    },
    {
        "title": "Footer",
        "items": [
            {"kind": "singleton", "key": "footer", "label": "Footer settings"},
            {"kind": "collection", "key": "footer-columns", "label": "Columns"},
            {"kind": "collection", "key": "footer-links", "label": "Links"},
            {"kind": "collection", "key": "social", "label": "Social links"},
        ],
    },
]
