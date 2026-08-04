"""
Content models for the Jun Technology marketing site.

Everything visible on the public page is stored here so the super admin can
edit copy, numbers, links and images without touching a template. The models
deliberately mirror the sections of the original static design one-to-one.
"""

from urllib.parse import quote

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from .icons import (
    CONTACT_ICON_CHOICES,
    SERVICE_ICON_CHOICES,
    SOCIAL_ICON_CHOICES,
    STAT_ICON_CHOICES,
)

# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #

#: The three accent treatments used by the original design. Keeping them as a
#: fixed palette means an editor can never break the visual language.
ACCENTS = {
    "blue": {
        "stroke": "var(--acc1,#8fb4ff)",
        "solid": "#3b82f6",
        "icon_bg": "rgba(59,130,246,.14)",
        "text_gradient": "var(--tx,#fff),var(--acc1,#8fb4ff)",
        "border_hover": "rgba(143,180,255,.32)",
        "shadow_hover": "0 30px 60px -34px rgba(59,130,246,.85)",
        "ring": "rgba(59,130,246,.5)",
        "social_bg": "rgba(59,130,246,.2)",
        "social_border": "rgba(59,130,246,.5)",
    },
    "purple": {
        "stroke": "var(--acc2,#c4b5fd)",
        "solid": "#7c5cff",
        "icon_bg": "rgba(124,92,255,.14)",
        "text_gradient": "var(--tx,#fff),var(--acc2,#c4b5fd)",
        "border_hover": "rgba(196,181,253,.32)",
        "shadow_hover": "0 30px 60px -34px rgba(124,92,255,.85)",
        "ring": "rgba(124,92,255,.5)",
        "social_bg": "rgba(124,92,255,.2)",
        "social_border": "rgba(124,92,255,.5)",
    },
    "sky": {
        "stroke": "#60a5fa",
        "solid": "#60a5fa",
        "icon_bg": "rgba(96,165,250,.14)",
        "text_gradient": "var(--tx,#fff),#60a5fa",
        "border_hover": "rgba(96,165,250,.32)",
        "shadow_hover": "0 30px 60px -34px rgba(37,99,235,.8)",
        "ring": "rgba(96,165,250,.5)",
        "social_bg": "rgba(96,165,250,.2)",
        "social_border": "rgba(96,165,250,.5)",
    },
}

ACCENT_CHOICES = [
    ("blue", "Blue"),
    ("purple", "Purple"),
    ("sky", "Sky"),
]


class AccentMixin(models.Model):
    """Adds an accent colour field plus the derived CSS values."""

    accent = models.CharField(
        max_length=10,
        choices=ACCENT_CHOICES,
        default="blue",
        help_text="Accent colour used for the icon, glow and hover state.",
    )

    class Meta:
        abstract = True

    @property
    def palette(self):
        return ACCENTS.get(self.accent, ACCENTS["blue"])

    @property
    def accent_stroke(self):
        return self.palette["stroke"]

    @property
    def accent_solid(self):
        return self.palette["solid"]

    @property
    def accent_icon_bg(self):
        return self.palette["icon_bg"]

    @property
    def accent_text_gradient(self):
        return self.palette["text_gradient"]

    @property
    def accent_border_hover(self):
        return self.palette["border_hover"]

    @property
    def accent_shadow_hover(self):
        return self.palette["shadow_hover"]

    @property
    def accent_ring(self):
        return self.palette["ring"]

    @property
    def accent_social_bg(self):
        return self.palette["social_bg"]

    @property
    def accent_social_border(self):
        return self.palette["social_border"]


