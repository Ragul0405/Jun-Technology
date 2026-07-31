# Jun Technology — Django site + super admin dashboard

The original static design converted to a production Django project, plus a
super-admin dashboard where every word, number and image on the page can be
edited. **The public design is unchanged** — the markup, inline styles,
keyframes and interactions are ported verbatim; only the content source moved
from hard-coded HTML into the database.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_content      # loads the original copy, projects, testimonials…
python manage.py createsuperuser   # your dashboard login
python manage.py runserver
```

- Website — http://127.0.0.1:8000/
- Super admin — http://127.0.0.1:8000/dashboard/
- Django admin (developer fallback) — http://127.0.0.1:8000/django-admin/
- `robots.txt` and `sitemap.xml` are served at the site root. `robots.txt`
  allows the site but blocks `/dashboard/` and `/django-admin/`, and points at
  the sitemap.

`seed_content` installs the logo mark into the media folder for you. The
remaining images start empty and show the same neutral placeholder frame the
prototype used — upload them from the dashboard: **Dashboard → Images to
upload** lists every slot still waiting for a file.

## What the super admin controls

| Screen | Controls |
| --- | --- |
| Brand & SEO | Logo, favicon, brand name, tagline, header button, accent colours, default theme, loader/cursor/particles toggles, meta tags, OG image, analytics ID |
| Navigation | Menu labels, targets and order (header + mobile menu) |
| Hero | Badge, three headline lines, subtitle, both buttons, floating "Build Health" panel, floating award badge |
| Hero highlights | The dotted proof points under the buttons |
| Statistics | Icon, number, suffix, label and accent for each counter |
| About | Eyebrow, heading, body, **studio photo**, floating badge |
| About cards | Mission / Vision / Why-choose-us cards |
| Services | Section heading plus each service's icon, title and copy |
| Portfolio | Section heading, categories (they drive the filter pills), and each project's **card image**, **case-study image**, stack, descriptions, key numbers and **gallery images** |
| Testimonials | Section heading, scroll speed, and each quote with **author photo** |
| Contact & map | Copy, contact detail rows, the map location, button and success text |
| Email / SMTP | Where enquiries are emailed, the mail server used to send them, and a "send test email" button |
| Footer | Blurb, copyright, columns, links, social links |
| Enquiries | Every contact-form submission, with status tracking |

Every repeatable item has an **order** number and a **Visible** toggle, so
content can be reordered or hidden without deleting it.

## Image slots

The prototype's `<image-slot>` elements became real uploads:

| Slot | Where to set it |
| --- | --- |
| Logo mark (nav, loader, footer) | Brand & SEO → Logo mark *(seeded)* |
| Favicon / social share image | Brand & SEO |
| About photo | About section → Image |
| Project card image (6 cards) | Projects → *project* → Card image |
| Project case-study hero | Projects → *project* → Case-study image |
| Project gallery (3 per project) | Projects → *project* → Gallery |
| Testimonial avatars | Testimonials → *testimonial* → Avatar |

Uploads are validated as images and capped at `DJANGO_MAX_UPLOAD_SIZE`
(8 MB by default). The `media/` folder is committed to git so uploaded images
travel with the code; `python manage.py sync_media` copies them onto a
persistent disk when `DJANGO_MEDIA_ROOT` points elsewhere, never overwriting a
file that is already there. Note that image *files* ship but the database rows
pointing at them do not — see [DEPLOY.md §3a](DEPLOY.md).

## Setting the map location

**Dashboard → Contact & map.** Three options, in priority order:

1. **Map address** *(easiest)* — type the address or place name exactly as it
   appears on Google Maps, e.g. `Jun Technology, MG Road, Kochi, Kerala`. A
   real Google map loads at that spot. **No API key or billing account
   needed.** Use **Map zoom** to frame it (15 = neighbourhood, 17 = street,
   19 = building).
2. **Map embed URL** *(precise)* — on Google Maps find your place →
   **Share** → **Embed a map** → **Copy HTML**, then paste only the value
   inside `src="…"` (it starts `https://www.google.com/maps/embed?pb=`). This
   overrides the address and is the way to embed a specific pinned business
   listing or Street View.
3. **Neither** — the original hand-drawn SVG map from the design is shown.
   `Map street label` and `Map area label` are the two words drawn on it.

`Map label` is the small caption in the bottom-left corner in all three cases,
and **Show map** hides the panel entirely.

