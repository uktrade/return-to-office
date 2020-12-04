# Generated by Django 3.1.4 on 2020-12-04 15:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("custom_usermodel", "0002_user_contact_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="username",
            field=models.CharField(
                error_messages={"unique": "A user with that username already exists."},
                max_length=150,
                null=True,
                unique=True,
                verbose_name="username",
            ),
        ),
    ]