class OrderedModel(models.Model):
    """Common ordering / visibility behaviour for every repeatable block."""

    order = models.PositiveIntegerField(
        default=0, help_text="Lower numbers appear first."
    )
    is_active = models.BooleanField(
        default=True, help_text="Uncheck to hide this item from the website."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ("order", "id")


class SingletonModel(models.Model):
    """A model with exactly one row — used for one-off page sections."""

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # pragma: no cover - guarded on purpose
        raise NotImplementedError("Singleton records cannot be deleted.")

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# --------------------------------------------------------------------------- #
# Global settings
# --------------------------------------------------------------------------- #
class SiteSettings(SingletonModel):
    THEME_CHOICES = [("dark", "Dark"), ("light", "Light")]

    brand_prefix = models.CharField(
        max_length=40, default="JUN", help_text="Highlighted part of the logo text."
    )
    brand_suffix = models.CharField(max_length=60, default="TECHNOLOGY")
    brand_tagline = models.CharField(max_length=80, default="Software Solutions")
    logo_mark = models.ImageField(
        upload_to="branding/",
        blank=True,
        help_text="Square logo mark shown in the navigation, loader and footer.",
    )
    favicon = models.ImageField(upload_to="branding/", blank=True)

    nav_cta_label = models.CharField(max_length=40, default="Get Quote")
    nav_cta_url = models.CharField(max_length=200, default="#contact")

    default_theme = models.CharField(
        max_length=10, choices=THEME_CHOICES, default="dark"
    )
    accent_primary = models.CharField(max_length=20, default="#3b82f6")
    accent_secondary = models.CharField(max_length=20, default="#7c5cff")
    show_loader = models.BooleanField(default=True)
    custom_cursor = models.BooleanField(default=True)
    show_particles = models.BooleanField(default=True)

    meta_title = models.CharField(
        max_length=120, default="Jun Technology — Software Solutions"
    )
    meta_description = models.TextField(
        default=(
            "Expert solutions in web development, UI/UX design, SEO and custom "
            "applications — engineered to scale with your business."
        )
    )
    meta_keywords = models.CharField(max_length=255, blank=True)
    og_image = models.ImageField(upload_to="branding/", blank=True)
    canonical_url = models.URLField(blank=True)
    google_analytics_id = models.CharField(max_length=40, blank=True)

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"


# --------------------------------------------------------------------------- #
# Navigation
# --------------------------------------------------------------------------- #
class NavLink(OrderedModel):
    label = models.CharField(max_length=40)
    target = models.CharField(
        max_length=80,
        help_text="Section id such as #services, or a full URL.",
    )
    section_key = models.CharField(
        max_length=40,
        blank=True,
        help_text=(
            "Section id without the # — used to highlight the link while "
            "scrolling. Leave blank for external links."
        ),
    )

    class Meta(OrderedModel.Meta):
        verbose_name = "Navigation link"

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        if not self.section_key and self.target.startswith("#"):
            self.section_key = self.target[1:]
        super().save(*args, **kwargs)


# --------------------------------------------------------------------------- #
# Hero
# --------------------------------------------------------------------------- #
class HeroSection(SingletonModel):
    badge_text = models.CharField(
        max_length=120, default="Trusted by 150+ businesses worldwide"
    )
    show_badge = models.BooleanField(default=True)

    title_line_1 = models.CharField(max_length=80, default="We Build Modern")
    title_line_2 = models.CharField(
        max_length=80,
        default="Websites That Grow",
        help_text="This line is rendered with the blue → purple gradient.",
    )
    title_line_3 = models.CharField(max_length=80, default="Your Business")

    subtitle = models.TextField(
        default=(
            "Expert solutions in web development, UI/UX design, SEO and custom "
            "applications — engineered to scale with your business."
        )
    )

    primary_cta_label = models.CharField(max_length=40, default="Get Started")
    primary_cta_url = models.CharField(max_length=200, default="#contact")
    secondary_cta_label = models.CharField(max_length=40, default="View Our Work")
    secondary_cta_url = models.CharField(max_length=200, default="#work")

    # Floating panel
    panel_label = models.CharField(max_length=40, default="Build Health")
    panel_value = models.CharField(max_length=20, default="99.8")
    panel_value_suffix = models.CharField(max_length=10, default="%")
    panel_caption = models.CharField(
        max_length=120, default="Average uptime across shipped platforms"
    )
    panel_metric_1_value = models.CharField(max_length=20, default="1.2s")
    panel_metric_1_label = models.CharField(max_length=40, default="Median LCP")
    panel_metric_2_value = models.CharField(max_length=20, default="A+")
    panel_metric_2_label = models.CharField(max_length=40, default="Core Web Vitals")

    # Floating badge
    badge_title = models.CharField(max_length=40, default="Award Winning")
    badge_subtitle = models.CharField(max_length=60, default="Digital Agency 2024")

    class Meta:
        verbose_name = "Hero section"
        verbose_name_plural = "Hero section"

    def __str__(self):
        return "Hero section"

    @property
    def title_lines(self):
        """Words with their staggered animation delay, exactly as designed."""
        lines, index = [], 0
        for raw, gradient in (
            (self.title_line_1, False),
            (self.title_line_2, True),
            (self.title_line_3, False),
        ):
            words = []
            for word in (raw or "").split():
                words.append({"text": word, "delay": round(0.25 + index * 0.07, 2)})
                index += 1
            if words:
                lines.append({"words": words, "gradient": gradient})
        return lines


class HeroHighlight(AccentMixin, OrderedModel):
    """The small dotted proof points under the hero buttons."""

    label = models.CharField(max_length=80)

    class Meta(OrderedModel.Meta):
        verbose_name = "Hero highlight"

    def __str__(self):
        return self.label


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
class Stat(AccentMixin, OrderedModel):
    icon = models.CharField(max_length=30, choices=STAT_ICON_CHOICES, default="bars")
    value = models.PositiveIntegerField(
        default=0, help_text="The number counts up from zero when scrolled into view."
    )
    suffix = models.CharField(max_length=10, blank=True, default="+")
    label = models.CharField(max_length=60)

    class Meta(OrderedModel.Meta):
        verbose_name = "Statistic"

    def __str__(self):
        return f"{self.value}{self.suffix} {self.label}"


# --------------------------------------------------------------------------- #
# About
# --------------------------------------------------------------------------- #
#: How many photos the about frame may flip through.
MAX_ABOUT_IMAGES = 5


class AboutSection(SingletonModel):
    eyebrow = models.CharField(
        max_length=60,
        blank=True,
        default="About Us",
        help_text="Small label above the heading. Leave blank to hide it.",
    )
    heading = models.CharField(
        max_length=160, default="Crafting digital excellence since 2019"
    )
    body = models.TextField(
        default=(
            "Jun Technology is a premium web development and digital solutions "
            "agency. We craft high-performance, visually striking websites and "
            "applications that help businesses stand out, scale up and win in "
            "the digital world."
        )
    )
    image = models.ImageField(
        upload_to="about/",
        blank=True,
        help_text="Team or studio photo shown in the tilting frame (4:3 works best).",
    )
    image_alt = models.CharField(max_length=160, blank=True, default="Our studio")
    badge_title = models.CharField(max_length=40, default="Since 2019")
    badge_subtitle = models.CharField(max_length=60, default="Silicon Valley, CA")

    class Meta:
        verbose_name = "About section"
        verbose_name_plural = "About section"

    def __str__(self):
        return "About section"


class AboutImage(OrderedModel):
    """
    Photos for the about frame's flip animation.

    When none exist the frame renders `AboutSection.image` exactly as it always
    has, so the section degrades to the original single-photo design.
    """

    image = models.ImageField(
        upload_to="about/",
        help_text="4:3 works best — the frame flips through these in order.",
    )
    alt = models.CharField(
        max_length=160,
        blank=True,
        help_text="Describes the photo for screen readers and search engines.",
    )

    class Meta(OrderedModel.Meta):
        verbose_name = "About image"

    def __str__(self):
        return self.alt or f"About image #{self.pk}"


class AboutCard(AccentMixin, OrderedModel):
    title = models.CharField(max_length=60)
    body = models.TextField()

    class Meta(OrderedModel.Meta):
        verbose_name = "About card"

    def __str__(self):
        return self.title


# --------------------------------------------------------------------------- #
# Services
# --------------------------------------------------------------------------- #
class ServicesSection(SingletonModel):
    eyebrow = models.CharField(
        max_length=60,
        blank=True,
        default="",
        help_text="Small label above the heading. Leave blank to hide it.",
    )
    heading = models.CharField(max_length=120, default="Our core services")
    subheading = models.TextField(
        default=(
            "From concept to launch, we deliver end-to-end digital solutions "
            "designed to grow your business."
        )
    )

    class Meta:
        verbose_name = "Services section"
        verbose_name_plural = "Services section"

    def __str__(self):
        return "Services section"


class Service(OrderedModel):
    icon = models.CharField(max_length=30, choices=SERVICE_ICON_CHOICES, default="code")
    title = models.CharField(max_length=80)
    slug = models.SlugField(
        max_length=90,
        unique=True,
        blank=True,
        help_text="Used by the enquiry link. Built from the title if left blank.",
    )
    show_in_footer = models.BooleanField(
        default=True,
        verbose_name="Feature in footer",
        help_text="List this service in the footer's services column.",
    )
    description = models.TextField()
    link_label = models.CharField(
        max_length=40,
        default="Learn more",
        blank=True,
        help_text="Leave blank to hide the “Learn more” line.",
    )
    link_url = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional — when set, clicking the card opens this link.",
    )

    class Meta(OrderedModel.Meta):
        verbose_name = "Service"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:80] or "service"
            slug, suffix = base, 2
            taken = Service.objects.exclude(pk=self.pk)
            while taken.filter(slug=slug).exists():
                slug = f"{base}-{suffix}"
                suffix += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def footer_badge(self):
        """Readable state for the dashboard's Services table."""
        return "Featured" if self.show_in_footer else "\u2014"

    @property
    def enquiry_url(self):
        """Home page, contact form open, this service already chosen."""
        from django.urls import reverse

        return f"{reverse('core:home')}?service={self.slug}#contact"


