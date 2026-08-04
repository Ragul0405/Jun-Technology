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
- All projects — http://127.0.0.1:8000/projects/ (add `?category=<slug>` to filter)
- Blog — http://127.0.0.1:8000/blog/
- FAQ — http://127.0.0.1:8000/faq/
- Terms — http://127.0.0.1:8000/terms/ · Privacy — http://127.0.0.1:8000/privacy/
- Super admin — http://127.0.0.1:8000/dashboard/
- Django admin (developer fallback) — http://127.0.0.1:8000/django-admin/
- `robots.txt` and `sitemap.xml` are served at the site root. `robots.txt`
  allows the site but blocks `/dashboard/` and `/django-admin/`, and points at
  the sitemap.

`seed_content` installs the logo mark into the media folder for you. Any image
still missing shows the same neutral placeholder frame the prototype used —
upload it from the dashboard: **Dashboard → Images to upload** lists every slot
still waiting for a file.

Content commands:

| Command | Use |
| --- | --- |
| `seed_content` | Load the original design's copy into an empty database |
| `export_content` | Save your dashboard content to `fixtures/content.json` to commit |
| `import_content` | Load that fixture on the server (`build.sh` does this) |
| `sync_media` | Copy bundled images onto a persistent `MEDIA_ROOT` |
| `seed_demo` | Add bulk demo projects and posts to try the site at real volume |
| `seed_demo --clear` | Take every demo row back out again |

## What the super admin controls

| Screen | Controls |
| --- | --- |
| Brand & SEO | Logo, favicon, brand name, tagline, header button, accent colours, default theme, loader/cursor/particles toggles, meta tags, OG image, analytics ID |
| Navigation | Menu labels, targets and order (header + mobile menu) |
| Hero | Badge, three headline lines, subtitle, both buttons, **which projects the flip card shows**, floating "Build Health" panel, floating award badge |
| Hero highlights | The dotted proof points under the buttons |
| Statistics | Icon, number, suffix, label and accent for each counter |
| About | Eyebrow, heading, body, floating badge, **fallback photo**, and the five **photo slots** the frame flips through |
| About cards | Mission / Vision / Why-choose-us cards |
| Services | Section heading plus each service's icon, title and copy |
| Portfolio | Section heading, categories (they drive the ticker and the listing page), and each project's **card image**, **case-study image**, stack, descriptions, key numbers and **gallery images** |
| Testimonials | Section heading, scroll speed, and each quote with **author photo** |
| Blog page | The blog's heading, intro copy and its empty-state message |
| Blog categories | The filters on the blog page |
| FAQ page | The FAQ page's heading and intro |
| FAQs | The questions and answers themselves |
| Pages | The terms and privacy pages |
| Posts | Every article — title, cover, excerpt, body, author, publish date, draft toggle |
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
| About photos (up to 5, flipped) | About section → Photo frame |
| About photo (fallback, used while every slot is empty) | About section → Fallback image |
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

## The splash cursor

The pointer stirs a WebGL fluid simulation that splashes in the brand accent
colours — a vanilla port of the React Bits "Splash Cursor" effect, itself built
on Pavel Dobryakov's WebGL Fluid Simulation (MIT). It lives in
`static/js/splash-cursor.js` with no build step and no dependencies.

It turns itself off, silently and with no layout change, when:

- **Custom cursor** is unticked in Brand & SEO;
- the visitor is on a touch device (no fine pointer);
- the browser or driver cannot give it a float render target.

Clicking adds a burst. The classic dot and ring still ride on top, so the
hover labels (“View case study” and friends) are unaffected.

## The two flip cards

Both the hero card and the about frame 3D-flip through a small set of items.
Neither is on by default — each falls back to the original single-item design
until you give it something to cycle through, so an untouched site looks
exactly as it always did.

Each is controlled on the screen for its own section — there is no separate
page to hunt for, and both save with that screen's one button.

| Card | Where | Limit | Rhythm |
| --- | --- | --- | --- |
| Hero | **Hero → Featured projects** — tick the projects to show | 5 projects | Flips every 4.2s |
| About frame | **About → Photo frame** — five upload slots | 5 photos | Flips every 5s |

Slot position is the order, so nothing has to be numbered by hand, and the
hero's line-up is only ever set in one place (editing a project cannot change
it).

`seed_content` features three projects, so the hero card is live on a fresh
install. It seeds no about photos — those are always uploads — but it does move
an existing **About section → Fallback image** into the photo slots the
first time it runs, so the photo ends up where the flip looks for it. Upload a
second photo there and the frame starts flipping.

- The limits are enforced when you save. Trying to feature a sixth project, or
  add a sixth about photo, is refused with a message naming what is already
  using the slots so you know what to free up.
- Both pause while the pointer is over them, and neither runs in a background
  browser tab.
- With more than one item a row of dots appears; clicking one jumps straight to
  that card.
- Hiding a project or photo (the **Visible** toggle) takes it out of the
  rotation without un-featuring or deleting it.
- The hero card shows the project's category, card image, title, technology
  line and its first two key numbers. Empty slots fall back to the same neutral
  placeholder frame used elsewhere.

## The portfolio

The home page shows at most **12** projects, newest order first, with a
**See all N projects** button underneath when there are more. The full list
lives at `/projects/`. (The blog section below it works the same way, capped
at 8 — see **The blog**.)

