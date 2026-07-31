from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """Public contact form. The honeypot silently drops naive spam bots."""

    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = ContactMessage
        fields = ("name", "email", "phone", "subject", "message")

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
