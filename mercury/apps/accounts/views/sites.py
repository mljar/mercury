from http.client import FORBIDDEN
import json

from django.db import transaction
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.serializers import ValidationError

from apps.accounts.models import Membership, Site
from apps.accounts.serializers import SiteSerializer
from apps.accounts.tasks import task_init_site
from apps.accounts.views.utils import (
    get_slug,
    is_cloud_version,
    PLAN_KEY,
    PLAN_STARTER,
    PLAN_PRO,
    PLAN_BUSINESS,
)

from apps.accounts.views.permissions import HasEditRights

FORBIDDEN_SLUGS = [
    "mercury",
    "dashboard",
    "report",
    "mljar",
    "cloud",
    "api",
    "python",
    "backend",
    "frontend",
    "www",
    "app",
    "blog",
]


def get_plan(user):
    info = json.loads(user.profile.info)
    user_plan = info.get(PLAN_KEY, PLAN_STARTER)
    if user_plan not in [PLAN_STARTER, PLAN_PRO, PLAN_BUSINESS]:
        user_plan = PLAN_STARTER
    return user_plan


def max_number_of_sites(user):
    if not is_cloud_version():
        return 1000
    try:
        user_plan = get_plan(user)
        sites_plans = {PLAN_STARTER: 1, PLAN_PRO: 3, PLAN_BUSINESS: 10}
        return sites_plans[user_plan]
    except Exception as e:
        pass
    return 1


class SiteViewSet(viewsets.ModelViewSet):
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Site.objects.filter(
            Q(
                pk__in=Membership.objects.filter(
                    user=self.request.user, rights=Membership.EDIT
                ).values("host__id")
            )
            | Q(created_by=self.request.user)
        )

    def create(self, request, *args, **kwargs):
        # check number of allowed sites
        if Site.objects.filter(created_by=request.user).count() >= max_number_of_sites(
            request.user
        ):
            return Response(
                {
                    "msg": "Sorry, you reached Sites limit. Please upgrade subscription plan"
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        proposed_slug = get_slug(
            request.data.get("slug", ""), request.data.get("title", "")
        )
        if proposed_slug in FORBIDDEN_SLUGS:
            return Response(
                {"msg": "Please change site subdomain, current value is forbidden"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if Site.objects.filter(slug=proposed_slug):
            return Response(
                {"msg": "Please change site subdomain, current value is not unique"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if is_cloud_version():
            proposed_share = request.data.get("share", "")
            user_plan = get_plan(self.request.user)
            if user_plan == PLAN_STARTER and proposed_share == "PRIVATE":
                return Response(
                    {
                        "msg": "Sorry, you can't create PRIVATE Site. Please uprgade subscription plan"
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        try:
            # create a database instance
            with transaction.atomic():
                instance = serializer.save(created_by=self.request.user)

                instance.slug = get_slug(instance.slug, instance.title)

                instance.save()
        except Exception as e:
            raise APIException(str(e))

    def perform_update(self, serializer):
        updated_instance = serializer.save()
        # lets check slug if we update it
        new_slug = self.request.data.get("slug")

        if new_slug is not None:
            new_slug = get_slug(new_slug, updated_instance.title)
            if new_slug in FORBIDDEN_SLUGS:
                raise ValidationError(f"You cant use {new_slug} as a subdomain")

            if is_cloud_version():
                proposed_share = self.request.data.get("share", "")
                user_plan = get_plan(self.request.user)
                if user_plan == PLAN_STARTER and proposed_share == "PRIVATE":
                    raise ValidationError(
                        f"Sorry, you can't create PRIVATE Site. Please uprgade subscription plan"
                    )

            updated_instance.slug = new_slug
            updated_instance.save()

    def destroy(self, request, *args, **kwargs):
        """Only owner can delete object"""
        try:
            instance = self.get_object()
            if instance.created_by == self.request.user:
                self.perform_destroy(instance)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetSiteView(APIView):
    def get(self, request, site_slug, format=None):
        url = site_slug
        # this can be a custom domain
        custom_domain = url
        # or subdomain with domain
        subdomain, domain = "single-site", "runmercury.com"

        if len(url.split(".")) > 1:
            subdomain = url.split(".")[0]
            domain = ".".join(url.split(".")[1:])

        if site_slug in ["127.0.0.1", "localhost"]:
            subdomain = "single-site"
            domain = "runmercury.com"

        if request.build_absolute_uri().startswith("http://127.0.0.1"):
            subdomain = "single-site"
            domain = "runmercury.com"

        # print(f"{url}|{request.build_absolute_uri()}|{subdomain}|{domain}|{custom_domain}")

        sites = Site.objects.filter(
            Q(custom_domain=custom_domain) | Q(slug=subdomain, domain=domain)
        )
        if not sites:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if sites[0].share == Site.PUBLIC:
            return Response(SiteSerializer(sites[0]).data)

        if request.user.is_anonymous:
            return Response(status=status.HTTP_403_FORBIDDEN)

        sites = sites.filter(
            # any Membership (VIEW or EDIT) or owner
            Q(
                pk__in=Membership.objects.filter(user=self.request.user).values(
                    "host__id"
                )
            )
            | Q(created_by=self.request.user)
        )

        if not sites:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return Response(SiteSerializer(sites[0]).data)


class InitializeSite(APIView):
    permission_classes = [permissions.IsAuthenticated, HasEditRights]

    def post(self, request, site_id, format=None):
        try:
            with transaction.atomic():
                job_params = {"site_id": site_id}
                transaction.on_commit(lambda: task_init_site.delay(job_params))
                return Response(status=status.HTTP_200_OK)
        except Exception as e:
            raise APIException(str(e))
