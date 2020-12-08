from django.db import models
from django.utils.translation import ugettext_lazy as _

from .abstractModel import AbstractUser


class User(AbstractUser):
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        error_messages={
            "unique": _("A user with that username already exists."),
        },
        null=True,
    )

    contact_email = models.CharField(
        _("contact_email"),
        max_length=255,
        blank=True,
    )

    USERNAME_FIELD = "username"

    def __str__(self):
        return f"User(username={self.username}, email={self.email}, contact_email={self.contact_email})"

    def __repr__(self):
        return str(self)

    def full_name(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.email

    def get_contact_email(self):
        return self.contact_email or self.email

    @staticmethod
    def get_by_email(email):
        """Get existing user by email address, or None if not found.

        Looks up by contact_email first, then email.
        """

        return (
            User.objects.filter(contact_email=email).first()
            or User.objects.filter(email=email).first()
            or None
        )
