#!/usr/bin/env bash
# Build step for platforms that run a build command (Render, Railway, Heroku…).
# Point your host's "Build Command" at:  ./build.sh
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Copies the images committed under media/ onto the persistent disk when
# DJANGO_MEDIA_ROOT points somewhere else. Never overwrites files already
# there, so images uploaded on the live dashboard are safe.
python manage.py sync_media

# Loads fixtures/content.json — the content exported from your local dashboard,
# including which image belongs to which project. Falls back to the original
# design's copy if no fixture has been committed. Enquiries are never touched
# and the SMTP password already saved on this server is kept.
python manage.py import_content --fallback-seed
