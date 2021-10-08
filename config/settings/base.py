"""
Django settings for fido project.

Generated by 'django-admin startproject' using Django 2.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""
import os
import environ

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

env = environ.Env()
env.read_env()

DEBUG = env.bool("DEBUG", default=False)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

VCAP_SERVICES = env.json("VCAP_SERVICES", {})

INSTALLED_APPS = [
    "main",
    "custom_usermodel",
    "authbroker_client",
    "pingdom.apps.PingdomConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_audit_log_middleware",
    # "dal",
    # "dal_select2",
    "sass_processor",
    "axes",
    # must be last so other apps can override widget rendering
    "django.forms",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django_settings_export.settings_export",
            ]
        },
    }
]

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

WSGI_APPLICATION = "config.wsgi.application"

if env("ELASTIC_APM_ENVIRONMENT", default=None):
    ELASTIC_APM = {
        "SERVICE_NAME": "return-to-office",
        "SECRET_TOKEN": env.bool("ELASTIC_APM_SECRET_TOKEN", default=None),
        "SERVER_URL": "https://apm.elk.uktrade.digital",
        "ENVIRONMENT": env("ELASTIC_APM_ENVIRONMENT", default=None),
    }

VCAP_SERVICES = env.json("VCAP_SERVICES", default={})

if "postgres" in VCAP_SERVICES:
    DATABASE_URL = VCAP_SERVICES["postgres"][0]["credentials"]["uri"]
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

DATABASES = {"default": env.db()}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},  # noqa
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/
LANGUAGE_CODE = "en-gb"  # must be gb for date entry to work
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Remove extra details in the label
# for the filter fields, it does
# not says 'contains' or similar
# def FILTERS_VERBOSE_LOOKUPS():
#     from django_filters.conf import DEFAULTS

#     verbose_lookups = DEFAULTS["VERBOSE_LOOKUPS"].copy()
#     verbose_lookups.update({
#             "icontains": "",
#             "contains": "",
#             "startswith": "",
#             "istartswith": ""
#         }
#     )
#     return verbose_lookups


AUTH_USER_MODEL = "custom_usermodel.User"
AUTHBROKER_URL = env("AUTHBROKER_URL", default=None)
AUTHBROKER_CLIENT_ID = env("AUTHBROKER_CLIENT_ID", default=None)
AUTHBROKER_CLIENT_SECRET = env("AUTHBROKER_CLIENT_SECRET", default=None)
AUTHBROKER_SCOPES = "read write"

LOGIN_URL = "/auth/login"
LOGIN_REDIRECT_URL = "main:index"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "sass_processor.finders.CssFinder",
]

SETTINGS_EXPORT = [
    "DEBUG",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
    "main.middleware.IpRestrictionMiddleware",
    "authbroker_client.middleware.ProtectAllViewsMiddleware",
    "django_audit_log_middleware.AuditLogMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    # "guardian.backends.ObjectPermissionBackend",
    "axes.backends.AxesBackend",
]

AXES_LOGIN_FAILURE_LIMIT = 5

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# we need to store dates in the session, which the default json serializer
# doesn't support
SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"

AUTHBROKER_ANONYMOUS_PATHS = [
    "/pingdom/ping.xml",
    "/activity-stream/bookings",
    "/activity-stream/pras",
]

GOVUK_NOTIFY_API_KEY = env("GOVUK_NOTIFY_API_KEY")

# IP filtering
IP_RESTRICT = env.bool("IP_RESTRICT", default=True)
IP_RESTRICT_APPS = ["admin"]
ALLOWED_IPS = env.list("ALLOWED_IPS", default=[])
ALLOWED_IP_RANGES = env.list("ALLOWED_IP_RANGES", default=[])
IP_SAFELIST_XFF_INDEX = env.int("IP_SAFELIST_XFF_INDEX", default=-3)

ACTIVITY_STREAM_ITEMS_PER_PAGE = 50
ACTIVITY_STREAM_HAWK_CREDENTIALS = {
    "id": env("ACTIVITY_STREAM_HAWK_ID"),
    "key": env("ACTIVITY_STREAM_HAWK_SECRET"),
    "algorithm": "sha256",
}

# whether to allow the "staff member" and "SCS" fields in the PRA form be the same
PRA_ALLOW_STAFF_MEMBER_TO_BE_SCS = False
