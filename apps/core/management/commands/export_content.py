"""
Write the site's current content to a fixture that ships with the repository.

Run this locally whenever you want the deployed site to pick up the content you
have arranged in the dashboard, then commit `fixtures/content.json`. On the
server, `import_content` loads it.

Deliberately excluded:
  * ContactMessage — visitor enquiries are personal data and stay on the server
    they were sent to.
  * The SMTP password — scrubbed so it never reaches git. Re-enter it once in
    the live dashboard.
"""

from pathlib import Path

from django.apps import apps
from django.core import serializers
from django.core.management.base import BaseCommand

EXCLUDED_MODELS = {"ContactMessage"}
SENSITIVE_FIELDS = {"EmailSettings": ["password"]}

DEFAULT_PATH = "fixtures/content.json"


class Command(BaseCommand):
    help = "Export all editable site content to fixtures/content.json."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=DEFAULT_PATH,
            help=f"Where to write the fixture (default: {DEFAULT_PATH}).",
        )

    def handle(self, *args, **options):
        from django.conf import settings

        target = Path(settings.BASE_DIR) / options["output"]
        target.parent.mkdir(parents=True, exist_ok=True)

        objects, scrubbed = [], []
        for model in apps.get_app_config("core").get_models():
            if model.__name__ in EXCLUDED_MODELS:
                continue
            for obj in model.objects.all():
                for field in SENSITIVE_FIELDS.get(model.__name__, []):
                    if getattr(obj, field, ""):
                        setattr(obj, field, "")
                        scrubbed.append(f"{model.__name__}.{field}")
                objects.append(obj)

        with target.open("w", encoding="utf-8") as handle:
            serializers.serialize(
                "json", objects, indent=2, stream=handle, ensure_ascii=False
            )

        self.stdout.write(
            self.style.SUCCESS(f"Wrote {len(objects)} records to {target}.")
        )
        if scrubbed:
            self.stdout.write(
                self.style.WARNING(
                    "Left out of the fixture for safety: "
                    + ", ".join(sorted(set(scrubbed)))
                    + ". Re-enter it in the live dashboard."
                )
            )
            email = apps.get_model("core", "EmailSettings").objects.filter(pk=1).first()
            if email and email.is_enabled:
                self.stdout.write(
                    self.style.WARNING(
                        "  Heads up: SMTP is switched on but the password does not "
                        "ship. After deploying, open Dashboard → Email / SMTP, "
                        "enter the password, save, and press Send test email — "
                        "until then enquiry notifications will fail to send "
                        "(the enquiries themselves are still saved)."
                    )
                )
        self.stdout.write(
            "Enquiries (ContactMessage) are never exported. "
            "Commit the fixture, then run `python manage.py import_content` on the server."
        )
