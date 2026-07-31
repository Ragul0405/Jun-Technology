from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import SiteSettings


class StaticViewSitemap(Sitemap):
    """The marketing site is a single page, so the sitemap lists just that."""

    changefreq = "weekly"
    priority = 1.0
    protocol = "https"

    def items(self):
        return ["core:home"]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        return SiteSettings.load().updated_at


SITEMAPS = {"static": StaticViewSitemap}
