import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.core import models
from apps.core.tests import an_image

from .forms import AboutImageForm, ProjectForm
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

    # -- hero flip card ---------------------------------------------------- #
    HERO_FIELDS = {
        "show_badge": "on",
        "badge_text": "Trusted by 150+ businesses worldwide",
        "title_line_1": "We Build Modern",
        "title_line_2": "Websites That Grow",
        "title_line_3": "Your Business",
        "subtitle": "Expert solutions.",
        "primary_cta_label": "Get Started",
        "primary_cta_url": "#contact",
        "secondary_cta_label": "View Our Work",
        "secondary_cta_url": "#work",
        "panel_label": "Build Health",
        "panel_value": "99.8",
        "panel_value_suffix": "%",
        "panel_caption": "Uptime",
        "panel_metric_1_value": "1.2s",
        "panel_metric_1_label": "Median LCP",
        "panel_metric_2_value": "A+",
        "panel_metric_2_label": "Core Web Vitals",
        "badge_title": "Award Winning",
        "badge_subtitle": "Digital Agency 2024",
    }

    def _hero_payload(self, projects):
        payload = dict(self.HERO_FIELDS)
        payload["featured_projects"] = [str(p.pk) for p in projects]
        return payload

    def test_hero_screen_picks_the_featured_projects(self):
        picks = list(models.Project.objects.all()[:2])
        response = self.client.post(
            reverse("dashboard:singleton", args=["hero"]), self._hero_payload(picks)
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            [p.title for p in models.Project.featured()], [p.title for p in picks]
        )

        # Unticking one drops it from the card without touching the project.
        self.client.post(
            reverse("dashboard:singleton", args=["hero"]),
            self._hero_payload(picks[:1]),
        )
        self.assertEqual([p.title for p in models.Project.featured()], [picks[0].title])
        self.assertTrue(models.Project.objects.get(pk=picks[1].pk).is_active)

    def test_hero_screen_shows_the_picker_with_every_project(self):
        response = self.client.get(reverse("dashboard:singleton", args=["hero"]))
        self.assertEqual(response.status_code, 200)
        field = response.context["form"]["featured_projects"]
        self.assertEqual(field.field.queryset.count(), models.Project.objects.count())
        self.assertIn("Featured projects", response.content.decode())

    def test_hero_screen_refuses_more_than_the_cap(self):
        too_many = list(models.Project.objects.all()[: models.MAX_HERO_FEATURED + 1])
        self.assertGreater(len(too_many), models.MAX_HERO_FEATURED)
        response = self.client.post(
            reverse("dashboard:singleton", args=["hero"]), self._hero_payload(too_many)
        )
        self.assertEqual(response.status_code, 200)  # redisplayed with the error
        self.assertIn(f"card holds {models.MAX_HERO_FEATURED}", response.content.decode())
        self.assertLessEqual(
            models.Project.objects.filter(is_featured=True).count(),
            models.MAX_HERO_FEATURED,
        )

    def test_editing_a_project_never_changes_the_hero_line_up(self):
        project = models.Project.objects.first()
        project.is_featured = True
        project.save(update_fields=["is_featured"])
        response = self.client.post(
            reverse("dashboard:project_edit", args=[project.pk]),
            {
                "title": project.title,
                "category": project.category_id,
                "stack": project.stack,
                "short_description": project.short_description,
                "description": project.description,
                "external_url": project.external_url,
                "order": project.order,
                "is_active": "on",
                "metrics-TOTAL_FORMS": "0",
                "metrics-INITIAL_FORMS": "0",
                "gallery-TOTAL_FORMS": "0",
                "gallery-INITIAL_FORMS": "0",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(models.Project.objects.get(pk=project.pk).is_featured)

    # -- about photo slots ------------------------------------------------- #
    ABOUT_FIELDS = {
        "eyebrow": "About Us",
        "heading": "Crafting digital excellence since 2019",
        "body": "Jun Technology is a premium web development agency.",
        "image_alt": "Our studio",
        "badge_title": "Since 2019",
        "badge_subtitle": "Silicon Valley, CA",
    }

    def _about_payload(self, filled=None, existing=()):
        payload = dict(self.ABOUT_FIELDS)
        payload.update(
            {
                "form-TOTAL_FORMS": str(models.MAX_ABOUT_IMAGES),
                "form-INITIAL_FORMS": str(len(existing)),
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": str(models.MAX_ABOUT_IMAGES),
            }
        )
        for index in range(models.MAX_ABOUT_IMAGES):
            payload["form-%d-alt" % index] = ""
            if index < len(existing):
                payload["form-%d-id" % index] = str(existing[index].pk)
                payload["form-%d-is_active" % index] = "on"
        for index, name in (filled or {}).items():
            payload["form-%d-alt" % index] = name
        return payload

    def test_about_screen_carries_the_photo_slots(self):
        response = self.client.get(reverse("dashboard:singleton", args=["about"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["photos"].total_form_count(), models.MAX_ABOUT_IMAGES
        )
        body = response.content.decode()
        self.assertIn("Photo 1", body)
        self.assertIn("Photo %d" % models.MAX_ABOUT_IMAGES, body)
        self.assertNotIn("Photo %d" % (models.MAX_ABOUT_IMAGES + 1), body)
        self.assertIn("Photo frame", body)

    def test_about_screen_saves_copy_and_photos_together(self):
        payload = self._about_payload({0: "Studio wide", 1: "The team"})
        payload["heading"] = "A brand new heading"
        payload["form-0-image"] = an_image("one.gif")
        payload["form-1-image"] = an_image("two.gif")

        response = self.client.post(
            reverse("dashboard:singleton", args=["about"]), payload
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.AboutSection.load().heading, "A brand new heading")

        photos = list(models.AboutImage.objects.order_by("order"))
        self.assertEqual([p.alt for p in photos], ["Studio wide", "The team"])
        self.assertEqual([p.order for p in photos], [0, 1])

        about = self.client.get(reverse("core:home")).content.decode()
        about = about[about.index('id="about"') : about.index('id="services"')]
        self.assertEqual(about.count("data-flip-face"), 2)

    def test_about_screen_removes_a_photo(self):
        for index in range(2):
            models.AboutImage.objects.create(
                image=an_image("s%d.gif" % index), alt="Photo %d" % index, order=index
            )
        existing = list(models.AboutImage.objects.order_by("order"))
        payload = self._about_payload({0: "Photo 0", 1: "Photo 1"}, existing)
        payload["form-1-DELETE"] = "on"

        self.assertEqual(
            self.client.post(
                reverse("dashboard:singleton", args=["about"]), payload
            ).status_code,
            302,
        )
        self.assertEqual(models.AboutImage.objects.count(), 1)
        self.assertEqual(models.AboutImage.objects.get().alt, "Photo 0")

    def test_about_photos_are_capped(self):
        for index in range(models.MAX_ABOUT_IMAGES):
            models.AboutImage.objects.create(
                image=an_image("studio-%d.gif" % index), alt="Studio %d" % index
            )
        response = self.client.get(reverse("dashboard:singleton", args=["about"]))
        self.assertEqual(len(response.context["photos"].extra_forms), 0)

        form = AboutImageForm(
            data={"alt": "One too many", "order": 9, "is_active": "on"},
            files={"image": an_image("one-too-many.gif")},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Only %d" % models.MAX_ABOUT_IMAGES, str(form.errors))

    def test_category_in_use_cannot_be_deleted(self):
        category = models.ProjectCategory.objects.filter(projects__isnull=False).first()
        self.client.post(reverse("dashboard:collection_delete", args=["categories", category.pk]))
        self.assertTrue(models.ProjectCategory.objects.filter(pk=category.pk).exists())
