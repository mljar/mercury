import os
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv("../.env")

STORAGE_MEDIA = "media"
STORAGE_S3 = "s3"
STORAGE = STORAGE_MEDIA

if os.environ.get("STORAGE", STORAGE_MEDIA) == STORAGE_S3:
    STORAGE = STORAGE_S3

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

MERCURY_DATA_DIR = Path(os.getenv('MERCURY_DATA_DIR', BASE_DIR))

MEDIA_ROOT = str(MERCURY_DATA_DIR / "media")
MEDIA_URL = "/media/"


def get_bucket_key(site, user, filename):
    return f"site-{site.id}/user-{user.id}/{filename}"


def get_site_bucket_key(site, filename):
    return f"site-{site.id}/files/{filename}"


def get_worker_bucket_key(session_id, output_dir, filename):
    return f"session-{session_id}/{output_dir}/{filename}"


def get_user_upload_bucket_key(site_id, session_id, filename):
    return f"site-{site_id}/session-{session_id}/user-input/{filename}"
