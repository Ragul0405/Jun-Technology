# Deployment checklist

Works on any host that runs Python. `manage.py` is at the repository root.

## 1. Environment variables

Copy `.env.example` to `.env` (or set these in your host's dashboard). The four
that matter:

```
DJANGO_SECRET_KEY=<50+ random characters — never reuse the dev key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=juntechnology.com,www.juntechnology.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://juntechnology.com,https://www.juntechnology.com
```

Generate a key with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

With `DJANGO_DEBUG=False` the project switches on HTTPS redirects, HSTS, secure
cookies and `X-Frame-Options: DENY` automatically.

## 2. Database

SQLite works for a brochure site like this one. For Postgres, set:

```
DATABASE_URL=postgres://user:password@host:5432/dbname
```

`psycopg` is already in `requirements.txt`.

## 3. Media files — read this one

**`media/` is committed to git**, so the images already uploaded travel with
the code. Three things follow:

- **The database must ship too, or the images are orphaned.** Image *files*
  live in `media/`; the rows that point at them live in the database. Deploying
  the files without the matching database gives you a fresh, empty site with
  unused image files sitting on disk. See §3a.
- Django does **not** serve `/media/` when `DEBUG=False`. Your web server must
  (nginx snippet at the bottom). WhiteNoise handles `/static/` only.
- If you set `DJANGO_MEDIA_ROOT` to a persistent disk (recommended — see
  below), the bundled images are not there automatically. `build.sh` runs
  `python manage.py sync_media`, which copies them across without ever
  overwriting a file already on the disk. Run it by hand after any deploy that
  skips the build script.

Prefer a **persistent disk** for `DJANGO_MEDIA_ROOT` on any host with an
ephemeral filesystem (Heroku, plain Render web services). Otherwise every image
uploaded on the live dashboard disappears at the next deploy.

Images uploaded on the live site afterwards are **not** in git. Before your
next deploy, either download them into `media/` and commit, or accept that
`sync_media` will leave the live ones untouched (it skips existing files).

### 3a. Shipping your content

The database itself is gitignored, so content travels as a fixture instead:
**`fixtures/content.json`**, which *is* committed. It holds every dashboard
edit — the copy, the map address, the mail settings, and which image belongs
to which project — so the deployed site comes up looking exactly like your
local one.

**Locally**, whenever you change content and want it on the server:

```bash
python manage.py export_content     # rewrites fixtures/content.json
git add fixtures/content.json media/
git commit -m "Update site content"
```

**On the server**, after `migrate`:

```bash
python manage.py import_content
```

`build.sh` already runs it (with `--fallback-seed`, so a deploy without a
fixture still comes up with the original design's copy).

What the fixture deliberately does **not** contain:

| Not exported | Why | What to do |
| --- | --- | --- |
| Enquiries (`ContactMessage`) | Visitor personal data | Nothing — they stay on the server that received them, and `import_content` never deletes them |
| The SMTP password | Secrets must not enter git | Enter it once in the live dashboard; re-running `import_content` keeps it |
| Admin users | Password hashes must not enter git | `python manage.py createsuperuser` on the server |

> **SMTP is switched on in your current export.** The host, username and
> "send enquiries to" address travel, but the password does not. After the
> first deploy open **Dashboard → Email / SMTP**, enter the password, save, and
> press **Send test email**. Until you do, notification emails fail to send —
> the enquiries themselves are still saved and visible in the dashboard.

`import_content` overwrites records with matching primary keys, so it is safe
to re-run. Do **not** run `seed_content` first on a fresh database; go straight
to `import_content`.

## 4. Build and run

```bash
./build.sh    # install → collectstatic → migrate → sync_media → import_content
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

A `Procfile` and `runtime.txt` are included for platforms that use them.

## 5. First run on the live site

```bash
python manage.py createsuperuser
```

Then sign in at `https://yourdomain.com/dashboard/` and:

1. **Email / SMTP** — enter the password (it does not ship), save, press
   *Send test email*.
2. **Brand & SEO** — set `canonical_url` to the live domain.
3. Upload any remaining images — the dashboard home lists what is missing.
4. Submit the contact form on the live site once and confirm it appears in
   **Enquiries** and lands in your inbox.

## 6. Verify

```bash
python manage.py check --deploy      # must report no issues
python manage.py test                # 46 tests
python scripts/compare_design.py     # must print "missing: 0"
```

Then load the site and confirm: the loader plays, the aurora and particles
animate, counters count up, the portfolio filters work, a project pop-up opens,
the theme toggle switches, and the contact form submits and lands in
**Dashboard → Enquiries**.

Also check `https://yourdomain.com/robots.txt` points at your real domain's
sitemap.

## nginx snippet

If you are on a VPS, `/media/` and `/static/` need serving directly:

```nginx
server {
    server_name juntechnology.com www.juntechnology.com;
    client_max_body_size 10M;              # image uploads

    location /static/ { alias /var/www/juntech/staticfiles/; expires 30d; }
    location /media/  { alias /var/www/juntech/media/;       expires 7d;  }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

`X-Forwarded-Proto` matters — the project reads it to know the request was
HTTPS.

## Notes

- `reference/original-design.html` is the untouched original design, kept only
  so `scripts/compare_design.py` can prove the Django output still matches it.
  It is never served. Delete it and the script if you do not want it shipped.
- `db.sqlite3` is gitignored on purpose — it holds password hashes. Content
  travels in `fixtures/content.json` instead (§3a); admin users are created on
  the server with `createsuperuser`.
- Re-export the fixture (`python manage.py export_content`) any time you change
  content locally and want it on the server. If you only ever edit through the
  live dashboard, you never need it again.