# --------------------------------------------------------------------------- #
# Portfolio
# --------------------------------------------------------------------------- #
class PortfolioSection(SingletonModel):
    eyebrow = models.CharField(
        max_length=60,
        blank=True,
        default="Our Portfolio",
        help_text="Small label above the heading. Leave blank to hide it.",
    )
    heading = models.CharField(max_length=120, default="Work we're proud of")
    subheading = models.TextField(
        default=(
            "A selection of projects that showcase our expertise, creativity "
            "and dedication to quality."
        )
    )
    all_filter_label = models.CharField(max_length=40, default="All")

    class Meta:
        verbose_name = "Portfolio section"
        verbose_name_plural = "Portfolio section"

    def __str__(self):
        return "Portfolio section"


class ProjectCategory(OrderedModel):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Project category"
        verbose_name_plural = "Project categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


#: How many projects the hero flip card may cycle through.
MAX_HERO_FEATURED = 5


class Project(OrderedModel):
    title = models.CharField(max_length=100)
    category = models.ForeignKey(
        ProjectCategory,
        on_delete=models.PROTECT,
        related_name="projects",
    )
    stack = models.CharField(
        max_length=120, help_text="Technology line, e.g. “React · Node.js”."
    )
    short_description = models.TextField(
        help_text="Shown on the card when hovering."
    )
    description = models.TextField(
        blank=True, help_text="Longer case-study copy shown in the pop-up."
    )
    image = models.ImageField(
        upload_to="projects/",
        blank=True,
        help_text="Card image — 16:10 works best.",
    )
    modal_image = models.ImageField(
        upload_to="projects/",
        blank=True,
        help_text="Case-study hero image — 16:8 works best. Falls back to the card image.",
    )
    external_url = models.URLField(blank=True, help_text="Optional live project link.")
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Feature in hero",
        help_text=(
            f"Show this project in the hero's flip card. At most "
            f"{MAX_HERO_FEATURED} projects can be featured at once."
        ),
    )

    class Meta(OrderedModel.Meta):
        verbose_name = "Project"

    def __str__(self):
        return self.title

    @property
    def hero_image(self):
        return self.modal_image or self.image

    @property
    def hero_metrics(self):
        """The two numbers the hero flip card has room for."""
        return list(self.metrics.filter(is_active=True)[:2])

    @property
    def hero_badge(self):
        """Readable state for the dashboard's Projects table."""
        return "Featured" if self.is_featured else "—"

    @classmethod
    def featured(cls):
        """The projects the hero flip card cycles through, capped at the limit."""
        return (
            cls.objects.filter(is_active=True, is_featured=True)
            .select_related("category")[:MAX_HERO_FEATURED]
        )


