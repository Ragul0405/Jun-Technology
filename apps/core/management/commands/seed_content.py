"""
Populate the database with the content of the original static design.

Running it twice is safe: singletons are updated in place and repeatable rows
are matched on a natural key, so no duplicates are created. Pass --reset to
wipe the repeatable rows first.
"""

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core import models


TERMS_BLOCKS = ['Using this website:',
    'By using this website you agree to these terms. If you do not agree with them, please stop using the site.',
    'Our work:',
    'Every engagement is governed by the written proposal and statement of work signed by both parties. Where those documents and these terms differ, the signed documents win.',
    'Intellectual property:',
    'The design, text, graphics and code of this website belong to us unless stated otherwise. Work produced for a client transfers to that client on final payment, as set out in the relevant proposal.',
    'Liability:',
    'We take care to keep the information on this site accurate but make no warranty that it is complete or current. We are not liable for loss arising from reliance on it.',
    'Changes:',
    'We may update these terms. The date at the top of this page shows when they were last changed.',
    'REPLACE THIS PAGE before launch. It is a starting point written by your developers, not legal advice — have your solicitor review it.']

PRIVACY_BLOCKS = ['What we collect:',
    'When you send an enquiry we collect the name, email address, phone number, subject and message you type into the form, along with your IP address and browser, which are recorded to help us identify spam.',
    'Why we collect it:',
    'Solely to reply to your enquiry and keep a record of the conversation. We do not sell it and we do not use it for advertising.',
    'How long we keep it:',
    'Enquiries stay in our dashboard until they are no longer needed. You can ask us to delete yours at any time.',
    'Analytics:',
    'If analytics are enabled, an anonymised record of the pages you visit is collected. It is never linked to your enquiry.',
    'Your rights:',
    'You can ask what we hold about you, ask for it to be corrected, or ask for it to be deleted. Contact us through the form on the home page.',
    'REPLACE THIS PAGE before launch. It is a starting point written by your developers, not legal advice — have it reviewed against the law that applies to you.']


