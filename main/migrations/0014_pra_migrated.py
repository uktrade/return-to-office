# Generated by Django 3.1.3 on 2020-11-18 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0013_pra"),
    ]

    operations = [
        migrations.AddField(
            model_name="pra",
            name="migrated",
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]