class ProjectMetric(OrderedModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="metrics"
    )
    value = models.CharField(max_length=20)
    label = models.CharField(max_length=40)

    class Meta(OrderedModel.Meta):
        verbose_name = "Project metric"

    def __str__(self):
        return f"{self.value} {self.label}"


class ProjectImage(OrderedModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="gallery"
    )
    image = models.ImageField(upload_to="projects/gallery/")
    caption = models.CharField(max_length=120, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Project gallery image"

    def __str__(self):
        return self.caption or f"Image #{self.pk}"


# --------------------------------------------------------------------------- #
# Blog
# --------------------------------------------------------------------------- #
class BlogSection(SingletonModel):
    """The copy at the top of the blog page."""

    eyebrow = models.CharField(
        max_length=60,
        blank=True,
        default="Our Blog",
        help_text="Small label above the heading. Leave blank to hide it.",
    )
    heading = models.CharField(max_length=120, default="Ideas, notes and releases")
    subheading = models.TextField(
        default=(
            "What we are building, what we are learning, and what we think is "
            "worth your time."
        )
    )
    empty_message = models.CharField(
        max_length=160,
        default="The first post is on its way — check back shortly.",
        help_text="Shown on the blog page while no posts are published.",
    )

    class Meta:
        verbose_name = "Blog page"
        verbose_name_plural = "Blog page"

    def __str__(self):
        return "Blog page"


class BlogCategory(OrderedModel):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Blog category"
        verbose_name_plural = "Blog categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def post_count(self):
        return self.posts.filter(is_active=True).count()


class BlogPost(models.Model):
    """
    One article.

    Ordered by publication date rather than a hand-set number: a marketing team
    publishing daily should never have to renumber anything.
    """

    title = models.CharField(max_length=160)
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        related_name="posts",
        null=True,
        blank=True,
        help_text=(
            "Optional — used by the filters on the blog page. Deleting a "
            "category leaves its posts uncategorised rather than removing them."
        ),
    )
    slug = models.SlugField(
        max_length=180,
        unique=True,
        blank=True,
        help_text="Its web address. Left blank, it is built from the title.",
    )
    author = models.CharField(max_length=80, blank=True, default="Jun Technology")
    published_at = models.DateField(
        default=timezone.localdate,
        help_text="The date shown on the post, and what the list is ordered by.",
    )
    cover = models.ImageField(
        upload_to="blog/",
        blank=True,
        help_text="Header image — 16:9 works best.",
    )
    excerpt = models.TextField(
        max_length=300,
        help_text="One or two sentences, shown on the blog list and in search results.",
    )
    body = models.TextField(
        help_text="The article. Leave a blank line between paragraphs.",
    )
    is_active = models.BooleanField(
        default=True, help_text="Uncheck to keep this a draft."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-published_at", "-id")
        verbose_name = "Blog post"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:170] or "post"
            slug, suffix = base, 2
            taken = BlogPost.objects.exclude(pk=self.pk)
            while taken.filter(slug=slug).exists():
                slug = f"{base}-{suffix}"
                suffix += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("core:blog_post", args=[self.slug])

    @property
    def paragraphs(self):
        """The body split into paragraphs, so templates never render raw HTML."""
        return [p.strip() for p in (self.body or "").split("\n\n") if p.strip()]

    @property
    def reading_minutes(self):
        words = len((self.body or "").split())
        return max(1, round(words / 200))


