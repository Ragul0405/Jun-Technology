from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

from ..icons import ICONS

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_href(context, target):
    """
    A navigation target that still works away from the home page.

    Section links are bare anchors like `#about`, which point at nothing on the
    project listing page — so off the home page they are rewritten to
    `/#about`.
    """
    if target.startswith("#") and not context.get("is_home", False):
        return reverse("core:home") + target
    return target


@register.simple_tag
def icon(key, stroke="currentColor", size="18px", width="1.6", extra=""):
    """Render one of the design's SVG icons with the original markup."""
    body = ICONS.get(key)
    if not body:
        return ""
    style = f"width:{size};height:{size}" + (f";{extra}" if extra else "")
    return mark_safe(
        f'<svg viewBox="0 0 24 24" fill="none" stroke="{stroke}" '
        f'stroke-width="{width}" style="{style}">{body}</svg>'
    )


@register.filter
def multiply(value, factor):
    """Small helper used for the staggered reveal delays."""
    try:
        return int(float(value) * float(factor))
    except (TypeError, ValueError):
        return 0


@register.filter
def stagger(index, step=80):
    """Reveal delay in milliseconds for the item at `index`."""
    try:
        return int(index) * int(step)
    except (TypeError, ValueError):
        return 0


@register.filter
def modulo(value, divisor):
    """Wrap an index so reveal delays repeat per row, as in the original design."""
    try:
        return int(value) % int(divisor)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0


@register.filter
def ring_delay(index):
    """Testimonial avatar pulse offset — 0s, .6s, 1.2s, 1.8s, …"""
    try:
        return f"{round(int(index) * 0.6, 1)}s"
    except (TypeError, ValueError):
        return "0s"
