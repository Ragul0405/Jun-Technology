"""Forms for the super-admin dashboard.

`styled()` builds a ModelForm whose widgets already carry the dashboard's
classes, so every screen looks the same without hand-writing HTML per field.
"""

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.forms import inlineformset_factory

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
HeroSectionForm = styled(models.HeroSection)
AboutSectionForm = styled(models.AboutSection)
ServicesSectionForm = styled(models.ServicesSection)
PortfolioSectionForm = styled(models.PortfolioSection)
TestimonialsSectionForm = styled(models.TestimonialsSection)
ContactSectionForm = styled(models.ContactSection)
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
ProjectForm = styled(models.Project)
TestimonialForm = styled(models.Testimonial)
ContactDetailForm = styled(models.ContactDetail)
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
