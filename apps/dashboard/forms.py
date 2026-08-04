"""Forms for the super-admin dashboard.

`styled()` builds a ModelForm whose widgets already carry the dashboard's
classes, so every screen looks the same without hand-writing HTML per field.
"""

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.forms import inlineformset_factory, modelformset_factory

from apps.core import models

TEXT_INPUTS = (
    forms.TextInput,
    forms.EmailInput,
    forms.URLInput,
    forms.NumberInput,
    forms.PasswordInput,
)


class ImageFieldMixin:
    """Rejects oversized or non-image uploads before they reach disk."""

    def clean(self):
        cleaned = super().clean()
        max_size = getattr(settings, "MAX_UPLOAD_SIZE", 8 * 1024 * 1024)
        for name, field in self.fields.items():
            if not isinstance(field, forms.ImageField):
                continue
            upload = cleaned.get(name)
            if upload and hasattr(upload, "size") and upload.size > max_size:
                self.add_error(
                    name,
                    f"Image is too large — keep it under {max_size // (1024 * 1024)} MB.",
                )
        return cleaned


class BaseStyledForm(ImageFieldMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, TEXT_INPUTS):
                widget.attrs.setdefault("class", "fld")
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", "fld")
                widget.attrs.setdefault("rows", 4)
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "fld fld-select")
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "chk")
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs.setdefault("class", "fld-file")
                widget.attrs.setdefault("accept", "image/*")


def styled(model_cls, fields="__all__", widgets=None, labels=None, help_texts=None):
    """Return a dashboard-styled ModelForm for `model_cls`."""
    meta_attrs = {"model": model_cls, "fields": fields}
    if widgets:
        meta_attrs["widgets"] = widgets
    if labels:
        meta_attrs["labels"] = labels
    if help_texts:
        meta_attrs["help_texts"] = help_texts
    meta = type("Meta", (), meta_attrs)
    return type(f"{model_cls.__name__}Form", (BaseStyledForm,), {"Meta": meta})


COLOR = forms.TextInput(attrs={"type": "color", "class": "fld fld-color"})

