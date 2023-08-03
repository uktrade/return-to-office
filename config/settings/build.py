"""
Minimum base settings required to build an OCI image when compiling statics during build phase.
manage.py compilestatic --settings=config.settings.build
"""
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

SECRET_KEY = "dont-use-in-prod"

ALLOWED_HOSTS = "*"

INSTALLED_APPS = [
    "main",
    "custom_usermodel",
    #"pingdom.apps.PingdomConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    #"django_audit_log_middleware",
    "sass_processor",
    #"django.forms",
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
                #"django_settings_export.settings_export",
            ]
        },
    }
]

#FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR + '/' + 'db.sqlite3',
        }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"}, 
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# USE_I18N = True
# LANGUAGE_CODE = "en-gb"  
# TIME_ZONE = "UTC"
# USE_L10N = True
# USE_TZ = True

AUTH_USER_MODEL = "custom_usermodel.User"
AUTHBROKER_URL = "dont-use-in-prod"

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "sass_processor.finders.CssFinder",
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
    #"axes.middleware.AxesMiddleware",

    #"django_audit_log_middleware.AuditLogMiddleware",
]

# AUTHENTICATION_BACKENDS = [
#     "django.contrib.auth.backends.ModelBackend",
#     "guardian.backends.ObjectPermissionBackend",

# ]
# AUTHENTICATION_BACKENDS += [
#     "custom_usermodel.backends.CustomAuthbrokerBackend",
# ]