- **All** is pinned on the left so it is always reachable; the categories run
  past it on a **ticker** that pauses while the pointer is over it. Each pill is a link to `/projects/?category=<slug>`,
  so filtering is done by the server and the result is a real, shareable,
  indexable URL rather than a JavaScript toggle.
- An unknown `?category=` shows everything rather than a 404.
- **Cards are one fixed size.** Every row is as tall as the tallest card, each
  card fills its row, titles reserve two lines and the description two more, so
  a long title or a sparse category can never make one card a different size
  from another. Hovering fades the description in rather than growing the card.
- The listing page uses `auto-fill` so a category with two projects keeps
  card-sized cards instead of stretching them across the row.
- `/projects/` is in the sitemap, and section links in the header and footer
  become `/#about` style links away from the home page so they still work.

## The blog

A separate section at `/blog/`, with each article at `/blog/<slug>/`, so the
marketing team can publish without a developer. The home page carries the
**8 most recent** posts with a **See all N posts** button beneath, and hides
the section entirely until something is published.

- **Dashboard → Blog → Posts.** Title, category, cover image, excerpt, body,
  author and publish date. The web address is built from the title unless one
  is typed, and duplicate titles get `-2`, `-3` suffixes rather than colliding.
- **Categories** work like the portfolio's: **Dashboard → Blog → Categories**,
  shown as the same pinned-**All**-plus-ticker filter, each linking to
  `/blog/?category=<slug>`. Paging keeps the filter.
  A category is optional — an uncategorised post still appears under **All** —
  and deleting one leaves its posts uncategorised rather than deleting them.
- Posts are ordered by **publish date**, newest first — nothing to renumber
  when publishing daily — and paginate 9 to a page.
- Untick **Is active** to keep a post as a draft: it disappears from the list
  and its URL returns 404.
- The body is plain text. Leave a blank line between paragraphs and they are
  rendered as separate `<p>` elements — never as raw HTML, so a pasted article
  cannot inject markup into the page.
- Reading time is estimated at 200 words per minute.
- **Dashboard → Blog → Blog page** holds the heading, intro copy, and the
  message shown while nothing is published.
- The blog and every published post are in `sitemap.xml`; posts carry their own
  `<title>`, description and OG image.

`seed_content` creates four starter categories (Insights, Engineering, Design,
Company news) so the filters work from day one — rename or delete them freely.
No articles are seeded; those are the marketing team's to write. Until the
first one is published the page shows its empty-state message.

## Demo content

`seed_content` loads the real copy of the original design. `seed_demo` is
separate, and exists only to fill the site out while you are looking at it:

```bash
python manage.py seed_demo                    # 24 projects + 24 posts
python manage.py seed_demo --projects 40 --posts 40
python manage.py seed_demo --clear            # remove them all again
```

It only ever touches rows whose titles are in its own catalogue, so `--clear`
takes every one of them out without risking anything you have written. Run it
to see the home page cap at 12 with its **See all** button, the listing page
filter down by category, and the blog paginate.

**Do not ship it.** Run `seed_demo --clear` before exporting content for the
live site.

## Footer, pages and service enquiries

**Services column.** The footer's services column fills itself from the
services ticked **Feature in footer** (Dashboard → Services). Each one links to
`/?service=<slug>#contact`, which opens the home page at the contact form with
the subject already filled in — “UI/UX Design enquiry”. The slug is looked up
against the services on the page, so nothing from the URL is written into the
form verbatim. Service cards on the home page do the same unless the service
has its own **Link URL**.

A column's **Source** decides this: *The links below* (the default, manual
links) or *Featured services*.

**Terms and privacy** live at `/terms/` and `/privacy/`, edited under
**Dashboard → Pages**. Leave a blank line between paragraphs; a short line
ending in a colon becomes a sub-heading. Untick **Is active** and the page
returns 404.

> Both ship as **drafts written by your developers, not legal advice** — the
> last paragraph of each says so. Have them reviewed before launch.

**FAQ** lives at `/faq/` as a keyboard-accessible `<details>` accordion, with
the copy under **Dashboard → FAQ page** and the questions under **FAQs**.

All three are in `sitemap.xml`, and the footer's Resources column links to
them.

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
build.sh           install → collectstatic → migrate → sync_media → import_content
DEPLOY.md          deployment checklist
fixtures/content.json   your dashboard content, exported for the server
media/             uploaded images (committed, so they ship)
config/            settings, urls, wsgi/asgi
apps/core/         content models, public views, mail, seed command,
                   icon catalogue, sitemap + robots.txt
apps/dashboard/    super-admin views, forms and the section registry
templates/site/    the converted design (one partial per section), plus
                   projects.html, blog.html and blog_post.html.
                   _project_card.html and _blog_card.html are shared by the
                   home page and their listing pages so they cannot drift
templates/dashboard/
static/css/site.css        keyframes + light-theme variables (verbatim)
static/js/site.js          the prototype's behaviour as plain JS
static/js/splash-cursor.js WebGL fluid "splash cursor" (no dependencies)
reference/original-design.html   the untouched original, never served
scripts/compare_design.py        design-parity check
```

Adding a new editable section means adding one entry to
`apps/dashboard/registry.py` — the list, form, delete and sidebar screens are
generic.

## Verifying the design did not drift

```bash
python manage.py test              # 106 tests: rendering, content, SEO, mail, fixtures, flip cards, dashboard CRUD
python scripts/compare_design.py   # every inline style of the original must still render
```

It reports `superseded` separately from `missing`: a prototype element the
client has since asked us to replace is named in the script with its reason,
while anything else that stops rendering still fails the check.

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
