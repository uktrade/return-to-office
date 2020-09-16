from django.db import migrations


def add_dummy_data(apps, schema_editor):
    DitGroup = apps.get_model("main", "DitGroup")

    DitGroup.objects.create(
        name="TRID",
        business_units="\n".join(
            [
                "Chief Investigators",
                "Communications",
                "Corporate and Commercial",
                "Economics Unit",
                "Finance and Operations",
                "Human Resources",
                "Legal",
                "Operational Policy",
                "Performance, Planning and Risk",
                "Technical Advice",
                "Trade Remedies Authority",
            ]
        ),
    )

    DitGroup.objects.create(
        name="Communications and Marketing",
        business_units="\n".join(
            [
                "Central Communication and Marketing",
                "Content and Digital",
                "Events",
                "Marketing Campaigns",
                "Media Group",
                "Strategic Planning, Insight & Corporate",
            ]
        ),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0010_add_ditgroup"),
    ]

    operations = [
        migrations.RunPython(add_dummy_data),
    ]