class Command(BaseCommand):
    help = "Seed the site with the original Jun Technology content."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing repeatable content before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            for model in (
                models.NavLink,
                models.HeroHighlight,
                models.Stat,
                models.AboutCard,
                models.AboutImage,
                models.Service,
                models.ProjectMetric,
                models.ProjectImage,
                models.Project,
                models.ProjectCategory,
                models.BlogPost,
                models.BlogCategory,
                models.Testimonial,
                models.ContactDetail,
                models.FaqItem,
                models.FooterLink,
                models.FooterColumn,
                models.SocialLink,
            ):
                model.objects.all().delete()
            self.stdout.write(self.style.WARNING("Existing content removed."))

        self._singletons()
        self._branding()
        self._nav()
        self._hero_highlights()
        self._stats()
        self._about_images()
        self._about_cards()
        self._services()
        self._portfolio()
        self._blog_categories()
        self._testimonials()
        self._contact_details()
        self._pages()
        self._faqs()
        self._footer()
        self._social()

        self.stdout.write(self.style.SUCCESS("Content seeded."))

    # -- helpers ---------------------------------------------------------- #
    @staticmethod
    def _upsert(model, defaults, **lookup):
        obj, created = model.objects.get_or_create(**lookup, defaults=defaults)
        if not created:
            changed = False
            for field, value in defaults.items():
                if getattr(obj, field) != value:
                    setattr(obj, field, value)
                    changed = True
            if changed:
                obj.save()
        return obj

    # -- sections --------------------------------------------------------- #
    def _singletons(self):
        for model in (
            models.SiteSettings,
            models.HeroSection,
            models.AboutSection,
            models.ServicesSection,
            models.PortfolioSection,
            models.TestimonialsSection,
            models.BlogSection,
            models.FaqSection,
            models.ContactSection,
            models.FooterSettings,
            models.EmailSettings,
        ):
            model.load()

    def _branding(self):
        """Give the site its logo so the Brand screen starts filled in."""
        site = models.SiteSettings.load()
        if site.logo_mark:
            return
        source = settings.BASE_DIR / "static" / "img" / "jun-logo-mark.png"
        if not source.exists():
            self.stdout.write(self.style.WARNING(f"Logo not found at {source}."))
            return
        with source.open("rb") as handle:
            site.logo_mark.save(source.name, File(handle), save=True)
        self.stdout.write("Logo copied into media.")

    def _nav(self):
        items = [
            ("Home", "#home"),
            ("About", "#about"),
            ("Services", "#services"),
            ("Work", "#work"),
            ("Testimonials", "#voices"),
            ("Blog", "/blog/"),
            ("Contact", "#contact"),
        ]
        for index, (label, target) in enumerate(items):
            anchor = target.startswith("#")
            self._upsert(
                models.NavLink,
                {
                    "target": target,
                    "section_key": target[1:] if anchor else "",
                    "order": index,
                },
                label=label,
            )

    def _hero_highlights(self):
        items = [
            ("100+ Projects Delivered", "blue"),
            ("98% Client Satisfaction", "purple"),
            ("Built SEO-first", "sky"),
        ]
        for index, (label, accent) in enumerate(items):
            self._upsert(
                models.HeroHighlight, {"accent": accent, "order": index}, label=label
            )

    def _stats(self):
        items = [
            ("bars", 100, "+", "Projects Delivered", "blue"),
            ("check", 98, "%", "Client Satisfaction", "purple"),
            ("clock", 5, "+", "Years Experience", "sky"),
            ("user", 50, "+", "Happy Clients", "blue"),
        ]
        for index, (icon, value, suffix, label, accent) in enumerate(items):
            self._upsert(
                models.Stat,
                {
                    "icon": icon,
                    "value": value,
                    "suffix": suffix,
                    "accent": accent,
                    "order": index,
                },
                label=label,
            )

    def _about_images(self):
        """
        Adopt the section's single photo into the flip collection.

        The frame flips through AboutImage rows and only falls back to
        AboutSection.image while none exist, so moving the existing photo
        across puts it where an editor will go looking for it. Adding a second
        photo there is all it takes to start the flip.
        """
        if models.AboutImage.objects.exists():
            return
        section = models.AboutSection.load()
        if not section.image:
            return
        models.AboutImage.objects.create(
            image=section.image.name,  # same file, no copy
            alt=section.image_alt,
            order=0,
        )
        self.stdout.write("About photo adopted into About images.")

    def _about_cards(self):
        items = [
            (
                "Our Mission",
                "Empower businesses with cutting-edge digital solutions that "
                "drive measurable growth and lasting online presence.",
                "blue",
            ),
            (
                "Our Vision",
                "To be the most trusted technology partner for ambitious "
                "businesses across the globe, at every stage of scale.",
                "purple",
            ),
            (
                "Why Choose Us",
                "Strategic thinking, beautiful design and technical precision — "
                "websites that don't just look great, they perform.",
                "sky",
            ),
        ]
        for index, (title, body, accent) in enumerate(items):
            self._upsert(
                models.AboutCard,
                {"body": body, "accent": accent, "order": index},
                title=title,
            )

    def _services(self):
        items = [
            (
                "code",
                "Website Development",
                "Modern, fast and scalable websites built with the latest "
                "technologies and best practices.",
            ),
            (
                "browser",
                "UI/UX Design",
                "Beautiful, intuitive interfaces crafted to convert visitors "
                "into loyal customers.",
            ),
            (
                "redesign",
                "Website Redesign",
                "Revamp your existing site with a fresh, modern look that "
                "reflects your brand today.",
            ),
            (
                "cart",
                "E-Commerce Development",
                "Powerful online stores built to drive sales, streamline "
                "operations and delight buyers.",
            ),
            (
                "search",
                "SEO Optimization",
                "Data-driven SEO strategies that lift rankings and bring "
                "qualified organic traffic.",
            ),
            (
                "megaphone",
                "Website Promotion",
                "Digital marketing campaigns that increase visibility and grow "
                "your customer base.",
            ),
            (
                "gear",
                "Maintenance & Support",
                "24/7 monitoring, updates and support to keep your website "
                "secure and performing.",
            ),
            (
                "shield",
                "Custom Web Applications",
                "Bespoke web apps and portals tailored to your unique business "
                "workflows.",
            ),
        ]
        # The four the original design listed in its footer. The rest are
        # available to tick in the dashboard, but a footer column of eight
        # would not match the design.
        footer_four = {
            "Website Development",
            "UI/UX Design",
            "Website Promotion",
            "SEO Optimization",
        }
        for index, (icon, title, description) in enumerate(items):
            self._upsert(
                models.Service,
                {
                    "icon": icon,
                    "description": description,
                    "order": index,
                    "show_in_footer": title in footer_four,
                    # Explicit so the card's "Learn more →" line can never be
                    # lost to a blank value.
                    "link_label": "Learn more",
                },
                title=title,
            )

    def _portfolio(self):
        # `is_featured` marks the projects the hero flip card cycles through.
        # Seeding a few means a fresh install shows the card straight away
        # instead of falling back to the build-health panel. At most
        # models.MAX_HERO_FEATURED may carry the flag.
        categories = [
            "Business",
            "E-Commerce",
            "Healthcare",
            "Education",
            "Restaurant",
        ]
        category_map = {}
        for index, name in enumerate(categories):
            category_map[name] = self._upsert(
                models.ProjectCategory, {"order": index}, name=name
            )

        projects = [
            {
                "title": "CoreLogic CRM",
                "category": "Business",
                "stack": "React · Node.js",
                "short_description": "Enterprise CRM with analytics dashboard and client management.",
                "description": (
                    "A unified CRM for a 400-seat sales organisation: pipeline "
                    "analytics, client records, quoting and role-based dashboards, "
                    "replacing four disconnected internal tools."
                ),
                "metrics": [("+38%", "Sales velocity"), ("4→1", "Tools replaced"), ("11wk", "To launch")],
                "is_featured": True,
            },
            {
                "title": "ShopVault Store",
                "category": "E-Commerce",
                "stack": "Next.js · Stripe",
                "short_description": "Full-featured commerce platform with real-time inventory and payments.",
                "description": (
                    "Headless commerce build with real-time inventory, one-page "
                    "checkout and a merchandising CMS the client's own team runs "
                    "without developers."
                ),
                "metrics": [("2.1x", "Conversion"), ("0.9s", "LCP"), ("+64%", "AOV lift")],
                "is_featured": True,
            },
            {
                "title": "MediConnect",
                "category": "Healthcare",
                "stack": "React · Firebase",
                "short_description": "Appointment scheduling and patient management portal for clinics.",
                "description": (
                    "Patient portal and clinician scheduling system with "
                    "HIPAA-conscious data handling, automated reminders and "
                    "multi-location capacity planning."
                ),
                "metrics": [("−72%", "No-shows"), ("9", "Clinics live"), ("24/7", "Booking")],
                "is_featured": True,
            },
            {
                "title": "LearnSphere LMS",
                "category": "Education",
                "stack": "Vue.js · Django",
                "short_description": "Learning management system with live classes, quizzes and progress tracking.",
                "description": (
                    "Learning platform with live classes, adaptive quizzing and "
                    "progress analytics for faculty — built to hold 5,000 "
                    "concurrent students."
                ),
                "metrics": [("5k", "Concurrent"), ("+41%", "Completion"), ("4.8", "App rating")],
            },
            {
                "title": "TasteBud Online",
                "category": "Restaurant",
                "stack": "React · Supabase",
                "short_description": "Restaurant site with online menu, reservations and order management.",
                "description": (
                    "Reservation and ordering experience for a six-venue "
                    "restaurant group, with live table availability and a "
                    "kitchen-side order display."
                ),
                "metrics": [("+120%", "Direct orders"), ("6", "Venues"), ("18%", "Fee saved")],
            },
            {
                "title": "ProManage Suite",
                "category": "Business",
                "stack": "React · AWS",
                "short_description": "Project management tool with kanban boards, time tracking and team collaboration.",
                "description": (
                    "Project management workspace with kanban boards, time "
                    "tracking and team workload views, deployed as a white-label "
                    "product for agencies."
                ),
                "metrics": [("3.4k", "Daily users"), ("99.9%", "Uptime"), ("−30%", "Admin time")],
            },
        ]

        seeded_featured = sum(1 for p in projects if p.get("is_featured"))
        if seeded_featured > models.MAX_HERO_FEATURED:
            raise CommandError(
                f"Seed marks {seeded_featured} projects as featured but the hero "
                f"card holds {models.MAX_HERO_FEATURED}."
            )

        for index, data in enumerate(projects):
            metrics = data.pop("metrics")
            category = category_map[data.pop("category")]
            project = self._upsert(
                models.Project,
                {**data, "category": category, "order": index},
                title=data["title"],
            )
            for m_index, (value, label) in enumerate(metrics):
                self._upsert(
                    models.ProjectMetric,
                    {"value": value, "order": m_index},
                    project=project,
                    label=label,
                )

    def _blog_categories(self):
        """
        Starter categories so the blog's filters work from day one.

        These are structure, not content — rename or delete them freely. No
        articles are seeded; those are the marketing team's to write.
        """
        for index, name in enumerate(
            ["Insights", "Engineering", "Design", "Company news"]
        ):
            self._upsert(models.BlogCategory, {"order": index}, name=name)

    def _testimonials(self):
        items = [
            (
                "Jun Technology transformed our outdated website into a stunning, "
                "high-converting platform. Sales increased by 40% within the first month.",
                "Sarah Mitchell",
                "Founder, Peak Retail",
                "blue",
            ),
            (
                "Their attention to detail and understanding of our brand was "
                "incredible. The new platform streamlined our patient bookings dramatically.",
                "Raj Patel",
                "Director, Medicare Clinic",
                "purple",
            ),
            (
                "From the first consultation to launch, the process was seamless. "
                "Our LMS has received overwhelmingly positive feedback from students and faculty.",
                "Emma Chen",
                "Lead, EdVantage Academy",
                "sky",
            ),
            (
                "Best investment we made for our business. The e-commerce site is "
                "blazing fast, beautiful, and our conversion rate has doubled.",
                "Marcus Johnson",
                "Owner, Urban Commerce",
                "blue",
            ),
        ]
        for index, (quote, name, role, accent) in enumerate(items):
            self._upsert(
                models.Testimonial,
                {"quote": quote, "author_role": role, "accent": accent, "order": index},
                author_name=name,
            )

    def _contact_details(self):
        items = [
            ("pin", "Office Address", "123 Tech Park, Silicon Avenue, CA 94025", "", "blue"),
            ("phone", "Phone Number", "+1 (555) 123-4567", "tel:+15551234567", "purple"),
            ("mail", "Email Address", "hello@juntechnology.com", "mailto:hello@juntechnology.com", "sky"),
            ("hours", "Business Hours", "Mon – Fri, 9AM – 6PM PST", "", "blue"),
        ]
        for index, (icon, label, value, link, accent) in enumerate(items):
            self._upsert(
                models.ContactDetail,
                {
                    "icon": icon,
                    "value": value,
                    "link": link,
                    "accent": accent,
                    "order": index,
                },
                label=label,
            )

    def _pages(self):
        """Terms and privacy start as editable drafts, clearly marked as such."""
        pages = [
            (
                "terms",
                "Terms & Conditions",
                "The terms you agree to when you use this website or engage us "
                "for work.",
                TERMS_BLOCKS,
            ),
            (
                "privacy",
                "Privacy Policy",
                "What we collect when you use this website, why, and what you "
                "can ask us to do about it.",
                PRIVACY_BLOCKS,
            ),
        ]
        for slug, title, intro, blocks in pages:
            self._upsert(
                models.ContentPage,
                {"title": title, "intro": intro, "body": "\n\n".join(blocks)},
                slug=slug,
            )

    def _faqs(self):
        items = [
            (
                "How long does a website take?",
                "A marketing site is usually three to six weeks from the "
                "kick-off workshop to launch. The single biggest factor is how "
                "quickly the copy and images arrive, which is why we agree an "
                "owner for each page on day one.",
            ),
            (
                "What does it cost?",
                "We quote a fixed price against a fixed scope, so there are no "
                "hourly surprises. Send us an enquiry describing what you need "
                "and we will come back with a proposal and a number.",
            ),
            (
                "Do you write the content?",
                "We can. Most clients supply their own words and we edit them "
                "for the web; if you would rather we wrote them, we quote for "
                "that separately.",
            ),
            (
                "Can we edit the site ourselves afterwards?",
                "Yes \u2014 that is the point of the dashboard. Every word, number "
                "and image on the site can be changed without a developer, and "
                "we walk your team through it before launch.",
            ),
            (
                "Do you offer support after launch?",
                "Yes. We offer a monthly plan covering updates, backups, "
                "security patches and a set number of content changes. It is "
                "optional and you can cancel it at any time.",
            ),
            (
                "Will the site work on mobile?",
                "Every page is built and tested on phones first. We also test "
                "on tablets and on the browsers your visitors actually use.",
            ),
            (
                "Do you help with SEO?",
                "The build is SEO-first: fast pages, clean markup, proper "
                "headings, sitemaps and metadata you control. Ongoing keyword "
                "and content work is a separate service.",
            ),
            (
                "Who owns the site when it is finished?",
                "You do. Code, design and content transfer to you on final "
                "payment, and we hand over every account and credential.",
            ),
        ]
        for index, (question, answer) in enumerate(items):
            self._upsert(
                models.FaqItem, {"answer": answer, "order": index}, question=question
            )

    def _footer(self):
        columns = [
            (
                "Company",
                [
                    ("About Us", "#about"),
                    ("Services", "#services"),
                    ("Portfolio", "#work"),
                    ("Careers", "#contact"),
                ],
            ),
            ("Services", []),
            (
                "Resources",
                [
                    ("Blog", "/blog/"),
                    ("FAQs", "/faq/"),
                    ("Privacy Policy", "/privacy/"),
                    ("Terms & Conditions", "/terms/"),
                ],
            ),
        ]
        for index, (title, links) in enumerate(columns):
            # The services column fills itself from the services ticked
            # "Feature in footer", so it carries no manual links.
            source = "services" if title == "Services" else "links"
            column = self._upsert(
                models.FooterColumn, {"order": index, "source": source}, title=title
            )
            if source == "services":
                column.links.all().delete()
                continue
            for l_index, (label, url) in enumerate(links):
                self._upsert(
                    models.FooterLink,
                    {"url": url, "order": l_index},
                    column=column,
                    label=label,
                )

    def _social(self):
        items = [
            ("linkedin", "LinkedIn", "#contact", "blue"),
            ("x", "X", "#contact", "purple"),
            ("github", "GitHub", "#contact", "sky"),
            ("dribbble", "Dribbble", "#contact", "blue"),
        ]
        for index, (icon, label, url, accent) in enumerate(items):
            self._upsert(
                models.SocialLink,
                {"icon": icon, "url": url, "accent": accent, "order": index},
                label=label,
            )
