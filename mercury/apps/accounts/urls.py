from django.conf.urls import include
from django.urls import path, re_path
from django.conf.urls import url
from django.views.generic.base import TemplateView
from rest_framework.routers import DefaultRouter

from apps.accounts.views import (
    AddSecret,
    ListSecrets,
    GetSiteView,
    InitializeSite,
    InviteView,
    MembershipViewSet,
    SiteViewSet,
    WorkerListSecrets,
)

router = DefaultRouter()
router.register(r"api/v1/sites", SiteViewSet, basename="sites")
router.register(r"api/v1/(?P<site_id>.+)/members", MembershipViewSet, basename="sites")

accounts_urlpatterns = router.urls

accounts_urlpatterns += [
    path("api/v1/auth/", include("dj_rest_auth.urls")),
    path("api/v1/auth/register/", include("dj_rest_auth.registration.urls")),
    # path to set verify email in the frontend
    # fronted will do POST request to server with key
    # this is empty view, just to make reverse works
    re_path(
        r"^verify-email/(?P<key>[-:\w]+)/$",
        TemplateView.as_view(),
        name="account_confirm_email",
    ),
    # path to set password reset in the frontend
    # fronted will do POST request to server with uid and token
    # this is empty view, just to make reverse works
    re_path(
        r"^reset-password/(?P<uid>[-:\w]+)/(?P<token>[-:\w]+)/$",
        TemplateView.as_view(),
        name="password_reset_confirm",
    ),
    re_path("api/v1/(?P<site_id>.+)/invite", InviteView.as_view()),
    re_path("api/v1/get-site/(?P<site_slug>.+)/", GetSiteView.as_view()),
    re_path("api/v1/init-site/(?P<site_id>.+)/", InitializeSite.as_view()),
    re_path("api/v1/(?P<site_id>.+)/add-secret", AddSecret.as_view()),
    re_path("api/v1/(?P<site_id>.+)/list-secrets", ListSecrets.as_view()),
    re_path(
        "api/v1/worker/(?P<session_id>.+)/(?P<worker_id>.+)/(?P<notebook_id>.+)/worker-secrets",
        WorkerListSecrets.as_view(),
    )
]

