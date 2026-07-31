"""
Populate the database with the content of the original static design.

Running it twice is safe: singletons are updated in place and repeatable rows
are matched on a natural key, so no duplicates are created. Pass --reset to
wipe the repeatable rows first.
"""

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core import models


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
                models.Service,
                models.ProjectMetric,
                models.ProjectImage,
                models.Project,
                models.ProjectCategory,
                models.Testimonial,
                models.ContactDetail,
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
        self._about_cards()
        self._services()
        self._portfolio()
        self._testimonials()
        self._contact_details()
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
            ("Contact", "#contact"),
        ]
        for index, (label, target) in enumerate(items):
            self._upsert(
                models.NavLink,
                {"target": target, "section_key": target.lstrip("#"), "order": index},
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
        for index, (icon, title, description) in enumerate(items):
            self._upsert(
                models.Service,
                {
                    "icon": icon,
                    "description": description,
                    "order": index,
                    # Explicit so the card's "Learn more →" line can never be
                    # lost to a blank value.
                    "link_label": "Learn more",
                },
                title=title,
            )

    def _portfolio(self):
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
            (
                "Services",
                [
                    ("Website Development", "#services"),
                    ("UI/UX Design", "#services"),
                    ("Website Promotion", "#services"),
                    ("SEO Optimization", "#services"),
                ],
            ),
            (
                "Resources",
                [
                    ("Blog", "#voices"),
                    ("FAQs", "#contact"),
                    ("Privacy Policy", "#contact"),
                    ("Terms & Conditions", "#contact"),
                ],
            ),
        ]
        for index, (title, links) in enumerate(columns):
            column = self._upsert(models.FooterColumn, {"order": index}, title=title)
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