## Sending mail (SMTP)

**Dashboard → Email / SMTP.** Fill in **Send enquiries to** (the inbox that
receives contact-form submissions), then the mail server details, tick **Use
these settings**, save, and press **Send test email**. The result — success or
the exact server error — is shown on the page.

| Provider | SMTP server | Port | Security |
| --- | --- | --- | --- |
| Gmail / Google Workspace | `smtp.gmail.com` | 587 | TLS |
| Zoho Mail (India) | `smtp.zoho.in` | 587 | TLS |
| Hostinger | `smtp.hostinger.com` | 587 | TLS |
| Microsoft 365 | `smtp.office365.com` | 587 | TLS |
| Brevo / SendGrid | `smtp-relay.brevo.com` / `smtp.sendgrid.net` | 587 | TLS |

Notes:

- Use a provider **app password**, not your main account password. For Gmail
  that means turning on 2-step verification, then Google Account → Security →
  App passwords.
- **Send from** usually has to match the username — most providers reject a
  mismatched sender.
- Pick TLS *or* SSL, never both (587 = TLS, 465 = SSL).
- The password is stored in this site's database and is never rendered back
  into the page. Leave the field blank when saving to keep the existing one.
- Leaving **Use these settings** off falls back to the `DJANGO_EMAIL_*`
  environment variables, which is the more secure option for production since
  the password then lives only in `.env`.
- If mail fails, the enquiry is still saved — visitors never see an error and
  nothing is lost. Everything is in **Dashboard → Enquiries** regardless.

## Project layout

```
manage.py          repository root — point your host here
Procfile           release + web process for Heroku-style hosts
build.sh           install → collectstatic → migrate → seed
DEPLOY.md          deployment checklist
config/            settings, urls, wsgi/asgi
apps/core/         content models, public views, mail, seed command,
                   icon catalogue, sitemap + robots.txt
apps/dashboard/    super-admin views, forms and the section registry
templates/site/    the converted design (one partial per section)
templates/dashboard/
static/css/site.css        keyframes + light-theme variables (verbatim)
static/js/site.js          the prototype's behaviour as plain JS
reference/original-design.html   the untouched original, never served
scripts/compare_design.py        design-parity check
```

Adding a new editable section means adding one entry to
`apps/dashboard/registry.py` — the list, form, delete and sidebar screens are
generic.

## Verifying the design did not drift

```bash
python manage.py test              # 39 tests: rendering, content, SEO, mail, form, dashboard CRUD
python scripts/compare_design.py   # every inline style of the original must still render
```

`compare_design.py` extracts every `style="…"` declaration from
`reference/original-design.html` — the untouched original design, kept purely
as a comparison fixture — and asserts each one still appears in the rendered
page (or in the pop-up markup that `site.js` builds). It currently reports
**0 missing**. Delete the reference file and the script together if you would
rather not ship them.

## Deployment

Full checklist in **[DEPLOY.md](DEPLOY.md)**. In short:

1. Copy `.env.example` to `.env` and set at minimum `DJANGO_SECRET_KEY`,
   `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` and
   `DJANGO_CSRF_TRUSTED_ORIGINS`.
2. Point `DJANGO_MEDIA_ROOT` at persistent storage — uploaded images live
   there and must survive redeploys.
3. `python manage.py collectstatic --noinput`
4. `python manage.py migrate` then `seed_content` on a fresh database.
5. Serve with `gunicorn config.wsgi:application` behind nginx/Caddy.
   Static files are handled by WhiteNoise; `/media/` must be served by the web
   server (Django only serves it while `DEBUG=True`).
6. `python manage.py check --deploy` should report no issues.

With `DEBUG=False` the project enables HTTPS redirects, HSTS, secure cookies
and `X-Frame-Options: DENY`.

### Security notes

- Dashboard access requires an authenticated **staff** user; the sign-in page
  is at `/dashboard/login/` and is `noindex`.
- The contact form is CSRF-protected, honeypot-guarded and server-validated;
  submissions are stored and optionally emailed (see **Sending mail** above).
- The SMTP password is write-only in the UI. It is stored in the database in
  plain text, so prefer the `.env` route in production and always use a
  provider app password that can be revoked on its own.
- Project data reaches the pop-up through `json_script`, and the pop-up is
  built with DOM APIs rather than `innerHTML`, so editor content cannot inject
  markup.
