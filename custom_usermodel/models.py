from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .abstractModel import AbstractUser
from .managers import UserManager


class User(AbstractUser):
    contact_email = models.CharField(
        _('contact_email'),
        max_length=255,
        blank=True,
    )

    def get_contact_email(self):
        return self.contact_email or self.email
