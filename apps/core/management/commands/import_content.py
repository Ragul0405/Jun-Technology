"""
Load the shipped content fixture on a server.

This is the deploy-time counterpart to `export_content`. Use it instead of
`seed_content` when a fixture is present — it restores exactly what the site
looked like locally, including which image belongs to which project.

Existing records with the same primary key are overwritten. Enquiries are never
touched, and the SMTP password is not in the fixture, so it survives.
"""

from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import ContactMessage, EmailSettings

DEFAULT_PATH = "fixtures/content.json"


class Command(BaseCommand):
    help = "Load fixtures/content.json into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=DEFAULT_PATH,
            help=f"Fixture to load (default: {DEFAULT_PATH}).",
        )
        parser.add_argument(
            "--fallback-seed",
            action="store_true",
            help="Run seed_content instead of failing when the fixture is missing.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        fixture = Path(settings.BASE_DIR) / options["path"]

        if not fixture.exists():
            if options["fallback_seed"]:
                self.stdout.write(
                    self.style.WARNING(
                        f"No fixture at {fixture} — falling back to seed_content."
                    )
                )
                call_command("seed_content")
                return
            raise CommandError(
                f"No fixture at {fixture}. Run `python manage.py export_content` "
                "locally and commit the result, or pass --fallback-seed."
            )

        # The SMTP password is deliberately absent from the fixture; keep
        # whatever the live server already has.
        existing_password = ""
        if EmailSettings.objects.filter(pk=1).exists():
            existing_password = EmailSettings.objects.get(pk=1).password

        enquiries = ContactMessage.objects.count()

        call_command("loaddata", str(fixture), verbosity=0)

        if existing_password:
            EmailSettings.objects.filter(pk=1).update(password=existing_password)
            self.stdout.write("Kept the SMTP password already saved on this server.")

        self.stdout.write(self.style.SUCCESS(f"Content loaded from {fixture}."))
        self.stdout.write(f"{enquiries} enquiries left untouched.")
        self.stdout.write(
            "If images are missing, run `python manage.py sync_media` and check "
            "your web server serves /media/."
        )
