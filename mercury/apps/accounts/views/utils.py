import os
import uuid

from django.template.defaultfilters import slugify


def is_cloud_version():
    return os.environ.get("MERCURY_CLOUD", "0") == "1"


def some_random_slug():
    h = uuid.uuid4().hex.replace("-", "")
    return h[:8]


def get_slug(slug, title):
    new_slug = slugify(slug)
    if new_slug == "":
        new_slug = slugify(title)
    if new_slug == "":
        new_slug = some_random_slug()
    return new_slug
