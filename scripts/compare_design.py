"""
Design-parity check.

Renders the Django home page and compares every inline `style="…"` declaration
against the original static design file. Any style present in the original but
missing from the render is reported — that is what a design regression would
look like.

The hero and about cards each have two mutually exclusive states: the flip deck
when content is featured, and the original single-panel design when it is not.
Both are rendered and their styles pooled, so neither branch can rot unnoticed
just because the current database happens to use the other one.

Usage:  python scripts/compare_design.py [path/to/original.html]
"""

import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.test import Client  # noqa: E402

DEFAULT_ORIGINAL = BASE_DIR / "reference" / "original-design.html"

STYLE_RE = re.compile(r'style="([^"]+)"')
PLACEHOLDER_RE = re.compile(r"\{\{[^}]*\}\}")

# Styles that legitimately differ: prototype-only chrome and per-item values
# that the database now supplies (animation delays, accent colours, …).
IGNORE_SUBSTRINGS = (
    "animation:wordUp",          # per-word delay comes from the headline text
    "animation:pulseRing 3s",    # testimonial avatar offset is per-row
    "animation:marquee",         # duration is editable
    "transition:opacity .7s ease .",  # pop-up gallery cells: delay built per index in site.js
)

# Parts of the prototype the client has since asked us to replace. Listed
# explicitly, with the reason, so a deliberate change reads differently from a
# regression — anything not named here that stops rendering is still a failure.
SUPERSEDED = {
    "display:flex;flex-wrap:wrap;justify-content:center;gap:10px;margin-top:34px":
        "portfolio filter row — replaced by the scrolling category ticker, "
        "whose pills link to the project listing page",
}


def norm(style):
    return re.sub(r"\s+", " ", style).strip().rstrip(";")


def collect(html):
    return {norm(m) for m in STYLE_RE.findall(html) if not PLACEHOLDER_RE.search(m)}


def render_both_states():
    """The page as it stands, plus the same page with every flip deck emptied."""
    from django.db import transaction

    from apps.core.models import AboutImage, Project

    client = Client()
    pages = [client.get("/").content.decode()]

    with transaction.atomic():
        Project.objects.update(is_featured=False)
        AboutImage.objects.update(is_active=False)
        pages.append(client.get("/").content.decode())
        transaction.set_rollback(True)  # never touch the real content

    return pages


def js_source():
    """site.js builds the project pop-up's tiles and gallery at open time."""
    return (BASE_DIR / "static" / "js" / "site.js").read_text(encoding="utf-8")


def in_js(style, js):
    """True when every declaration of `style` appears in the JS cssText."""
    return all(part.strip() in js for part in style.split(";") if part.strip())


def main():
    original_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ORIGINAL
    if not original_path.exists():
        print(f"Original design file not found: {original_path}")
        return 1

    original = collect(original_path.read_text(encoding="utf-8"))
    rendered = set()
    for page in render_both_states():
        rendered |= collect(page)
    js = js_source()

    gone = [
        s for s in original - rendered
        if not any(token in s for token in IGNORE_SUBSTRINGS) and not in_js(s, js)
    ]
    superseded = sorted(s for s in gone if s in SUPERSEDED)
    missing = sorted(s for s in gone if s not in SUPERSEDED)

    print(f"original styles : {len(original)}")
    print(f"rendered styles : {len(rendered)}")
    print(f"superseded      : {len(superseded)}")
    for style in superseded:
        print("  ~", SUPERSEDED[style])
    print(f"missing         : {len(missing)}")
    for style in missing:
        print("  -", style[:150])
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