# --------------------------------------------------------------------------- #
# Singleton section forms
# --------------------------------------------------------------------------- #
SiteSettingsForm = styled(
    models.SiteSettings,
    widgets={"accent_primary": COLOR, "accent_secondary": COLOR},
)
class HeroSectionForm(styled(models.HeroSection)):
    """
    The hero, including which projects its flip card cycles through.

    `is_featured` lives on Project, but choosing the line-up belongs here next
    to the panel it replaces — so the field is declared on this form and
    written back to the projects on save.
    """

    featured_projects = forms.ModelMultipleChoiceField(
        queryset=models.Project.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Projects in the flip card",
        help_text=(
            f"Tick up to {models.MAX_HERO_FEATURED}. The card flips through "
            "them in this order, every 4.2 seconds. Tick none and the "
            "build-health panel below is shown instead."
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["featured_projects"]
        field.queryset = models.Project.objects.order_by("order", "id")
        field.label_from_instance = lambda p: (
            f"{p.title} — {p.stack}" + ("" if p.is_active else "  (hidden)")
        )
        if not self.is_bound:
            field.initial = models.Project.objects.filter(is_featured=True)

    def clean_featured_projects(self):
        picked = self.cleaned_data.get("featured_projects")
        if picked and len(picked) > models.MAX_HERO_FEATURED:
            raise forms.ValidationError(
                f"The card holds {models.MAX_HERO_FEATURED} projects — "
                f"you picked {len(picked)}. Untick a few."
            )
        return picked

    def save(self, commit=True):
        hero = super().save(commit=commit)
        if commit:
            chosen = [p.pk for p in self.cleaned_data.get("featured_projects") or []]
            models.Project.objects.filter(is_featured=True).exclude(
                pk__in=chosen
            ).update(is_featured=False)
            models.Project.objects.filter(pk__in=chosen).update(is_featured=True)
        return hero
AboutSectionForm = styled(models.AboutSection)
ServicesSectionForm = styled(models.ServicesSection)
PortfolioSectionForm = styled(models.PortfolioSection)
TestimonialsSectionForm = styled(models.TestimonialsSection)
ContactSectionForm = styled(models.ContactSection)
BlogSectionForm = styled(models.BlogSection)
FaqSectionForm = styled(models.FaqSection)
FooterSettingsForm = styled(models.FooterSettings)


class EmailSettingsForm(BaseStyledForm):
    """SMTP settings. The password is write-only — it is never sent back out."""

    class Meta:
        model = models.EmailSettings
        fields = (
            "is_enabled",
            "host",
            "port",
            "username",
            "password",
            "use_tls",
            "use_ssl",
            "timeout",
            "from_email",
            "notify_email",
            "subject_prefix",
            "reply_to_sender",
        )
        widgets = {
            "password": forms.PasswordInput(
                render_value=False,
                attrs={"class": "fld", "autocomplete": "new-password"},
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].required = False
        if self.instance and self.instance.password:
            self.fields["password"].help_text = (
                "A password is saved. Leave blank to keep it, or type a new "
                "one to replace it."
            )

    def clean_password(self):
        # Blank means "keep what is already stored".
        return self.cleaned_data.get("password") or self.instance.password

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("is_enabled"):
            return cleaned

        if cleaned.get("use_tls") and cleaned.get("use_ssl"):
            self.add_error(
                "use_ssl", "Choose either TLS or SSL, not both. TLS on port 587 is usual."
            )
        for name, label in (("host", "SMTP server"), ("from_email", "Send from")):
            if not cleaned.get(name):
                self.add_error(name, f"{label} is required to send mail.")
        return cleaned

# --------------------------------------------------------------------------- #
# Repeatable content forms
# --------------------------------------------------------------------------- #
NavLinkForm = styled(models.NavLink)
HeroHighlightForm = styled(models.HeroHighlight)
StatForm = styled(models.Stat)
AboutCardForm = styled(models.AboutCard)
ServiceForm = styled(models.Service)
ProjectCategoryForm = styled(models.ProjectCategory)
BlogCategoryForm = styled(models.BlogCategory)
FaqItemForm = styled(models.FaqItem)
ContentPageForm = styled(
    models.ContentPage,
    widgets={"body": forms.Textarea(attrs={"class": "fld", "rows": 20})},
)
TestimonialForm = styled(models.Testimonial)
class BlogPostForm(styled(models.BlogPost)):
    """An article. The slug is optional — it is built from the title."""

    class Meta(styled(models.BlogPost).Meta):
        widgets = {
            "published_at": forms.DateInput(
                attrs={"type": "date", "class": "fld"}, format="%Y-%m-%d"
            ),
            "body": forms.Textarea(attrs={"class": "fld", "rows": 18}),
            "excerpt": forms.Textarea(attrs={"class": "fld", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["published_at"].input_formats = ["%Y-%m-%d"]
        self.fields["slug"].required = False


ContactDetailForm = styled(models.ContactDetail)


def _limit_error(limit, noun, existing):
    """A cap message that names what is already using the slots."""
    listing = ", ".join(str(item) for item in existing)
    return (
        f"Only {limit} {noun} are allowed. Remove one first — "
        f"currently using the slots: {listing}."
    )


class ProjectForm(styled(models.Project)):
    """
    A project.

    `is_featured` is deliberately absent: the hero's line-up is chosen on the
    Hero screen, so there is only ever one place to set it.
    """

    class Meta(styled(models.Project).Meta):
        exclude = ("is_featured",)


class AboutImageForm(styled(models.AboutImage)):
    """An about photo, with the flip-frame limit enforced at save time."""

    def clean(self):
        cleaned = super().clean()
        others = models.AboutImage.objects.all()
        if self.instance.pk:
            others = others.exclude(pk=self.instance.pk)
        if others.count() >= models.MAX_ABOUT_IMAGES:
            raise forms.ValidationError(
                _limit_error(models.MAX_ABOUT_IMAGES, "about images", others)
            )
        return cleaned


class AboutImageSlotForm(AboutImageForm):
    """
    One slot on the About images screen.

    Order is not asked for — the slots are numbered on the page and the view
    renumbers rows to match, so an editor never types an order value.
    """

    class Meta(AboutImageForm.Meta):
        fields = ("image", "alt", "is_active")
        # A plain file input: the slot already shows the photo and offers
        # "Remove this photo", so the stock widget's "Currently / Change /
        # Clear" line is just noise. Submitting nothing keeps the photo.
        widgets = {"image": forms.FileInput(attrs={"accept": "image/*"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["alt"].label = "Description"
        self.fields["is_active"].label = "Show this photo"
        self.fields["image"].required = not self.instance.pk

    def has_changed(self):
        """
        An empty slot is not an attempt to add a photo.

        Without this, saving the screen with any slot left blank fails with
        "image is required": a blank slot renders no `is_active` checkbox, so
        the unchecked default reads as a change.
        """
        if not self.instance.pk and not self.files.get(self.add_prefix("image")):
            return False
        return super().has_changed()

    def clean_is_active(self):
        """
        A photo you have just uploaded is visible.

        The "Show this photo" toggle only appears once a slot holds a photo, so
        a new upload posts no value — which would otherwise save it hidden and
        leave the editor wondering why the site did not change.
        """
        if not self.instance.pk:
            return True
        return self.cleaned_data.get("is_active", False)


def about_image_formset(*args, **kwargs):
    """Exactly MAX_ABOUT_IMAGES slots: the saved photos, then empty ones."""
    used = models.AboutImage.objects.count()
    formset_cls = modelformset_factory(
        models.AboutImage,
        form=AboutImageSlotForm,
        extra=max(0, models.MAX_ABOUT_IMAGES - used),
        max_num=models.MAX_ABOUT_IMAGES,
        validate_max=True,
        can_delete=True,
    )
    return formset_cls(*args, **kwargs)


FooterColumnForm = styled(models.FooterColumn)
FooterLinkForm = styled(models.FooterLink)
SocialLinkForm = styled(models.SocialLink)

# --------------------------------------------------------------------------- #
# Project inlines
# --------------------------------------------------------------------------- #
ProjectMetricFormSet = inlineformset_factory(
    models.Project,
    models.ProjectMetric,
    form=styled(models.ProjectMetric, fields=("value", "label", "order", "is_active")),
    fields=("value", "label", "order", "is_active"),
    extra=1,
    can_delete=True,
)

ProjectImageFormSet = inlineformset_factory(
    models.Project,
    models.ProjectImage,
    form=styled(models.ProjectImage, fields=("image", "caption", "order", "is_active")),
    fields=("image", "caption", "order", "is_active"),
    extra=1,
    can_delete=True,
)


class DashboardLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "fld", "autofocus": True, "placeholder": "Username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "fld", "placeholder": "Password"}
        )


class MessageStatusForm(forms.ModelForm):
    class Meta:
        model = models.ContactMessage
        fields = ("status",)
        widgets = {"status": forms.Select(attrs={"class": "fld fld-select"})}
