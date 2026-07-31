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

# Loads the original copy on a brand-new database. Safe to re-run: existing
# rows are matched on their natural key, so nothing is duplicated and your
# dashboard edits are preserved.
python manage.py seed_content
