import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.core import models

from .registry import COLLECTIONS, SINGLETONS

TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix="juntech-dashboard-media-")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DashboardTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        call_command("seed_content")
        cls.admin = get_user_model().objects.create_superuser(
            "admin", "admin@example.com", "TestPass123!"
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("dashboard:login"), response["Location"])

    def test_non_staff_cannot_enter(self):
        get_user_model().objects.create_user("bob", password="TestPass123!")
        self.client.logout()
        self.client.login(username="bob", password="TestPass123!")
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 302)

    def test_overview_renders(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)

    def test_every_singleton_page_renders(self):
        for key in SINGLETONS:
            with self.subTest(key=key):
                response = self.client.get(reverse("dashboard:singleton", args=[key]))
                self.assertEqual(response.status_code, 200)

    def test_every_collection_page_renders(self):
        for key in COLLECTIONS:
            with self.subTest(key=key):
                self.assertEqual(
                    self.client.get(reverse("dashboard:collection_list", args=[key])).status_code,
                    200,
                )
                self.assertEqual(
                    self.client.get(reverse("dashboard:collection_create", args=[key])).status_code,
                    200,
                )

    def test_edit_pages_render(self):
        project = models.Project.objects.first()
        self.assertEqual(
            self.client.get(reverse("dashboard:project_edit", args=[project.pk])).status_code, 200
        )
        testimonial = models.Testimonial.objects.first()
        self.assertEqual(
            self.client.get(
                reverse("dashboard:collection_edit", args=["testimonials", testimonial.pk])
            ).status_code,
            200,
        )

    def test_editing_a_singleton_changes_the_website(self):
        response = self.client.post(
            reverse("dashboard:singleton", args=["hero"]),
            {
                "show_badge": "on",
                "badge_text": "Trusted worldwide",
                "title_line_1": "We Ship Fast",
                "title_line_2": "Software That Scales",
                "title_line_3": "For Everyone",
                "subtitle": "New subtitle copy.",
                "primary_cta_label": "Start now",
                "primary_cta_url": "#contact",
                "secondary_cta_label": "See work",
                "secondary_cta_url": "#work",
                "panel_label": "Build Health",
                "panel_value": "99.9",
                "panel_value_suffix": "%",
                "panel_caption": "Uptime",
                "panel_metric_1_value": "1.0s",
                "panel_metric_1_label": "LCP",
                "panel_metric_2_value": "A+",
                "panel_metric_2_label": "Vitals",
                "badge_title": "Award Winning",
                "badge_subtitle": "Agency 2026",
            },
        )
        self.assertEqual(response.status_code, 302)
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertIn("Ship", body)
        self.assertIn("New subtitle copy.", body)

    def test_creating_and_deleting_a_service(self):
        response = self.client.post(
            reverse("dashboard:collection_create", args=["services"]),
            {
                "icon": "cloud",
                "title": "Cloud Migration",
                "description": "We move workloads to the cloud safely.",
                "link_label": "Learn more",
                "link_url": "",
                "order": 9,
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        service = models.Service.objects.get(title="Cloud Migration")
        self.assertIn("Cloud Migration", self.client.get(reverse("core:home")).content.decode())

        self.client.post(reverse("dashboard:collection_delete", args=["services", service.pk]))
        self.assertFalse(models.Service.objects.filter(pk=service.pk).exists())

    def test_toggling_visibility(self):
        stat = models.Stat.objects.first()
        self.client.post(reverse("dashboard:collection_toggle", args=["stats", stat.pk]))
        stat.refresh_from_db()
        self.assertFalse(stat.is_active)

    def test_message_workflow(self):
        message = models.ContactMessage.objects.create(
            name="Ada", email="ada@example.com", subject="Hi", message="Hello there team."
        )
        self.client.get(reverse("dashboard:message_detail", args=[message.pk]))
        message.refresh_from_db()
        self.assertEqual(message.status, "read")

        self.client.post(reverse("dashboard:message_detail", args=[message.pk]), {"status": "replied"})
        message.refresh_from_db()
        self.assertEqual(message.status, "replied")

        self.client.post(reverse("dashboard:message_delete", args=[message.pk]))
        self.assertFalse(models.ContactMessage.objects.filter(pk=message.pk).exists())

    def test_email_settings_page_and_password_handling(self):
        url = reverse("dashboard:singleton", args=["email"])
        self.assertEqual(self.client.get(url).status_code, 200)

        payload = {
            "is_enabled": "on",
            "host": "smtp.example.com",
            "port": "587",
            "username": "hello@juntechnology.com",
            "password": "app-password-123",
            "use_tls": "on",
            "timeout": "20",
            "from_email": "hello@juntechnology.com",
            "notify_email": "hello@juntechnology.com",
            "subject_prefix": "New enquiry:",
            "reply_to_sender": "on",
        }
        self.assertEqual(self.client.post(url, payload).status_code, 302)
        config = models.EmailSettings.load()
        self.assertEqual(config.password, "app-password-123")
        self.assertTrue(config.is_configured)

        # The saved password is never rendered back into the page.
        self.assertNotIn("app-password-123", self.client.get(url).content.decode())

        # Saving with a blank password keeps the stored one.
        payload["password"] = ""
        payload["subject_prefix"] = "Enquiry —"
        self.client.post(url, payload)
        config = models.EmailSettings.load()
        self.assertEqual(config.password, "app-password-123")
        self.assertEqual(config.subject_prefix, "Enquiry —")

    def test_email_settings_reject_tls_and_ssl_together(self):
        response = self.client.post(
            reverse("dashboard:singleton", args=["email"]),
            {
                "is_enabled": "on",
                "host": "smtp.example.com",
                "port": "465",
                "use_tls": "on",
                "use_ssl": "on",
                "timeout": "20",
                "from_email": "hello@juntechnology.com",
                "subject_prefix": "New enquiry: ",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(models.EmailSettings.load().is_enabled)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_test_email_action(self):
        from django.core import mail

        response = self.client.post(
            reverse("dashboard:send_test_email"), {"recipient": "jana@example.com"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["jana@example.com"])
        config = models.EmailSettings.load()
        self.assertTrue(config.last_test_ok)
        self.assertIsNotNone(config.last_test_at)

    def test_map_address_saves_from_the_dashboard(self):
        url = reverse("dashboard:singleton", args=["contact-section"])
        response = self.client.post(
            url,
            {
                "eyebrow": "Get In Touch",
                "heading": "Let's build something amazing",
                "subheading": "Ready to start your project?",
                "show_map": "on",
                "map_address": "Jun Technology, Kochi, Kerala",
                "map_zoom": "16",
                "map_label": "Jun Technology HQ",
                "map_street_label": "SILICON AVE",
                "map_area_label": "TECH PARK",
                "map_embed_url": "",
                "submit_label": "Send Message",
                "success_message": "Message sent",
            },
        )
        self.assertEqual(response.status_code, 302)
        contact = models.ContactSection.load()
        self.assertIn("maps.google.com", contact.map_iframe_url)
        self.assertIn("<iframe", self.client.get("/").content.decode())

    def test_category_in_use_cannot_be_deleted(self):
        category = models.ProjectCategory.objects.filter(projects__isnull=False).first()
        self.client.post(reverse("dashboard:collection_delete", args=["categories", category.pk]))
        self.assertTrue(models.ProjectCategory.objects.filter(pk=category.pk).exists())
