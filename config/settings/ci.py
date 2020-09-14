import os
import sys

from .base import *  # noqa


AUTHENTICATION_BACKENDS += [
    "custom_usermodel.backends.CustomAuthbrokerBackend",
]

STATICFILES_DIRS = (os.path.join(BASE_DIR, "node_modules/govuk-frontend"),)

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
