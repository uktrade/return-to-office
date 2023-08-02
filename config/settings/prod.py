import os
import sys

from .base import *  # noqa
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from django_log_formatter_ecs import ECSFormatter

AUTHENTICATION_BACKENDS += [
    "custom_usermodel.backends.CustomAuthbrokerBackend",
]

# INSTALLED_APPS += [  # noqa F405
#     "elasticapm.contrib.django",
# ]

# ELASTIC_APM = {
#     "SERVICE_NAME": "Return to Office",
#     "SECRET_TOKEN": env("ELASTIC_APM_SECRET_TOKEN"),  # noqa F405
#     "SERVER_URL": env("ELASTIC_APM_SERVER_URL"),  # noqa F405
#     "ENVIRONMENT": env("APP_ENV"),  # noqa F405
#     "SERVER_TIMEOUT": env("ELASTIC_APM_SERVER_TIMEOUT", default="20s"),  # noqa F405
# }

STATICFILES_DIRS = (os.path.join(BASE_DIR, "node_modules/govuk-frontend"),)

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_MANIFEST_STRICT = False

# X_ROBOTS_TAG (https://man.uktrade.io/docs/procedures/1st-go-live.html)
X_ROBOTS_TAG = [
    "noindex",
    "nofollow",
]

# TODO: needed?
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': CELERY_BROKER_URL,
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         },
#         'KEY_PREFIX': 'cache_'
#     }
# }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "ecs_formatter": {
            "()": ECSFormatter,
        },
        "simple": {
            "format": "{asctime} {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "ecs": {
            "class": "logging.StreamHandler",
            "formatter": "ecs_formatter",
        },
        "simple": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": [
            "ecs",
            "simple",
        ],
        "level": os.getenv("ROOT_LOG_LEVEL", "INFO"),  # noqa F405
    },
    "loggers": {
        "django": {
            "handlers": [
                "ecs",
                "simple",
            ],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),  # noqa F405
            "propagate": False,
        },
        "django.server": {
            "handlers": [
                "ecs",
                "simple",
            ],
            "level": os.getenv("DJANGO_SERVER_LOG_LEVEL", "ERROR"),  # noqa F405
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": [
                "ecs",
                "simple",
            ],
            "level": os.getenv("DJANGO_DB_LOG_LEVEL", "ERROR"),  # noqa F405
            "propagate": False,
        },
    },
}

sentry_sdk.init(
    os.environ.get("SENTRY_DSN"),
    environment=os.environ.get("SENTRY_ENVIRONMENT"),
    integrations=[DjangoIntegration()],
)

# HSTS (https://man.uktrade.io/docs/procedures/1st-go-live.html)
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# ## IHTC compliance

# Set crsf cookie to be secure
CSRF_COOKIE_SECURE = True

# Set session cookie to be secure
SESSION_COOKIE_SECURE = True

# Make browser end session when user closes browser
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Set cookie expiry to 4 hours
SESSION_COOKIE_AGE = 4 * 60 * 60  # 4 hours in seconds

# Prevent client side JS from accessing CRSF token
CSRF_COOKIE_HTTPONLY = True

# Prevent client side JS from accessing session cookie (true by default)
SESSION_COOKIE_HTTPONLY = True

# Set content to no sniff
SECURE_CONTENT_TYPE_NOSNIFF = True

#  Set anti XSS header
SECURE_BROWSER_XSS_FILTER = True
