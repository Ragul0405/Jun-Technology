from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from . import models
from .mail import (
    build_connection,
    build_subject,
    recipient_address,
    send_enquiry_notification,
)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EnquiryMailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # The form now requires a service; this class does not seed content.
        cls.service = models.Service.objects.create(
            icon="code", title="Website Development", description="Sites."
        )

    def _enquiry(self, **kwargs):
        defaults = {
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "phone": "+91 98765 43210",
            "subject": "New website",
            "message": "We would like a quote for a marketing site.",
        }
        defaults.update(kwargs)
        return models.ContactMessage.objects.create(**defaults)

    def test_no_email_when_no_recipient(self):
        self.assertFalse(send_enquiry_notification(self._enquiry()))
        self.assertEqual(len(mail.outbox), 0)

    def test_dashboard_recipient_is_used(self):
        config = models.EmailSettings.load()
        config.notify_email = "hello@juntechnology.com"
        config.save()

        self.assertTrue(send_enquiry_notification(self._enquiry()))
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.to, ["hello@juntechnology.com"])
        self.assertEqual(sent.reply_to, ["ada@example.com"])
        self.assertIn("New enquiry: New website", sent.subject)
        self.assertIn("Ada Lovelace", sent.body)

    @override_settings(CONTACT_NOTIFY_EMAIL="env@example.com")
    def test_dashboard_value_overrides_the_environment(self):
        self.assertEqual(recipient_address(), "env@example.com")
        config = models.EmailSettings.load()
        config.notify_email = "dashboard@example.com"
        config.save()
        self.assertEqual(recipient_address(), "dashboard@example.com")

    def test_reply_to_can_be_turned_off(self):
        config = models.EmailSettings.load()
        config.notify_email = "hello@juntechnology.com"
        config.reply_to_sender = False
        config.save()
        send_enquiry_notification(self._enquiry())
        self.assertFalse(mail.outbox[0].reply_to)

    def test_submitting_the_form_sends_the_notification(self):
        config = models.EmailSettings.load()
        config.notify_email = "hello@juntechnology.com"
        config.save()

        response = self.client.post(
            reverse("core:contact_submit"),
            {
                "name": "Grace Hopper",
                "email": "grace@example.com",
                "service": self.service.pk,
                "subject": "Ecommerce build",
                "message": "Please send a proposal for an online store.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Grace Hopper", mail.outbox[0].body)

    def test_a_broken_mail_server_never_breaks_the_form(self):
        config = models.EmailSettings.load()
        config.is_enabled = True
        config.host = "smtp.invalid.example"
        config.port = 587
        config.from_email = "no-reply@juntechnology.com"
        config.notify_email = "hello@juntechnology.com"
        config.timeout = 1
        config.save()

        response = self.client.post(
            reverse("core:contact_submit"),
            {
                "name": "Alan Turing",
                "email": "alan@example.com",
                "service": self.service.pk,
                "subject": "Portal",
                "message": "We need a secure internal portal built.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        # The enquiry is still captured for the dashboard.
        self.assertTrue(models.ContactMessage.objects.filter(name="Alan Turing").exists())

    def test_subject_prefix_always_gets_one_space(self):
        # Form fields strip whitespace, so the prefix cannot carry its own space.
        self.assertEqual(build_subject("New enquiry:", "Website"), "New enquiry: Website")
        self.assertEqual(build_subject("New enquiry: ", "Website"), "New enquiry: Website")
        self.assertEqual(build_subject("", "Website"), "Website")
        self.assertEqual(build_subject(None, "Website"), "Website")

    def test_connection_uses_dashboard_settings_when_enabled(self):
        config = models.EmailSettings.load()
        config.is_enabled = True
        config.host = "smtp.example.com"
        config.port = 2525
        config.username = "postmaster@example.com"
        config.password = "secret"
        config.use_tls = True
        config.from_email = "no-reply@example.com"
        config.save()

        connection = build_connection()
        self.assertEqual(connection.host, "smtp.example.com")
        self.assertEqual(connection.port, 2525)
        self.assertEqual(connection.username, "postmaster@example.com")
        self.assertTrue(connection.use_tls)
