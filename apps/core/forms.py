from django import forms

from .models import ContactMessage, ProjectCategory, Service


class ContactForm(forms.ModelForm):
    """Public contact form. The honeypot silently drops naive spam bots."""

    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = ContactMessage
        fields = ("name", "email", "phone", "service", "category", "subject", "message")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only what is live on the site, and only ever chosen from that list —
        # a visitor cannot submit a service that is hidden or does not exist.
        service = self.fields["service"]
        service.queryset = Service.objects.filter(is_active=True)
        service.required = True
        service.empty_label = "Which service do you need?"
        service.error_messages["required"] = "Please choose a service."

        category = self.fields["category"]
        category.queryset = ProjectCategory.objects.filter(is_active=True)
        category.required = False
        category.empty_label = "What kind of business? (optional)"

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return ""

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_subject(self):
        return self.cleaned_data["subject"].strip()

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Please tell us a little more (10+ characters).")
        return message
