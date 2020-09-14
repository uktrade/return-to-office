# Generated by Django 2.2.16 on 2020-09-14 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0008_booking_on_behalf_of_dit_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="canceled_timestamp",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