# --------------------------------------------------------------------------- #
# Testimonials
# --------------------------------------------------------------------------- #
class TestimonialsSection(SingletonModel):
    eyebrow = models.CharField(
        max_length=60,
        blank=True,
        default="Client Love",
        help_text="Small label above the heading. Leave blank to hide it.",
    )
    heading = models.CharField(max_length=120, default="What our clients say")
    subheading = models.TextField(
        default=(
            "Real feedback from businesses that trusted us to build their "
            "digital presence."
        )
    )
    scroll_seconds = models.PositiveIntegerField(
        default=42,
        validators=[MinValueValidator(10), MaxValueValidator(200)],
        help_text="Seconds for one full pass of the scrolling row.",
    )

    class Meta:
        verbose_name = "Testimonials section"
        verbose_name_plural = "Testimonials section"

    def __str__(self):
        return "Testimonials section"


class Testimonial(AccentMixin, OrderedModel):
    quote = models.TextField()
    author_name = models.CharField(max_length=80)
    author_role = models.CharField(max_length=120)
    avatar = models.ImageField(
        upload_to="testimonials/",
        blank=True,
        help_text="Square photo — shown as a circle.",
    )

    class Meta(OrderedModel.Meta):
        verbose_name = "Testimonial"

    def __str__(self):
        return f"{self.author_name} — {self.author_role}"

    @property
    def initials(self):
        parts = [p for p in self.author_name.split() if p]
        return "".join(p[0] for p in parts[:2]).upper()


