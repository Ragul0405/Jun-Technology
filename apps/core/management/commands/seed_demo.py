"""
Bulk demo content, for trying the site out with realistic volume.

Deliberately separate from `seed_content`, which loads the real copy of the
original design. This command only ever touches rows whose titles are in the
catalogues below, so `--clear` can take every one of them back out again
without risking anything the client has written.

    python manage.py seed_demo             # 24 projects + 24 posts
    python manage.py seed_demo --projects 40 --posts 40
    python manage.py seed_demo --clear     # remove them all again
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.core import models

# (title, category, stack, short description, [(metric value, label), ...])
PROJECTS = [
    ("Northwind Freight Portal", "Business", "React · Node.js",
     "Shipment tracking and rate quoting for a 200-truck freight operator.",
     [("−41%", "Quote time"), ("18k", "Shipments/mo"), ("6wk", "To launch")]),
    ("Kettle & Co Storefront", "E-Commerce", "Next.js · Stripe",
     "Speciality coffee shop with subscriptions and a roast calendar.",
     [("3.1x", "Repeat orders"), ("0.8s", "LCP"), ("+52%", "AOV")]),
    ("Brightpath Clinics", "Healthcare", "React · Firebase",
     "Multi-site clinic booking with automated reminders and triage forms.",
     [("−63%", "No-shows"), ("14", "Sites live"), ("4.9", "Patient rating")]),
    ("Atlas Study Hub", "Education", "Vue.js · Django",
     "Course delivery with live cohorts, assignments and progress reporting.",
     [("7k", "Learners"), ("+38%", "Completion"), ("99.9%", "Uptime")]),
    ("Saffron House", "Restaurant", "React · Supabase",
     "Table booking and pre-ordering for a five-venue restaurant group.",
     [("+96%", "Direct bookings"), ("5", "Venues"), ("22%", "Fees saved")]),
    ("Meridian Wealth", "Business", "Next.js · PostgreSQL",
     "Client portal with document vaults, e-signing and portfolio summaries.",
     [("2.4k", "Clients"), ("−70%", "Paperwork"), ("SOC 2", "Audited")]),
    ("Loomcraft Textiles", "E-Commerce", "Shopify · Hydrogen",
     "Made-to-order fabric shop with a live swatch configurator.",
     [("+2.8x", "Conversion"), ("11k", "SKUs"), ("1.1s", "LCP")]),
    ("Vitals Remote", "Healthcare", "React Native · Django",
     "At-home monitoring app feeding a clinician dashboard.",
     [("30k", "Readings/day"), ("−48%", "Readmissions"), ("HIPAA", "Aligned")]),
    ("Cadence Music School", "Education", "Vue.js · Node.js",
     "Lesson scheduling, practice logs and parent reporting in one place.",
     [("1.8k", "Students"), ("+44%", "Retention"), ("4.8", "App rating")]),
    ("Harbour & Vine", "Restaurant", "Astro · Sanity",
     "Waterfront restaurant site with seasonal menus and private hire.",
     [("+120%", "Enquiries"), ("0.6s", "LCP"), ("A+", "Vitals")]),
    ("Ironclad Insurance", "Business", "React · .NET",
     "Quote-and-bind journey replacing a 40-page paper application.",
     [("9min", "To quote"), ("−55%", "Drop-off"), ("3", "Products")]),
    ("Peak Outfitters", "E-Commerce", "Next.js · Medusa",
     "Outdoor gear retailer with in-store stock lookup and click-and-collect.",
     [("+67%", "Collect orders"), ("24", "Stores"), ("1.0s", "LCP")]),
    ("Willow Dental", "Healthcare", "Astro · Django",
     "Practice site with online registration and treatment plan viewing.",
     [("+81%", "Online regs"), ("6", "Practices"), ("4.9", "Reviews")]),
    ("Lumen Academy", "Education", "React · FastAPI",
     "Corporate training platform with skills mapping and certification.",
     [("120", "Employers"), ("31k", "Certificates"), ("+29%", "Pass rate")]),
    ("The Copper Pot", "Restaurant", "Next.js · Stripe",
     "Neighbourhood bistro with online ordering and a loyalty scheme.",
     [("+58%", "Repeat visits"), ("2", "Venues"), ("18%", "Fees saved")]),
    ("Fairline Property", "Business", "Vue.js · Django",
     "Lettings portal with viewings, referencing and tenancy paperwork.",
     [("4.2k", "Listings"), ("−62%", "Admin hours"), ("11", "Branches")]),
    ("Bloom Botanicals", "E-Commerce", "Shopify · Remix",
     "Plant retailer with care guides and a delivery-window picker.",
     [("+2.1x", "Conversion"), ("−34%", "Returns"), ("0.9s", "LCP")]),
    ("Caldera Physio", "Healthcare", "React · Node.js",
     "Rehab programme builder with video exercises and adherence tracking.",
     [("+73%", "Adherence"), ("8", "Clinics"), ("4.7", "Rating")]),
    ("Orbit Coding Club", "Education", "Svelte · Django",
     "After-school coding platform with projects, badges and parent updates.",
     [("3.6k", "Members"), ("+51%", "Weekly active"), ("40", "Schools")]),
    ("Nona's Kitchen", "Restaurant", "Astro · Supabase",
     "Family trattoria with events, catering enquiries and a gift-card shop.",
     [("+88%", "Catering leads"), ("1", "Venue"), ("A+", "Vitals")]),
    ("Sterling Legal", "Business", "Next.js · PostgreSQL",
     "Matter intake and secure client messaging for a commercial practice.",
     [("−45%", "Intake time"), ("1.2k", "Matters"), ("ISO", "Certified")]),
    ("Tidepool Surf", "E-Commerce", "Next.js · Stripe",
     "Surf shop with board finder, hire bookings and lesson scheduling.",
     [("+134%", "Hire bookings"), ("5", "Beaches"), ("1.1s", "LCP")]),
    ("Grove Veterinary", "Healthcare", "React · Firebase",
     "Pet records, repeat prescriptions and appointment booking.",
     [("+69%", "Online bookings"), ("12k", "Pets"), ("4.9", "Rating")]),
    ("Beacon Language", "Education", "Vue.js · Node.js",
     "Language school with placement tests, live classes and progress reports.",
     [("2.9k", "Learners"), ("+36%", "Renewals"), ("22", "Tutors")]),
]

# (title, category, excerpt, [paragraph, ...])
POSTS = [
    ("What clients actually ask for in a first call", "Insights",
     "Six months of discovery calls, and the three questions that come up every single time.",
     ["Almost every first conversation lands on the same three worries: how long it takes, who writes the words, and what happens after launch.",
      "The timeline question is really a question about certainty. We answer it by fixing the scope, not the hours.",
      "The words are the hard part. A site without copy is a design exercise, so we agree the owner of every page before anything is designed."]),
    ("Why we still render on the server", "Engineering",
     "A short case for boring, fast pages, and the trade-offs we accept to get them.",
     ["A marketing site's job is to load quickly on a mid-range phone on a bad connection. Very little else matters.",
      "Server rendering gets us there with less machinery: no hydration cost, no waterfall of client requests, no framework to keep current.",
      "We give up some interactivity. For a site whose busiest interaction is a contact form, that is a bargain."]),
    ("Designing in the browser", "Design",
     "The prototype is the spec. Here is what that changes about how we work.",
     ["A static mock is a picture of a website. It cannot show a hover, a loading state, or what happens at 380 pixels wide.",
      "Designing in the browser removes the translation step, and with it the argument about whether the build matches the design.",
      "It also front-loads the awkward questions. Long titles, missing images and empty states show up on day two instead of week six."]),
    ("How we scope a project in one workshop", "Insights",
     "Two hours, a whiteboard and a list of pages nobody is allowed to add to.",
     ["Scope creep is rarely dramatic. It is one more page, one more field, one more integration.",
      "We spend the first session listing every page and naming an owner for each, then agree that anything new displaces something else.",
      "It sounds rigid. In practice it is the reason projects land on the date we promised."]),
    ("Image formats, measured", "Engineering",
     "What actually moved the needle when we audited image delivery across ten client sites.",
     ["Modern formats helped, but not as much as simply not shipping a 4000-pixel-wide hero to a phone.",
      "The biggest single win was setting explicit dimensions, which removed layout shift entirely.",
      "Lazy loading below the fold came third, and only mattered on long pages."]),
    ("Type scales that survive real content", "Design",
     "Choosing sizes that still work when the headline is four words longer than the mock.",
     ["Every type scale looks good with placeholder text. The test is a real headline written by someone who was not thinking about your grid.",
      "We clamp headline sizes to a viewport range rather than picking fixed breakpoint values.",
      "And we always design the longest plausible title, not the shortest."]),
    ("Handing a site over without a handover document", "Company news",
     "If the dashboard needs a manual, the dashboard is wrong.",
     ["We used to ship a PDF explaining which field controlled what. Nobody read it.",
      "Now every field carries its own help text, and every screen says what happens when you save.",
      "The measure of success is a client changing something on launch day without emailing us."]),
    ("The case against carousels, revisited", "Design",
     "We rebuilt one anyway. Here is when it earns its place.",
     ["The research against carousels is about hero sliders that hide content behind a timer.",
      "A gallery a visitor controls is a different thing, and it tests well.",
      "The rule we settled on: never put something a visitor needs behind an animation they did not start."]),
    ("Migrating a site without losing rankings", "Engineering",
     "A checklist we run before, during and after every launch.",
     ["Redirects are the whole game. Every old URL needs a home, and a spreadsheet is the only way to be sure.",
      "We crawl the old site, map every path, then test the redirect map against that crawl before switching DNS.",
      "Afterwards we watch coverage reports daily for a fortnight, not once at the end of the month."]),
    ("What a good brief looks like", "Insights",
     "The three pages of information that make everything after them faster.",
     ["A good brief names the audience, the one action you want them to take, and the thing you do that competitors do not.",
      "Everything else — colours, references, favourite sites — is useful but secondary.",
      "When a brief is missing those three, the first workshop is about writing them."]),
    ("Accessibility is mostly not a plugin", "Engineering",
     "The fixes that actually help, and the widgets that do not.",
     ["Overlay widgets promise compliance in one line of JavaScript. They do not deliver it.",
      "Real progress came from semantic markup, keyboard focus states and colour contrast — none of which are glamorous.",
      "We test with the keyboard first. If a page cannot be used without a mouse, nothing else counts."]),
    ("Working with a marketing team, not around one", "Company news",
     "Why the blog is the first thing we build, not the last.",
     ["A blog added at the end is a blog nobody uses. It arrives after the launch rush, with no workflow around it.",
      "Building it early means the team publishes during the project and finds the rough edges while we can still fix them.",
      "By launch, publishing is a habit rather than a new tool."]),
    ("Dark mode without doubling the work", "Design",
     "Custom properties, one palette, and the traps we hit anyway.",
     ["Two themes are not two designs. They are one design with two sets of values.",
      "Everything that resolves to a colour goes through a custom property, including shadows and gradients.",
      "The trap is imagery. A screenshot with a white background undoes the whole effect."]),
    ("Measuring a marketing site properly", "Insights",
     "Vanity metrics, useful metrics, and the one number we report every month.",
     ["Sessions go up when a newsletter goes out. That tells you about the newsletter.",
      "We report qualified enquiries, because that is the thing the site is for.",
      "Everything else is diagnostic: useful when the number moves, meaningless on its own."]),
    ("Forms that people finish", "Design",
     "Field order, error copy and the surprising cost of one extra question.",
     ["Every field you add costs completions. The phone number field is usually the most expensive.",
      "Errors belong next to the field, in words describing what to do rather than what went wrong.",
      "And the button should say what happens, not 'Submit'."]),
    ("Our deployment checklist", "Engineering",
     "Eleven things we check before a site goes live, in order.",
     ["Most launch problems are not code. They are a missing environment variable or a DNS record with a long TTL.",
      "The checklist starts with backups and ends with a real submission through the contact form.",
      "Anything that has bitten us once gets added to it permanently."]),
    ("When to say no to a feature", "Insights",
     "Three questions we ask before agreeing to build something.",
     ["Who maintains it? Most feature requests are cheap to build and expensive to keep.",
      "What happens if it is empty? Features that look broken without content usually stay broken.",
      "What does it displace? Time is the only genuinely fixed resource."]),
    ("Naming things for the people who edit them", "Design",
     "Why our field labels do not match our database columns.",
     ["'Hero panel metric 2 label' means something to a developer and nothing to anyone else.",
      "Labels should describe what a visitor will see, in the words the client already uses.",
      "It costs nothing and removes an entire category of support email."]),
    ("A year of Core Web Vitals", "Engineering",
     "What changed, what did not, and where the remaining points hide.",
     ["Layout shift was the easiest to fix and the most commonly ignored.",
      "Interaction latency is the one that catches modern sites, usually from third-party scripts.",
      "The remaining points are almost always in something someone else's tag manager loaded."]),
    ("How we price fixed-scope work", "Company news",
     "Transparency about the thing agencies are usually least transparent about.",
     ["We price the scope, not the hours, because the client is buying an outcome.",
      "That only works if the scope is genuinely fixed, which is why the workshop matters so much.",
      "Changes are quoted as changes. No surprises in either direction."]),
    ("The content freeze that saves a launch", "Insights",
     "Two weeks before go-live, the copy stops moving.",
     ["Late copy changes are the single most common cause of a slipped launch date.",
      "A freeze is not about control. It is about giving proofreading and testing a stable target.",
      "Anything after the freeze goes live the week after launch, from the dashboard, by the client."]),
    ("Component libraries for sites, not apps", "Engineering",
     "Why we keep ours deliberately small.",
     ["A marketing site needs maybe fifteen components. A library of ninety is a liability.",
      "Small libraries stay consistent because there is only one way to do each thing.",
      "When we need a ninety-component library, we are usually building an application instead."]),
    ("What we learned from rebuilding our own site", "Company news",
     "Doing to ourselves what we do to clients, and finding the same problems.",
     ["We had no content owner, so the copy was late. We had no scope, so it grew.",
      "The fix was the same process we sell, applied to ourselves.",
      "It shipped three weeks after we started treating it like a client project."]),
    ("Motion that earns its keep", "Design",
     "Animation as an explanation, not decoration.",
     ["Motion is useful when it tells you where something came from or where it went.",
      "It is noise when it fires on scroll for its own sake.",
      "We keep durations short and give everything a reason to move."]),
]

DEMO_BODY_TAIL = (
    "\n\nThis is demo content, generated by `python manage.py seed_demo`. "
    "Remove every demo row again with `python manage.py seed_demo --clear`."
)


class Command(BaseCommand):
    help = "Create (or remove) bulk demo projects and blog posts."

    def add_arguments(self, parser):
        parser.add_argument("--projects", type=int, default=24)
        parser.add_argument("--posts", type=int, default=24)
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete the demo rows instead of creating them.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            return self._clear()

        self._projects(options["projects"])
        self._posts(options["posts"])
        self.stdout.write(
            self.style.SUCCESS(
                "Demo content ready. Remove it with "
                "`python manage.py seed_demo --clear`."
            )
        )

    # -- create ----------------------------------------------------------- #
    def _projects(self, wanted):
        catalogue = PROJECTS[: max(0, wanted)]
        if not catalogue:
            return
        start = models.Project.objects.count()
        made = 0
        for index, (title, category, stack, blurb, metrics) in enumerate(catalogue):
            if models.Project.objects.filter(title=title).exists():
                continue
            project = models.Project.objects.create(
                title=title,
                category=models.ProjectCategory.objects.get_or_create(
                    name=category, defaults={"order": 99}
                )[0],
                stack=stack,
                short_description=blurb,
                description=f"{blurb}{DEMO_BODY_TAIL}",
                order=start + index,
            )
            for position, (value, label) in enumerate(metrics):
                models.ProjectMetric.objects.create(
                    project=project, value=value, label=label, order=position
                )
            made += 1
        self.stdout.write(f"Projects added: {made} (total {models.Project.objects.count()}).")

    def _posts(self, wanted):
        catalogue = POSTS[: max(0, wanted)]
        if not catalogue:
            return
        today = timezone.localdate()
        made = 0
        for index, (title, category, excerpt, paragraphs) in enumerate(catalogue):
            if models.BlogPost.objects.filter(title=title).exists():
                continue
            models.BlogPost.objects.create(
                title=title,
                category=models.BlogCategory.objects.get_or_create(
                    name=category, defaults={"order": 99}
                )[0],
                excerpt=excerpt,
                body="\n\n".join(paragraphs) + DEMO_BODY_TAIL,
                published_at=today - timedelta(days=index * 3),
            )
            made += 1
        self.stdout.write(f"Posts added: {made} (total {models.BlogPost.objects.count()}).")

    # -- remove ----------------------------------------------------------- #
    def _clear(self):
        posts = models.BlogPost.objects.filter(title__in=[p[0] for p in POSTS])
        removed_posts = posts.count()
        posts.delete()

        projects = models.Project.objects.filter(title__in=[p[0] for p in PROJECTS])
        removed_projects = projects.count()
        for project in projects:
            project.metrics.all().delete()
            project.gallery.all().delete()
        projects.delete()

        self.stdout.write(
            self.style.WARNING(
                f"Demo content removed: {removed_projects} projects, "
                f"{removed_posts} posts. Nothing else was touched."
            )
        )
