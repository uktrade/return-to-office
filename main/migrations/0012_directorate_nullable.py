# Generated by Django 3.1.1 on 2020-09-17 12:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0011_dummy_ditgroup"),
    ]

    operations = [
        migrations.AlterField(
            model_name="booking",
            name="directorate",
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
    ]