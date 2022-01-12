import os
import sys
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

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_BUILD_DIR = BASE_DIR / "frontend-dist"
FRONTEND_STATIC_DIR = BASE_DIR / "frontend-dist" / "static"

#  celery -A server worker --loglevel=info -P gevent --concurrency 2 -E
CELERY_BROKER_URL = "sqla+sqlite:///celery.sqlite"
CELERY_RESULT_BACKEND = "db+sqlite:///celery.sqlite"

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

ALLOWED_HOSTS = ["127.0.0.1", "0.0.0.0", "mercury.mljar.com"]

if os.environ.get("ALLOWED_HOSTS") is not None:
    try:
        ALLOWED_HOSTS += os.environ.get("ALLOWED_HOSTS").split(",")
    except Exception as e:
        print("Cant set ALLOWED_HOSTS, using default")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "apps.tasks",
    "apps.notebooks",
]

CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

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
        "DIRS": [FRONTEND_BUILD_DIR],
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


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

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
if DEBUG or SERVE_STATIC:
    STATIC_URL = "/static/"
    STATICFILES_DIRS = [FRONTEND_BUILD_DIR, FRONTEND_STATIC_DIR]
    if SERVE_STATIC:
        STATIC_ROOT = BASE_DIR / "static"
else:
    STATIC_URL = "/django_static/"
    STATIC_ROOT = BASE_DIR / "django_static"

MEDIA_ROOT = BASE_DIR / "media"

if not os.path.exists(MEDIA_ROOT):
    try:
        os.mkdir(MEDIA_ROOT)
    except Exception as e:
        raise Exception(f"Cannot create directory {MEDIA_ROOT}. {str(e)}")

MEDIA_URL = "/media/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
