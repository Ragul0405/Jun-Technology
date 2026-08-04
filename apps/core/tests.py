import base64
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from . import models

#: Keep seeded/uploaded files out of the real media folder during tests.
TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix="juntech-test-media-")

#: Smallest thing Pillow will accept as an upload.
ONE_PIXEL_GIF = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)


def an_image(name):
    return SimpleUploadedFile(name, ONE_PIXEL_GIF, content_type="image/gif")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PublicSiteTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        call_command("seed_content")

    def test_home_renders_every_section(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        for marker in (
            'id="home"',
            'id="stats"',
            'id="about"',
            'id="services"',
            'id="work"',
            'id="voices"',
            'id="contact"',
            "data-particles",
            "data-marquee",
            "jt-projects",
        ):
            self.assertIn(marker, body)

    def test_home_shows_seeded_content(self):
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertIn("Website Development", body)
        self.assertIn("CoreLogic CRM", body)
        self.assertIn("Sarah Mitchell", body)
        self.assertIn("Projects Delivered", body)

    def test_contact_form_stores_message(self):
        service = models.Service.objects.first()
        response = self.client.post(
            reverse("core:contact_submit"),
            {
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "phone": "+1 555 0100",
                "service": service.pk,
                "subject": "New website",
                "message": "We would like a quote for a new marketing site.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        message = models.ContactMessage.objects.get()
        self.assertEqual(message.name, "Ada Lovelace")
        self.assertEqual(message.status, "new")

    def test_contact_form_rejects_invalid_input(self):
        response = self.client.post(
            reverse("core:contact_submit"),
            {"name": "", "email": "not-an-email", "subject": "", "message": "hi"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])
        self.assertEqual(models.ContactMessage.objects.count(), 0)

    def test_honeypot_blocks_bots(self):
        response = self.client.post(
            reverse("core:contact_submit"),
            {
                "name": "Bot",
                "email": "bot@example.com",
                "service": models.Service.objects.first().pk,
                "subject": "Cheap links",
                "message": "Buy our backlinks today please.",
                "website": "http://spam.example",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(models.ContactMessage.objects.count(), 0)

    def test_seed_is_idempotent(self):
        before = models.Service.objects.count()
        call_command("seed_content")
        self.assertEqual(models.Service.objects.count(), before)

    def test_seed_installs_the_logo(self):
        site = models.SiteSettings.load()
        self.assertTrue(site.logo_mark, "seed_content should install the logo mark")
        first_name = site.logo_mark.name

        call_command("seed_content")
        models.SiteSettings.load().refresh_from_db()
        self.assertEqual(models.SiteSettings.load().logo_mark.name, first_name)

        self.assertIn(site.logo_mark.url, self.client.get(reverse("core:home")).content.decode())

    def test_hidden_items_are_not_rendered(self):
        service = models.Service.objects.create(
            icon="cloud", title="Kubernetes Wrangling", description="Cluster care."
        )
        self.assertIn(
            service.title, self.client.get(reverse("core:home")).content.decode()
        )
        service.is_active = False
        service.save(update_fields=["is_active"])
        self.assertNotIn(
            service.title, self.client.get(reverse("core:home")).content.decode()
        )

    def test_robots_txt_protects_the_admin_areas(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        body = response.content.decode()
        self.assertIn("Disallow: /dashboard/", body)
        self.assertIn("Disallow: /django-admin/", body)
        self.assertIn("Sitemap: http://testserver/sitemap.xml", body)

    def test_sitemap_lists_the_home_page(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<loc>https://testserver/</loc>", response.content.decode())

    def test_service_cards_keep_their_learn_more_line(self):
        # The arrow line is part of the original design — seeding must set it.
        self.assertTrue(
            all(s.link_label for s in models.Service.objects.all()),
            "every seeded service needs a link label",
        )
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertIn("data-arrow", body)
        self.assertIn("Learn more", body)

    def test_services_eyebrow_is_hidden_by_default(self):
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertNotIn("What We Offer", body)
        self.assertIn("Our core services", body)

    def test_eyebrow_reappears_when_set(self):
        section = models.ServicesSection.load()
        section.eyebrow = "What We Do"
        section.save()
        self.assertIn(
            "What We Do", self.client.get(reverse("core:home")).content.decode()
        )

    def test_map_address_builds_an_embed(self):
        contact = models.ContactSection.load()
        self.assertEqual(contact.map_iframe_url, "")  # illustrated map by default

        contact.map_address = "Jun Technology, MG Road, Kochi"
        contact.map_zoom = 17
        contact.save()
        url = models.ContactSection.load().map_iframe_url
        self.assertIn("maps.google.com", url)
        self.assertIn("Jun%20Technology%2C%20MG%20Road%2C%20Kochi", url)
        self.assertIn("z=17", url)
        self.assertIn("output=embed", url)
        self.assertIn("<iframe", self.client.get(reverse("core:home")).content.decode())

    def test_map_embed_url_wins_over_address(self):
        contact = models.ContactSection.load()
        contact.map_address = "Somewhere"
        contact.map_embed_url = "https://www.google.com/maps/embed?pb=custom"
        contact.save()
        self.assertEqual(
            models.ContactSection.load().map_iframe_url,
            "https://www.google.com/maps/embed?pb=custom",
        )

    def test_seed_features_projects_within_the_cap(self):
        featured = list(models.Project.featured())
        self.assertTrue(featured, "seed_content should feature projects in the hero")
        self.assertLessEqual(len(featured), models.MAX_HERO_FEATURED)
        self.assertEqual(
            models.Project.objects.filter(is_featured=True).count(), len(featured)
        )

    def test_seeded_site_shows_the_flip_card_not_the_panel(self):
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertNotIn("Build Health", body)
        self.assertEqual(
            body.count("data-flip-face"), models.Project.featured().count()
        )
        self.assertIn("data-flip-dot", body)
        for project in models.Project.featured():
            self.assertIn(project.title, body)

    def test_hero_falls_back_to_the_panel_with_nothing_featured(self):
        models.Project.objects.update(is_featured=False)
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertIn("Build Health", body)
        self.assertNotIn("data-flip-face", body)

    def test_hero_flip_stops_at_the_featured_limit(self):
        models.Project.objects.update(is_featured=True)
        self.assertGreater(
            models.Project.objects.count(), models.MAX_HERO_FEATURED
        )
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertEqual(body.count("data-flip-face"), models.MAX_HERO_FEATURED)

    def test_hidden_project_never_reaches_the_hero(self):
        models.Project.objects.update(is_featured=False)
        project = models.Project.objects.first()
        project.is_featured = True
        project.is_active = False
        project.save(update_fields=["is_featured", "is_active"])
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertIn("Build Health", body)
        self.assertNotIn("data-flip-face", body)

    def test_seed_leaves_the_collection_alone_without_a_photo(self):
        # Nothing is seeded for the about frame — the photo is always an upload.
        self.assertFalse(models.AboutSection.load().image)
        self.assertEqual(models.AboutImage.objects.count(), 0)

    def test_seed_adopts_an_uploaded_about_photo_into_the_collection(self):
        section = models.AboutSection.load()
        section.image = an_image("studio.gif")
        section.image_alt = "Our studio"
        section.save()

        call_command("seed_content")
        adopted = models.AboutImage.objects.get()
        self.assertEqual(adopted.image.name, models.AboutSection.load().image.name)
        self.assertEqual(adopted.alt, "Our studio")

        # Re-seeding must not pile up duplicates of it.
        call_command("seed_content")
        self.assertEqual(models.AboutImage.objects.count(), 1)

    def _about_html(self):
        """Just the about section — the hero has a flip deck of its own."""
        body = self.client.get(reverse("core:home")).content.decode()
        return body[body.index('id="about"') : body.index('id="services"')]

    def test_about_frame_flips_through_its_images(self):
        for index in range(3):
            models.AboutImage.objects.create(
                image=an_image(f"studio-{index}.gif"), alt=f"Studio shot {index}"
            )
        about = self._about_html()
        self.assertEqual(about.count("data-flip-face"), 3)
        self.assertIn("Studio shot 1", about)

    def test_about_frame_ignores_hidden_images(self):
        models.AboutImage.objects.create(
            image=an_image("hidden.gif"), alt="Hidden shot", is_active=False
        )
        about = self._about_html()
        self.assertNotIn("Hidden shot", about)
        self.assertNotIn("data-flip-face", about)

    # -- portfolio: 12 on the home page, the rest on the listing page ------ #
    def _extra_projects(self, count):
        category = models.ProjectCategory.objects.first()
        for index in range(count):
            models.Project.objects.create(
                title=f"Filler Project {index}",
                category=category,
                stack="Django",
                short_description="Filler.",
                order=100 + index,
            )

    def test_home_shows_every_project_while_under_the_limit(self):
        from apps.core.views import HOME_PROJECT_LIMIT

        self.assertLess(models.Project.objects.count(), HOME_PROJECT_LIMIT)
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertEqual(body.count("data-card"), models.Project.objects.count())
        self.assertNotIn("See all", body)

    def test_home_caps_at_twelve_and_offers_the_listing_page(self):
        from apps.core.views import HOME_PROJECT_LIMIT

        self._extra_projects(9)
        total = models.Project.objects.count()
        self.assertGreater(total, HOME_PROJECT_LIMIT)

        body = self.client.get(reverse("core:home")).content.decode()
        self.assertEqual(body.count("data-card"), HOME_PROJECT_LIMIT)
        self.assertIn(f"See all {total} projects", body)
        self.assertIn(reverse("core:projects"), body)

    def test_listing_page_shows_them_all(self):
        self._extra_projects(9)
        response = self.client.get(reverse("core:projects"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertEqual(body.count("data-card"), models.Project.objects.count())

    def test_listing_page_filters_by_category(self):
        category = models.ProjectCategory.objects.get(slug="business")
        expected = models.Project.objects.filter(is_active=True, category=category)
        response = self.client.get(
            reverse("core:projects"), {"category": category.slug}
        )
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertEqual(body.count("data-card"), expected.count())
        for project in expected:
            self.assertIn(project.title, body)
        self.assertIn(category.name, body)

    def test_unknown_category_falls_back_to_everything(self):
        response = self.client.get(reverse("core:projects"), {"category": "nope"})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["active_category"])
        self.assertEqual(
            response.content.decode().count("data-card"),
            models.Project.objects.filter(is_active=True).count(),
        )

    def test_listing_page_hides_inactive_projects(self):
        project = models.Project.objects.first()
        project.is_active = False
        project.save(update_fields=["is_active"])
        body = self.client.get(reverse("core:projects")).content.decode()
        self.assertNotIn(project.title, body)

    def test_category_pills_link_to_the_listing_page(self):
        body = self.client.get(reverse("core:home")).content.decode()
        for category in models.ProjectCategory.objects.filter(is_active=True):
            self.assertIn(
                f'{reverse("core:projects")}?category={category.slug}', body
            )
        # "All" is pinned outside the ticker, so it appears exactly once; the
        # categories are rendered twice so the marquee loops seamlessly.
        self.assertIn("data-cat-track", body)
        self.assertEqual(body.count('data-filter="all"'), 1)
        for category in models.ProjectCategory.objects.filter(is_active=True):
            self.assertEqual(body.count(f'data-filter="{category.slug}"'), 2)

    def test_section_links_work_away_from_the_home_page(self):
        body = self.client.get(reverse("core:projects")).content.decode()
        self.assertIn('href="/#about"', body)
        self.assertNotIn('href="#about"', body)

    def test_sitemap_lists_the_listing_page(self):
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("<loc>https://testserver/projects/</loc>", body)

    # -- blog --------------------------------------------------------------- #
    def _post(self, title, **extra):
        fields = {
            "excerpt": f"{title} in one sentence.",
            "body": "First paragraph.\n\nSecond paragraph.",
        }
        fields.update(extra)
        return models.BlogPost.objects.create(title=title, **fields)

    def test_blog_page_is_reachable_and_empty_by_default(self):
        response = self.client.get(reverse("core:blog"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn(models.BlogSection.load().heading, body)
        self.assertIn(models.BlogSection.load().empty_message, body)

    def test_blog_lists_posts_newest_first(self):
        import datetime

        old = self._post("Older post", published_at=datetime.date(2026, 1, 1))
        new = self._post("Newer post", published_at=datetime.date(2026, 6, 1))
        body = self.client.get(reverse("core:blog")).content.decode()
        self.assertLess(body.index(new.title), body.index(old.title))
        self.assertNotIn(models.BlogSection.load().empty_message, body)

    def test_blog_post_page_renders_its_paragraphs(self):
        post = self._post("A post with body copy")
        response = self.client.get(post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn("First paragraph.", body)
        self.assertIn("Second paragraph.", body)
        self.assertIn(post.excerpt, body)

    def test_slug_is_built_from_the_title_and_stays_unique(self):
        first = self._post("Shipping faster with Django")
        second = self._post("Shipping faster with Django")
        self.assertEqual(first.slug, "shipping-faster-with-django")
        self.assertEqual(second.slug, "shipping-faster-with-django-2")

    def test_draft_posts_are_hidden_everywhere(self):
        draft = self._post("Not ready yet", is_active=False)
        self.assertNotIn(
            draft.title, self.client.get(reverse("core:blog")).content.decode()
        )
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)

    def test_blog_paginates(self):
        from apps.core.views import BLOG_PAGE_SIZE

        for index in range(BLOG_PAGE_SIZE + 2):
            self._post(f"Post number {index}")
        first = self.client.get(reverse("core:blog"))
        self.assertEqual(len(first.context["posts"]), BLOG_PAGE_SIZE)
        self.assertTrue(first.context["page"].has_next())

        second = self.client.get(reverse("core:blog"), {"page": 2})
        self.assertEqual(len(second.context["posts"]), 2)

    def test_blog_is_in_the_sitemap(self):
        post = self._post("Indexed post")
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("<loc>https://testserver/blog/</loc>", body)
        self.assertIn(f"<loc>https://testserver/blog/{post.slug}/</loc>", body)

    def test_blog_nav_link_is_seeded(self):
        link = models.NavLink.objects.get(label="Blog")
        self.assertEqual(link.target, "/blog/")
        # A page link is not a section anchor, so the scroll-spy ignores it.
        self.assertEqual(link.section_key, "")
        self.assertIn('href="/blog/"', self.client.get(reverse("core:home")).content.decode())

    def _home_blog_html(self):
        """Just the home page's blog section."""
        body = self.client.get(reverse("core:home")).content.decode()
        return body[body.index('id="blog"') : body.index('id="contact"')]

    def test_home_has_no_blog_section_until_something_is_published(self):
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertNotIn('id="blog"', body)

    def test_home_shows_published_posts_under_the_limit(self):
        for index in range(3):
            self._post(f"Home post {index}")
        section = self._home_blog_html()
        self.assertEqual(section.count("data-card"), 3)
        self.assertNotIn("See all", section)

    def test_home_caps_the_blog_at_eight_and_links_to_the_rest(self):
        from apps.core.views import HOME_BLOG_LIMIT

        for index in range(HOME_BLOG_LIMIT + 4):
            self._post(f"Home post {index}")
        total = models.BlogPost.objects.count()
        section = self._home_blog_html()
        self.assertEqual(section.count("data-card"), HOME_BLOG_LIMIT)
        self.assertIn(f"See all {total} posts", section)
        self.assertIn(reverse("core:blog"), section)

    def test_home_blog_section_shows_the_newest_and_skips_drafts(self):
        import datetime

        newest = self._post("Freshest", published_at=datetime.date(2026, 7, 1))
        self._post("Stalest", published_at=datetime.date(2020, 1, 1))
        draft = self._post("Hidden draft", is_active=False)
        section = self._home_blog_html()
        self.assertIn(newest.title, section)
        self.assertNotIn(draft.title, section)
        self.assertLess(section.index("Freshest"), section.index("Stalest"))

    def test_blog_categories_are_seeded_with_slugs(self):
        categories = models.BlogCategory.objects.filter(is_active=True)
        self.assertTrue(categories.exists())
        self.assertTrue(all(c.slug for c in categories))

    def test_blog_filters_by_category(self):
        insights = models.BlogCategory.objects.get(slug="insights")
        design = models.BlogCategory.objects.get(slug="design")
        wanted = self._post("An insight", category=insights)
        self._post("A design note", category=design)

        response = self.client.get(reverse("core:blog"), {"category": "insights"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_category"], insights)
        body = response.content.decode()
        self.assertIn(wanted.title, body)
        self.assertNotIn("A design note", body)
        self.assertIn("1 post in Insights.", body)

    def test_blog_unknown_category_shows_everything(self):
        self._post("Any post")
        response = self.client.get(reverse("core:blog"), {"category": "nope"})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["active_category"])
        self.assertIn("Any post", response.content.decode())

    def test_blog_category_pills_link_to_filtered_lists(self):
        body = self.client.get(reverse("core:blog")).content.decode()
        for category in models.BlogCategory.objects.filter(is_active=True):
            self.assertIn(f'{reverse("core:blog")}?category={category.slug}', body)
        self.assertEqual(body.count('data-filter="all"'), 1)

    def test_post_shows_its_category_and_links_to_it(self):
        category = models.BlogCategory.objects.get(slug="engineering")
        post = self._post("A build note", category=category)
        body = self.client.get(post.get_absolute_url()).content.decode()
        self.assertIn(category.name, body)
        self.assertIn(f'{reverse("core:blog")}?category={category.slug}', body)

    def test_posts_survive_their_category_being_deleted(self):
        category = models.BlogCategory.objects.get(slug="design")
        post = self._post("Outlives its category", category=category)
        category.delete()
        post.refresh_from_db()
        self.assertIsNone(post.category)
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 200)
        self.assertIn(post.title, self.client.get(reverse("core:blog")).content.decode())

    def test_uncategorised_posts_still_appear_in_the_full_list(self):
        post = self._post("No category at all")
        self.assertIsNone(post.category)
        self.assertIn(
            post.title, self.client.get(reverse("core:blog")).content.decode()
        )

    def test_category_paging_keeps_the_filter(self):
        from apps.core.views import BLOG_PAGE_SIZE

        category = models.BlogCategory.objects.get(slug="insights")
        for index in range(BLOG_PAGE_SIZE + 1):
            self._post(f"Insight {index}", category=category)
        body = self.client.get(reverse("core:blog"), {"category": "insights"}).content.decode()
        self.assertIn("?page=2&amp;category=insights", body)

    # -- footer pages, FAQ and service enquiries --------------------------- #
    # -- enquiry service and industry -------------------------------------- #
    def _enquiry(self, **extra):
        payload = {
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "service": models.Service.objects.first().pk,
            "subject": "New website",
            "message": "We would like a quote for a new marketing site.",
        }
        payload.update(extra)
        return self.client.post(reverse("core:contact_submit"), payload)

    def test_enquiry_records_the_chosen_service(self):
        service = models.Service.objects.first()
        self.assertEqual(self._enquiry().status_code, 200)
        message = models.ContactMessage.objects.get()
        self.assertEqual(message.service, service)
        self.assertEqual(message.service_name, service.title)
        self.assertEqual(message.service_label, service.title)

    def test_enquiry_records_the_industry_when_given(self):
        category = models.ProjectCategory.objects.first()
        self._enquiry(category=category.pk)
        message = models.ContactMessage.objects.get()
        self.assertEqual(message.category, category)
        self.assertEqual(message.category_label, category.name)

    def test_industry_is_optional(self):
        self.assertEqual(self._enquiry().status_code, 200)
        self.assertEqual(models.ContactMessage.objects.get().category_label, "\u2014")

    def test_service_is_optional(self):
        response = self._enquiry(service="")
        self.assertEqual(response.status_code, 200)
        message = models.ContactMessage.objects.get()
        self.assertIsNone(message.service)
        self.assertEqual(message.service_label, "—")

    def test_a_hidden_service_cannot_be_chosen(self):
        service = models.Service.objects.first()
        service.is_active = False
        service.save(update_fields=["is_active"])
        response = self._enquiry(service=service.pk)
        self.assertEqual(response.status_code, 400)
        self.assertIn("service", response.json()["errors"])

    def test_enquiry_survives_its_service_being_deleted(self):
        service = models.Service.objects.first()
        title = service.title
        self._enquiry()
        service.delete()

        message = models.ContactMessage.objects.get()
        self.assertIsNone(message.service)
        # The snapshot keeps the record meaningful.
        self.assertEqual(message.service_label, title)

    def test_form_offers_only_live_services_and_categories(self):
        from django.utils.html import escape

        body = self.client.get(reverse("core:home")).content.decode()
        form = body[body.index('<form data-form') : body.index("</form>")]
        for service in models.Service.objects.filter(is_active=True):
            self.assertIn(f'value="{service.pk}"', form)
            self.assertIn(escape(service.title), form)
        for category in models.ProjectCategory.objects.filter(is_active=True):
            self.assertIn(escape(category.name), form)
        self.assertIn('name="service"', form)
        self.assertIn('name="category"', form)

    def test_enquiry_email_names_the_service(self):
        from django.core import mail as django_mail
        from django.test import override_settings

        config = models.EmailSettings.load()
        config.notify_email = "hello@example.com"
        config.save()

        with override_settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
        ):
            self._enquiry(category=models.ProjectCategory.objects.first().pk)

        self.assertEqual(len(django_mail.outbox), 1)
        body = django_mail.outbox[0].body
        self.assertIn(models.Service.objects.first().title, body)
        self.assertIn(models.ProjectCategory.objects.first().name, body)

    def test_terms_and_privacy_pages_render(self):
        from django.utils.html import escape

        for name in ("core:terms", "core:privacy"):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                # "Terms & Conditions" reaches the page escaped.
                self.assertIn(
                    escape(response.context["page"].title),
                    response.content.decode(),
                )

    def test_a_page_taken_offline_returns_404(self):
        page = models.ContentPage.objects.get(slug="terms")
        page.is_active = False
        page.save(update_fields=["is_active"])
        self.assertEqual(self.client.get(reverse("core:terms")).status_code, 404)

    def test_page_body_splits_into_paragraphs_and_headings(self):
        page = models.ContentPage.objects.create(
            slug="sample",
            title="Sample",
            body="A heading:\n\nSome prose that follows it.",
        )
        blocks = page.blocks
        self.assertEqual(len(blocks), 2)
        self.assertTrue(blocks[0]["is_heading"])
        self.assertFalse(blocks[1]["is_heading"])

    def test_faq_page_lists_its_questions(self):
        response = self.client.get(reverse("core:faq"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertTrue(models.FaqItem.objects.exists())
        for item in models.FaqItem.objects.filter(is_active=True):
            self.assertIn(item.question, body)

    def test_hidden_faq_is_not_shown(self):
        item = models.FaqItem.objects.first()
        item.is_active = False
        item.save(update_fields=["is_active"])
        self.assertNotIn(
            item.question, self.client.get(reverse("core:faq")).content.decode()
        )

    def test_footer_links_point_at_the_real_pages(self):
        body = self.client.get(reverse("core:home")).content.decode()
        for path in ("/blog/", "/faq/", "/privacy/", "/terms/"):
            self.assertIn(f'href="{path}"', body)

    def test_footer_services_column_is_filled_from_services(self):
        column = models.FooterColumn.objects.get(title="Services")
        self.assertEqual(column.source, "services")
        self.assertFalse(column.links.exists())

        footer = self._footer_html()
        for service in models.Service.objects.filter(
            is_active=True, show_in_footer=True
        ):
            self.assertIn(service.enquiry_url, footer)

    def _footer_html(self):
        """Only the footer — service cards elsewhere use the same enquiry URL."""
        body = self.client.get(reverse("core:home")).content.decode()
        return body[body.index("<footer") :]

    def test_unfeaturing_a_service_removes_it_from_the_footer(self):
        service = models.Service.objects.first()
        self.assertIn(service.enquiry_url, self._footer_html())

        service.show_in_footer = False
        service.save(update_fields=["show_in_footer"])
        self.assertNotIn(service.enquiry_url, self._footer_html())

    def test_service_enquiry_url_targets_the_contact_form(self):
        service = models.Service.objects.first()
        self.assertEqual(service.enquiry_url, f"/?service={service.slug}#contact")

    def test_services_get_unique_slugs(self):
        first = models.Service.objects.create(
            icon="code", title="Duplicate Name", description="One."
        )
        second = models.Service.objects.create(
            icon="code", title="Duplicate Name", description="Two."
        )
        self.assertEqual(first.slug, "duplicate-name")
        self.assertEqual(second.slug, "duplicate-name-2")

    def test_home_page_config_maps_slugs_to_service_names(self):
        import json
        import re

        body = self.client.get(reverse("core:home")).content.decode()
        config = json.loads(
            re.search(r'<script id="jt-config"[^>]*>(.*?)</script>', body, re.S).group(1)
        )
        services = models.Service.objects.filter(is_active=True)
        self.assertEqual(len(config["services"]), services.count())
        for service in services:
            self.assertEqual(config["services"][service.slug], service.title)

    def test_service_cards_link_to_the_enquiry_form(self):
        body = self.client.get(reverse("core:home")).content.decode()
        service = models.Service.objects.filter(link_url="").first()
        if service:
            self.assertIn(f'data-service-url="{service.enquiry_url}"', body)

    def test_new_pages_are_in_the_sitemap(self):
        body = self.client.get("/sitemap.xml").content.decode()
        for path in ("/faq/", "/terms/", "/privacy/"):
            self.assertIn(f"<loc>https://testserver{path}</loc>", body)

    def test_reading_time_is_sensible(self):
        post = self._post("Long read", body=" ".join(["word"] * 600))
        self.assertEqual(post.reading_minutes, 3)

    def test_hero_word_delays_match_design(self):
        hero = models.HeroSection.load()
        lines = hero.title_lines
        self.assertEqual(lines[0]["words"][0]["delay"], 0.25)
        self.assertEqual(lines[1]["words"][0]["delay"], 0.46)
        self.assertTrue(lines[1]["gradient"])
