import os
from pathlib import Path

from dotenv import load_dotenv

# Please put your env variables in .env file in the main directory of your project.
# The main directory is the directory from where you call mercury executable
# or python manage.py script.
#
# The example content of .env file:
# DEBUG=False
# SERVE_STATIC=True
# SECRET_KEY=django-insecure-)$12ir6-s6vbcufpva*va7bf$s$$(76ue$twwz9noath0&e91h

load_dotenv(".env")
load_dotenv("../.env")


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

MERCURY_DATA_DIR = Path(os.getenv('MERCURY_DATA_DIR', BASE_DIR))

FRONTEND_BUILD_DIR = str(BASE_DIR / "frontend-dist")
FRONTEND_STATIC_DIR = str(BASE_DIR / "frontend-dist" / "static")

STORAGE_MEDIA = "media"
STORAGE_S3 = "s3"
STORAGE = STORAGE_MEDIA
if os.environ.get("STORAGE", STORAGE_MEDIA) == STORAGE_S3:
    STORAGE = STORAGE_S3
DJANGO_DRF_FILEPOND_UPLOAD_TMP = str(MERCURY_DATA_DIR / "uploads-temp")
DJANGO_DRF_FILEPOND_FILE_STORE_PATH = str(MERCURY_DATA_DIR / "uploads")


CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", f"sqla+sqlite:///{str(MERCURY_DATA_DIR)}/celery.sqlite")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", f"db+sqlite:///{str(MERCURY_DATA_DIR)}/celery.sqlite")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-)$12ir6-s6vbcufpva*va7bf$s$$(76ue$twwz9noath0&e91h"
)
# Please keep SECRET_KEY secret!
# Generate new SECRET_KEY with the following code:
# from django.core.management.utils import get_random_secret_key
# print(get_random_secret_key())


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "True") == "True"
SERVE_STATIC = os.environ.get("SERVE_STATIC", "False") == "True"

ALLOWED_HOSTS = [
    "api.docker",
    "server",
    "127.0.0.1",
    "0.0.0.0",
    "localhost",
    "mercury.mljar.com",
]

if os.environ.get("ALLOWED_HOSTS") is not None:
    try:
        ALLOWED_HOSTS += os.environ.get("ALLOWED_HOSTS").split(",")
    except Exception as e:
        print("Cant set ALLOWED_HOSTS, using default")

# Application definition

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # 3rd party
    "rest_framework",
    "corsheaders",
    "django_drf_filepond",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "rest_framework.authtoken",
    # Mercury apps
    "apps.tasks",
    "apps.notebooks",
    "apps.ws",
    "apps.storage",
    "apps.accounts",
    "apps.workers",
]


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
    )
}

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

REST_AUTH = {"USER_DETAILS_SERIALIZER": "apps.accounts.serializers.UserSerializer"}


SITE_ID = 1

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = os.environ.get("ACCOUNT_EMAIL_VERIFICATION", "mandatory")  # "none" or "mandatory"
ACCOUNT_EMAIL_CONFIRMATION_HMAC = False
OLD_PASSWORD_FIELD_ENABLED = True  # use old password when password change in the app

# CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://single-site.localhost:3000",
#                 "http://127.0.0.1:3000"]

# CORS_ALLOWED_ORIGIN_REGEXES = [
#     r"^http://\w+\.localhost:3000$",
# ]

CORS_ALLOW_ALL_ORIGINS = True

MIDDLEWARE = ["django.middleware.security.SecurityMiddleware"]
if SERVE_STATIC:
    MIDDLEWARE += ["whitenoise.middleware.WhiteNoiseMiddleware"]

MIDDLEWARE += [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

X_FRAME_OPTIONS = "ALLOWALL"  # SAMEORGIN

ROOT_URLCONF = "server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [FRONTEND_BUILD_DIR, BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "server.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DB_SQLITE = "sqlite"
DB_POSTGRESQL = "postgresql"

DATABASES_ALL = {
    DB_SQLITE: {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": MERCURY_DATA_DIR / "db.sqlite3",
    },
    DB_POSTGRESQL: {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "NAME": os.environ.get("POSTGRES_NAME", "postgres"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "PORT": int(os.environ.get("POSTGRES_PORT", "5432")),
    },
}

DATABASES = {"default": DATABASES_ALL[os.environ.get("DJANGO_DB", DB_SQLITE)]}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = os.environ.get("TIME_ZONE", "UTC")

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
if DEBUG or SERVE_STATIC:
    STATIC_URL = "/static/"
    STATICFILES_DIRS = [FRONTEND_BUILD_DIR, FRONTEND_STATIC_DIR]
    if SERVE_STATIC:
        STATIC_ROOT = str(MERCURY_DATA_DIR / "static")
else:
    STATIC_URL = "/django_static/"
    STATIC_ROOT = str(BASE_DIR / "django_static")

MEDIA_ROOT = str(MERCURY_DATA_DIR / "media")

if not os.path.exists(MEDIA_ROOT):
    try:
        os.mkdir(MEDIA_ROOT)
    except Exception as e:
        raise Exception(f"Cannot create directory {MEDIA_ROOT}. {str(e)}")

MEDIA_URL = "/media/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


ASGI_APPLICATION = "server.asgi.application"

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "DJ {levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "DJ {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": "django-errors.log",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "ERROR"),
            "propagate": False,
        },
        'daphne': {
            'handlers': [
                'console', "file"
            ],
            'level': os.getenv("DJANGO_LOG_LEVEL", "ERROR")
        },
        'channels': {
            'handlers': [
                'console', "file"
            ],
            'level': os.getenv("DJANGO_LOG_LEVEL", "ERROR")
        },
    },
}

NBWORKERS_PER_MACHINE = int(os.environ.get("NBWORKERS_PER_MACHINE", 20))

# delta time after which worker is considered as stale and deleted
WORKER_STALE_TIME = 1  # in minutes

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION_NAME = os.environ.get("AWS_REGION_NAME")
AWS_BUCKET_NAME = os.environ.get("AWS_BUCKET_NAME")

# email setup, used in notification
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
EMAIL_USE_TLS = True  # use TLS by default
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
if os.environ.get("DJANGO_EMAIL_BACKEND", "console") == "smtp":
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
if os.environ.get("DJANGO_EMAIL_BACKEND", "console") == "ses":
    # you need to install django-ses
    EMAIL_BACKEND = "django_ses.SESBackend"
    AWS_SES_REGION_NAME = AWS_REGION_NAME
    AWS_SES_REGION_ENDPOINT = f'email.{AWS_REGION_NAME}.amazonaws.com'
    # DEFAULT_FROM_EMAIL = os.environ("DEFAULT_FROM_EMAIL", '"Mercury" <contact@runmercury.com>')
