from .models import SiteSettings


def site_context(request):
    """Expose the global site settings to every template."""
    try:
        settings_obj = SiteSettings.load()
    except Exception:  # pragma: no cover - database not migrated yet
        settings_obj = None
    return {"site": settings_obj}
