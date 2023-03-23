from rest_framework import permissions

from apps.accounts.models import Membership, Site


class HasEditRights(permissions.BasePermission):
    def has_permission(self, request, view):
        site_id = view.kwargs.get("site_id")
        if site_id is None:  # just in case
            return False
        return (
            Membership.objects.filter(
                host__id=site_id, user=request.user, rights=Membership.EDIT
            )
            or Site.objects.get(pk=site_id).created_by == request.user
        )

    def has_object_permission(self, request, view, obj):
        return (
            Membership.objects.filter(
                host=obj.host, user=request.user, rights=Membership.EDIT
            )
            or obj.host.created_by == request.user
        )