# --------------------------------------------------------------------------- #
# Contact
# --------------------------------------------------------------------------- #
class ContactSection(SingletonModel):
    eyebrow = models.CharField(
        max_length=60,
        blank=True,
        default="Get In Touch",
        help_text="Small label above the heading. Leave blank to hide it.",
    )
    heading = models.CharField(
        max_length=120, default="Let's build something amazing"
    )
    subheading = models.TextField(
        default=(
            "Ready to start your project? Send us a message and we'll get back "
            "to you within 24 hours."
        )
    )
    show_map = models.BooleanField(default=True)
    map_label = models.CharField(
        max_length=120, default="Jun Technology HQ · Menlo Park"
    )
    map_street_label = models.CharField(max_length=40, default="SILICON AVE")
    map_area_label = models.CharField(max_length=40, default="TECH PARK")
    map_address = models.CharField(
        max_length=250,
        blank=True,
        help_text=(
            "Easiest option — type your address or place name exactly as it "
            "appears on Google Maps (e.g. “Jun Technology, MG Road, Kochi”). "
            "A real map is shown at that location. No API key needed."
        ),
    )
    map_zoom = models.PositiveSmallIntegerField(
        default=15,
        validators=[MinValueValidator(1), MaxValueValidator(21)],
        help_text="1 = whole world, 15 = neighbourhood, 21 = building.",
    )
    map_embed_url = models.URLField(
        blank=True,
        max_length=500,
        help_text=(
            "Advanced — paste the src=\"…\" URL from Google Maps → Share → "
            "Embed a map. Overrides the address above."
        ),
    )
    submit_label = models.CharField(max_length=40, default="Send Message")
    success_message = models.CharField(max_length=80, default="Message sent")

    class Meta:
        verbose_name = "Contact section"
        verbose_name_plural = "Contact section"

    def __str__(self):
        return "Contact section"

    @property
    def map_iframe_url(self):
        """The embed URL to load, or empty to keep the illustrated map."""
        if self.map_embed_url:
            return self.map_embed_url
        if self.map_address:
            return (
                "https://maps.google.com/maps"
                f"?q={quote(self.map_address)}&z={self.map_zoom}"
                "&hl=en&output=embed"
            )
        return ""


