"""
Design-parity check.

Renders the Django home page and compares every inline `style="…"` declaration
against the original static design file. Any style present in the original but
missing from the render is reported — that is what a design regression would
look like.

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


def norm(style):
    return re.sub(r"\s+", " ", style).strip().rstrip(";")


def collect(html):
    return {norm(m) for m in STYLE_RE.findall(html) if not PLACEHOLDER_RE.search(m)}


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
    rendered = collect(Client().get("/").content.decode())
    js = js_source()

    missing = sorted(
        s for s in original - rendered
        if not any(token in s for token in IGNORE_SUBSTRINGS) and not in_js(s, js)
    )

    print(f"original styles : {len(original)}")
    print(f"rendered styles : {len(rendered)}")
    print(f"missing         : {len(missing)}")
    for style in missing:
        print("  -", style[:150])
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
