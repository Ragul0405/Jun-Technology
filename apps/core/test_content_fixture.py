import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase, override_settings

from . import models

TMP = tempfile.mkdtemp(prefix="juntech-fixture-")


@override_settings(BASE_DIR=Path(TMP), MEDIA_ROOT=TMP)
class ContentFixtureTests(TestCase):
    """The export/import pair is how content reaches the deployed server."""

    fixture_name = "fixtures/content.json"

    def _export(self):
        call_command("export_content")
        return Path(TMP) / self.fixture_name

    def test_export_writes_every_content_model(self):
        call_command("seed_content")
        payload = json.loads(self._export().read_text(encoding="utf-8"))
        models_in_file = {row["model"] for row in payload}
        for expected in (
            "core.sitesettings",
            "core.herosection",
            "core.service",
            "core.project",
            "core.projectmetric",
            "core.testimonial",
            "core.contactdetail",
            "core.footerlink",
            "core.sociallink",
        ):
            self.assertIn(expected, models_in_file)

    def test_enquiries_are_never_exported(self):
        models.ContactMessage.objects.create(
            name="Ada", email="ada@example.com", subject="Hi", message="Hello there."
        )
        payload = json.loads(self._export().read_text(encoding="utf-8"))
        self.assertNotIn("core.contactmessage", {row["model"] for row in payload})

    def test_smtp_password_is_never_exported(self):
        config = models.EmailSettings.load()
        config.is_enabled = True
        config.host = "smtp.gmail.com"
        config.username = "hello@example.com"
        config.password = "super-secret-app-password"
        config.from_email = "hello@example.com"
        config.save()

        raw = self._export().read_text(encoding="utf-8")
        self.assertNotIn("super-secret-app-password", raw)

        row = next(
            r for r in json.loads(raw) if r["model"] == "core.emailsettings"
        )
        self.assertEqual(row["fields"]["password"], "")
        # The rest of the configuration still travels.
        self.assertEqual(row["fields"]["host"], "smtp.gmail.com")

        # Exporting must not damage the local database.
        self.assertEqual(models.EmailSettings.load().password, "super-secret-app-password")

    def test_round_trip_restores_content(self):
        call_command("seed_content")
        section = models.ServicesSection.load()
        section.heading = "What we build"
        section.save()
        contact = models.ContactSection.load()
        contact.map_address = "Jun Technology, Kochi"
        contact.save()
        fixture = self._export()

        models.Service.objects.all().delete()
        models.ServicesSection.objects.all().delete()
        models.ContactSection.objects.all().delete()

        call_command("import_content")

        self.assertEqual(models.Service.objects.count(), 8)
        self.assertEqual(models.ServicesSection.load().heading, "What we build")
        self.assertEqual(models.ContactSection.load().map_address, "Jun Technology, Kochi")
        self.assertTrue(fixture.exists())

    def test_import_keeps_the_servers_smtp_password(self):
        call_command("seed_content")
        self._export()  # fixture has an empty password

        config = models.EmailSettings.load()
        config.password = "password-entered-on-the-server"
        config.save()

        call_command("import_content")
        self.assertEqual(
            models.EmailSettings.load().password, "password-entered-on-the-server"
        )

    def test_import_leaves_enquiries_alone(self):
        call_command("seed_content")
        self._export()
        models.ContactMessage.objects.create(
            name="Grace", email="g@example.com", subject="Hi", message="Hello there."
        )
        call_command("import_content")
        self.assertEqual(models.ContactMessage.objects.count(), 1)

    def test_import_falls_back_to_seeding_when_no_fixture(self):
        missing = Path(TMP) / "fixtures" / "content.json"
        if missing.exists():
            missing.unlink()
        call_command("import_content", fallback_seed=True)
        self.assertEqual(models.Service.objects.count(), 8)