class ContactDetail(AccentMixin, OrderedModel):
    icon = models.CharField(max_length=30, choices=CONTACT_ICON_CHOICES, default="pin")
    label = models.CharField(max_length=60, help_text="Small uppercase caption.")
    value = models.CharField(max_length=200)
    link = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional link, e.g. mailto:hello@example.com or tel:+15551234567.",
    )

    class Meta(OrderedModel.Meta):
        verbose_name = "Contact detail"

    def __str__(self):
        return f"{self.label}: {self.value}"


class EmailSettings(SingletonModel):
    """
    Outgoing mail configuration, editable by the super admin.

    When `is_enabled` is off the project falls back to the DJANGO_EMAIL_*
    environment variables, so a server can still be configured outside the
    dashboard.
    """

    is_enabled = models.BooleanField(
        default=False,
        verbose_name="Use these settings",
        help_text=(
            "Turn on to send mail with the details below. Leave off to use "
            "the server's environment variables instead."
        ),
    )
    host = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="SMTP server",
        help_text="e.g. smtp.gmail.com, smtp.zoho.in, smtp.hostinger.com",
    )
    port = models.PositiveIntegerField(
        default=587,
        help_text="587 for TLS (usual), 465 for SSL, 25 unencrypted.",
    )
    username = models.CharField(
        max_length=200, blank=True, help_text="Usually the full email address."
    )
    password = models.CharField(
        max_length=255,
        blank=True,
        help_text=(
            "Stored in the database. Use a provider app password, never your "
            "main account password."
        ),
    )
    use_tls = models.BooleanField(default=True, verbose_name="Use TLS (port 587)")
    use_ssl = models.BooleanField(default=False, verbose_name="Use SSL (port 465)")
    timeout = models.PositiveSmallIntegerField(
        default=20, help_text="Seconds to wait for the mail server."
    )

    from_email = models.EmailField(
        blank=True,
        verbose_name="Send from",
        help_text="Address enquiries appear to come from. Many providers "
        "require this to match the username.",
    )
    notify_email = models.EmailField(
        blank=True,
        verbose_name="Send enquiries to",
        help_text="Where new contact-form enquiries are emailed. Leave blank "
        "to only keep them in the dashboard.",
    )
    subject_prefix = models.CharField(
        max_length=60,
        default="New enquiry:",
        blank=True,
        help_text=(
            "Put in front of the enquiry subject line — a space is added "
            "automatically."
        ),
    )
    reply_to_sender = models.BooleanField(
        default=True,
        help_text="Set Reply-To to the visitor's address so you can reply directly.",
    )

    last_test_at = models.DateTimeField(null=True, blank=True, editable=False)
    last_test_ok = models.BooleanField(default=False, editable=False)
    last_test_error = models.TextField(blank=True, editable=False)

    class Meta:
        verbose_name = "Email / SMTP settings"
        verbose_name_plural = "Email / SMTP settings"

    def __str__(self):
        return "Email settings"

    @property
    def is_configured(self):
        return bool(self.is_enabled and self.host and self.from_email)


class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("read", "Read"),
        ("replied", "Replied"),
        ("archived", "Archived"),
    ]

    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    # The service and category are kept twice: as a link, so the dashboard can
    # filter on them, and as plain text, so an enquiry still records what was
    # asked for after that service or category is renamed or deleted.
    service = models.ForeignKey(
        "Service",
        on_delete=models.SET_NULL,
        related_name="enquiries",
        null=True,
        blank=True,
    )
    service_name = models.CharField(max_length=80, blank=True)
    category = models.ForeignKey(
        "ProjectCategory",
        on_delete=models.SET_NULL,
        related_name="enquiries",
        null=True,
        blank=True,
        verbose_name="Industry",
    )
    category_name = models.CharField(max_length=60, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="new")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Contact message"

    def __str__(self):
        return f"{self.name} — {self.subject}"

    def save(self, *args, **kwargs):
        # Snapshot the names so the record outlives the rows it points at.
        if self.service_id and not self.service_name:
            self.service_name = self.service.title
        if self.category_id and not self.category_name:
            self.category_name = self.category.name
        super().save(*args, **kwargs)

    @property
    def service_label(self):
        return self.service_name or (self.service.title if self.service else "—")

    @property
    def category_label(self):
        return self.category_name or (self.category.name if self.category else "—")


