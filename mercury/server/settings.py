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


is_pro = False
try:
    # try to import the Mercury pro features
    # it is available only for commercial users
    # you can check available license at https://mljar.com/pricing
    import pro

    is_pro = True
except ImportError:
    pass

if is_pro:
    print("*** Running Mercury Pro ***")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# if HF_SPACE is defined we will use single notebook frontend
HF_SPACE = os.environ.get("HF_SPACE")
if HF_SPACE is None:
    FRONTEND_BUILD_DIR = BASE_DIR / "frontend-dist"
    FRONTEND_STATIC_DIR = BASE_DIR / "frontend-dist" / "static"
else:
    FRONTEND_BUILD_DIR = BASE_DIR / "frontend-single-site-dist"
    FRONTEND_STATIC_DIR = BASE_DIR / "frontend-single-site-dist" / "static"

    for d in [
        FRONTEND_BUILD_DIR,
        FRONTEND_BUILD_DIR / "static" / "css",
        FRONTEND_BUILD_DIR / "static" / "js",
    ]:
        for f in os.listdir(d):

            fpath = os.path.join(d, f)
            if not os.path.isfile(fpath):
                continue
            if fpath.endswith(".ico"):
                continue

            content = ""
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fin:
                content = fin.read()
            if HF_SPACE == "local":
                content = content.replace("http://mydomain.com/example/to/replace/", "")
            else:
                content = content.replace("example/to/replace", HF_SPACE)

            with open(fpath, "w", encoding="utf-8", errors="ignore") as fout:
                fout.write(content)

STORAGE_MEDIA = "media"
STORAGE_S3 = "s3"
STORAGE = STORAGE_MEDIA
DJANGO_DRF_FILEPOND_UPLOAD_TMP = str(BASE_DIR / "uploads-temp")
DJANGO_DRF_FILEPOND_FILE_STORE_PATH = str(BASE_DIR / "uploads")


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

ALLOWED_HOSTS = ["127.0.0.1", "0.0.0.0", "localhost", "mercury.mljar.com"]

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
    "rest_framework",
    "corsheaders",
    "django_drf_filepond",
    "apps.tasks",
    "apps.notebooks",
    "apps.ws",
    "apps.storage",
]

if is_pro:
    # setup pro features
    INSTALLED_APPS += [
        "rest_framework.authtoken",
        "pro.accounts",
    ]
    ACCOUNT_AUTHENTICATION_METHOD = "username"
    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": (
            "rest_framework.authentication.TokenAuthentication",
        )
    }


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

DB_SQLITE = "sqlite"
DB_POSTGRESQL = "postgresql"

DATABASES_ALL = {
    DB_SQLITE: {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
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

# email setup, used in notification
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")  # default set to gmail smtp
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_PORT = os.environ.get("EMAIL_PORT", 587)
EMAIL_USE_TLS = True  # use TLS by default
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
if EMAIL_HOST_USER is not None:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


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
    },
}

NBWORKERS_PER_MACHINE = 20


# delta time after which worker is considered as stale and deleted
WORKER_STALE_TIME = 1 # in minutes

