from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import BlogPost, SiteSettings


class StaticViewSitemap(Sitemap):
    """The site's fixed pages."""

    changefreq = "weekly"
    protocol = "https"

    def items(self):
        return ["core:home", "core:projects", "core:blog", "core:faq", "core:terms", "core:privacy"]

    def priority(self, item):
        return 1.0 if item == "core:home" else 0.8

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        return SiteSettings.load().updated_at


class BlogSitemap(Sitemap):
    """Every published article."""

    changefreq = "monthly"
    priority = 0.6
    protocol = "https"

    def items(self):
        return BlogPost.objects.filter(is_active=True)

    def lastmod(self, post):
        return post.updated_at


SITEMAPS = {"static": StaticViewSitemap, "blog": BlogSitemap}