# --------------------------------------------------------------------------- #
# Standalone pages
# --------------------------------------------------------------------------- #
class ContentPage(models.Model):
    """
    A plain prose page — terms, privacy policy, anything similar.

    Served at its own fixed URL rather than a catch-all, so the routes stay
    explicit and a typo cannot silently create a live page.
    """

    slug = models.SlugField(
        max_length=60,
        unique=True,
        help_text="Fixed by the page's URL — “terms” and “privacy”.",
    )
    title = models.CharField(max_length=120)
    intro = models.TextField(
        blank=True, help_text="One or two sentences under the heading. Optional."
    )
    body = models.TextField(
        help_text="Leave a blank line between paragraphs. A line ending in a "
        "colon is shown as a sub-heading."
    )
    is_active = models.BooleanField(
        default=True, help_text="Uncheck to take the page offline (it returns 404)."
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("slug",)
        verbose_name = "Page"

    def __str__(self):
        return self.title

    @property
    def blocks(self):
        """Paragraphs, with `Heading:` lines marked so the template can style them."""
        out = []
        for chunk in (self.body or "").split("\n\n"):
            text = chunk.strip()
            if not text:
                continue
            out.append(
                {"text": text, "is_heading": text.endswith(":") and len(text) < 90}
            )
        return out


class FaqSection(SingletonModel):
    eyebrow = models.CharField(max_length=60, blank=True, default="FAQs")
    heading = models.CharField(max_length=120, default="Questions we get asked")
    subheading = models.TextField(
        default="If yours is not here, the contact form is at the bottom of the page."
    )

    class Meta:
        verbose_name = "FAQ page"
        verbose_name_plural = "FAQ page"

    def __str__(self):
        return "FAQ page"


class FaqItem(OrderedModel):
    question = models.CharField(max_length=200)
    answer = models.TextField()

    class Meta(OrderedModel.Meta):
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


# --------------------------------------------------------------------------- #
# Footer
# --------------------------------------------------------------------------- #
class FooterSettings(SingletonModel):
    description = models.TextField(
        default=(
            "Building modern digital experiences that help businesses grow. "
            "Your success is our mission."
        )
    )
    copyright_text = models.CharField(
        max_length=200,
        default="© 2026 Jun Technology Software Solutions. All rights reserved.",
    )
    back_to_top_label = models.CharField(max_length=40, default="↑ Back to top")

    class Meta:
        verbose_name = "Footer settings"
        verbose_name_plural = "Footer settings"

    def __str__(self):
        return "Footer settings"


class FooterColumn(OrderedModel):
    SOURCE_CHOICES = [
        ("links", "The links below"),
        ("services", "Featured services"),
    ]

    title = models.CharField(max_length=60)
    source = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        default="links",
        help_text=(
            "“Featured services” fills this column automatically with the "
            "services ticked “Feature in footer”, each opening the enquiry "
            "form for that service."
        ),
    )

    class Meta(OrderedModel.Meta):
        verbose_name = "Footer column"

    def __str__(self):
        return self.title


class FooterLink(OrderedModel):
    column = models.ForeignKey(
        FooterColumn, on_delete=models.CASCADE, related_name="links"
    )
    label = models.CharField(max_length=60)
    url = models.CharField(max_length=200, default="#")

    class Meta(OrderedModel.Meta):
        verbose_name = "Footer link"

    def __str__(self):
        return self.label


class SocialLink(AccentMixin, OrderedModel):
    icon = models.CharField(
        max_length=30, choices=SOCIAL_ICON_CHOICES, default="linkedin"
    )
    label = models.CharField(max_length=40, help_text="Accessible name, e.g. LinkedIn.")
    url = models.CharField(max_length=200, default="#contact")

    class Meta(OrderedModel.Meta):
        verbose_name = "Social link"

    def __str__(self):
        return self.label
