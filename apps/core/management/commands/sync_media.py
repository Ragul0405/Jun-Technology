"""
Copy the images that ship with the repository into MEDIA_ROOT.

`media/` is committed to git, but a production server usually points
DJANGO_MEDIA_ROOT at a persistent disk somewhere else. Without this step the
bundled images would sit in the checkout while the app looked for them on the
disk, and the site would fall back to placeholders.

Existing files are never overwritten, so images uploaded on the live dashboard
always win over the bundled copies.
"""

import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Copy the repository's bundled media files into MEDIA_ROOT."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace files that already exist in MEDIA_ROOT.",
        )

    def handle(self, *args, **options):
        source = Path(settings.BASE_DIR) / "media"
        target = Path(settings.MEDIA_ROOT)

        if not source.exists():
            self.stdout.write("No bundled media directory — nothing to do.")
            return

        if source.resolve() == target.resolve():
            self.stdout.write("MEDIA_ROOT is the bundled directory — nothing to do.")
            return

        copied = skipped = 0
        for path in source.rglob("*"):
            if not path.is_file():
                continue
            destination = target / path.relative_to(source)
            if destination.exists() and not options["overwrite"]:
                skipped += 1
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            copied += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Media synced to {target} — {copied} copied, {skipped} already present."
            )
        )
