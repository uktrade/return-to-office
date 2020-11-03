from django.db import models
from django.utils.translation import ugettext_lazy as _

from .abstractModel import AbstractUser


class User(AbstractUser):
    contact_email = models.CharField(
        _("contact_email"),
        max_length=255,
        blank=True,
    )

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

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
