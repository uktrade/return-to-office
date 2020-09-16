# Generated by Django 3.1.1 on 2020-09-17 09:09

from django.db import migrations, models
import main.models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0009_auto_20200914_1502"),
    ]

    operations = [
        migrations.CreateModel(
            name="DitGroup",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=80, unique=True)),
                (
                    "business_units",
                    models.TextField(
                        help_text="One business unit per line",
                        validators=[main.models.validate_business_units],
                    ),
                ),
            ],
            options={
                "verbose_name": "DIT Group",
                "verbose_name_plural": "DIT Groups",
            },
        ),
        migrations.AddField(
            model_name="booking",
            name="business_unit",
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="group",
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
    ]
