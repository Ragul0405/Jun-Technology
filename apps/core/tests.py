import shutil
import tempfile

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from . import models

#: Keep seeded/uploaded files out of the real media folder during tests.
TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix="juntech-test-media-")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PublicSiteTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        call_command("seed_content")

    def test_home_renders_every_section(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        for marker in (
            'id="home"',
            'id="stats"',
            'id="about"',
            'id="services"',
            'id="work"',
            'id="voices"',
            'id="contact"',
            "data-particles",
            "data-marquee",
            "jt-projects",
        ):
            self.assertIn(marker, body)

    def test_home_shows_seeded_content(self):
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertIn("Website Development", body)
        self.assertIn("CoreLogic CRM", body)
        self.assertIn("Sarah Mitchell", body)
        self.assertIn("Projects Delivered", body)

    def test_contact_form_stores_message(self):
        response = self.client.post(
            reverse("core:contact_submit"),
            {
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "phone": "+1 555 0100",
                "subject": "New website",
                "message": "We would like a quote for a new marketing site.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        message = models.ContactMessage.objects.get()
        self.assertEqual(message.name, "Ada Lovelace")
        self.assertEqual(message.status, "new")

    def test_contact_form_rejects_invalid_input(self):
        response = self.client.post(
            reverse("core:contact_submit"),
            {"name": "", "email": "not-an-email", "subject": "", "message": "hi"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])
        self.assertEqual(models.ContactMessage.objects.count(), 0)

    def test_honeypot_blocks_bots(self):
        response = self.client.post(
            reverse("core:contact_submit"),
            {
                "name": "Bot",
                "email": "bot@example.com",
                "subject": "Cheap links",
                "message": "Buy our backlinks today please.",
                "website": "http://spam.example",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(models.ContactMessage.objects.count(), 0)

    def test_seed_is_idempotent(self):
        before = models.Service.objects.count()
        call_command("seed_content")
        self.assertEqual(models.Service.objects.count(), before)

    def test_seed_installs_the_logo(self):
        site = models.SiteSettings.load()
        self.assertTrue(site.logo_mark, "seed_content should install the logo mark")
        first_name = site.logo_mark.name

        call_command("seed_content")
        models.SiteSettings.load().refresh_from_db()
        self.assertEqual(models.SiteSettings.load().logo_mark.name, first_name)

        self.assertIn(site.logo_mark.url, self.client.get(reverse("core:home")).content.decode())

    def test_hidden_items_are_not_rendered(self):
        service = models.Service.objects.create(
            icon="cloud", title="Kubernetes Wrangling", description="Cluster care."
        )
        self.assertIn(
            service.title, self.client.get(reverse("core:home")).content.decode()
        )
        service.is_active = False
        service.save(update_fields=["is_active"])
        self.assertNotIn(
            service.title, self.client.get(reverse("core:home")).content.decode()
        )

    def test_robots_txt_protects_the_admin_areas(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        body = response.content.decode()
        self.assertIn("Disallow: /dashboard/", body)
        self.assertIn("Disallow: /django-admin/", body)
        self.assertIn("Sitemap: http://testserver/sitemap.xml", body)

    def test_sitemap_lists_the_home_page(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<loc>https://testserver/</loc>", response.content.decode())

    def test_service_cards_keep_their_learn_more_line(self):
        # The arrow line is part of the original design — seeding must set it.
        self.assertTrue(
            all(s.link_label for s in models.Service.objects.all()),
            "every seeded service needs a link label",
        )
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertIn("data-arrow", body)
        self.assertIn("Learn more", body)

    def test_services_eyebrow_is_hidden_by_default(self):
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertNotIn("What We Offer", body)
        self.assertIn("Our core services", body)

    def test_eyebrow_reappears_when_set(self):
        section = models.ServicesSection.load()
        section.eyebrow = "What We Do"
        section.save()
        self.assertIn(
            "What We Do", self.client.get(reverse("core:home")).content.decode()
        )

    def test_map_address_builds_an_embed(self):
        contact = models.ContactSection.load()
        self.assertEqual(contact.map_iframe_url, "")  # illustrated map by default

        contact.map_address = "Jun Technology, MG Road, Kochi"
        contact.map_zoom = 17
        contact.save()
        url = models.ContactSection.load().map_iframe_url
        self.assertIn("maps.google.com", url)
        self.assertIn("Jun%20Technology%2C%20MG%20Road%2C%20Kochi", url)
        self.assertIn("z=17", url)
        self.assertIn("output=embed", url)
        self.assertIn("<iframe", self.client.get(reverse("core:home")).content.decode())

    def test_map_embed_url_wins_over_address(self):
        contact = models.ContactSection.load()
        contact.map_address = "Somewhere"
        contact.map_embed_url = "https://www.google.com/maps/embed?pb=custom"
        contact.save()
        self.assertEqual(
            models.ContactSection.load().map_iframe_url,
            "https://www.google.com/maps/embed?pb=custom",
        )

    def test_hero_word_delays_match_design(self):
        hero = models.HeroSection.load()
        lines = hero.title_lines
        self.assertEqual(lines[0]["words"][0]["delay"], 0.25)
        self.assertEqual(lines[1]["words"][0]["delay"], 0.46)
        self.assertTrue(lines[1]["gradient"])
