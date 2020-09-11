import os
import sys
import requests
import logging
from .base import *  # noqa

from django_log_formatter_ecs import ECSFormatter

STATICFILES_DIRS = (os.path.join(BASE_DIR, "node_modules/govuk-frontend"),)

SASS_PROCESSOR_INCLUDE_DIRS = [os.path.join("/node_modules")]

AUTHENTICATION_BACKENDS += [
    "main.backends.CustomAuthbrokerBackend",
]
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
        },
    },
    "root": {
        "handlers": ["stdout"],
        "level": os.getenv("ROOT_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": [
                "stdout",
            ],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": True,
        },
    },
}

# disable ip restriction for local dev
IP_RESTRICT = False
