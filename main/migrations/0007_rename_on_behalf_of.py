# Generated by Django 2.2.16 on 2020-09-10 11:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0006_auto_20200910_0738"),
    ]

    operations = [
        migrations.RenameField("Booking", "on_behalf_of", "on_behalf_of_name"),
    ]
