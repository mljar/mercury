from django.conf.urls import include
from django.urls import path, re_path
from django.views.generic.base import TemplateView


accounts_urlpatterns = [
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
    )
]
