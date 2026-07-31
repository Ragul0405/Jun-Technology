"""Drop the “What We Offer” label above the services heading."""

from django.db import migrations

OLD_DEFAULT = "What We Offer"


def clear_eyebrow(apps, schema_editor):
    ServicesSection = apps.get_model("core", "ServicesSection")
    # Only clear the old default, so a deliberately customised label survives.
    ServicesSection.objects.filter(eyebrow=OLD_DEFAULT).update(eyebrow="")


def restore_eyebrow(apps, schema_editor):
    ServicesSection = apps.get_model("core", "ServicesSection")
    ServicesSection.objects.filter(eyebrow="").update(eyebrow=OLD_DEFAULT)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_emailsettings_contactsection_map_address_and_more"),
    ]

    operations = [migrations.RunPython(clear_eyebrow, restore_eyebrow)]
