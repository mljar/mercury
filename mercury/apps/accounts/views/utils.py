import os
import uuid

from django.template.defaultfilters import slugify


PLAN_KEY = "plan"
PLAN_STARTER = "starter"
PLAN_PRO = "pro"
PLAN_BUSINESS = "business"

IDLE_TIME = {PLAN_STARTER: 5 * 60, PLAN_PRO: 30 * 60, PLAN_BUSINESS: 60 * 60}


def is_cloud_version():
    return os.environ.get("MERCURY_CLOUD", "0") == "1"


def get_idle_time(owner):
    if not is_cloud_version():
        return 24 * 60 * 60
    plan = PLAN_STARTER
    try:
        plan = owner.plan
    except Exception as e:
        pass
    return IDLE_TIME.get(plan, 5 * 60)


def get_max_run_time(owner):
    return get_idle_time(owner)


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
