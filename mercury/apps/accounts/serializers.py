from dj_rest_auth.serializers import UserDetailsSerializer
from rest_framework import serializers

from apps.accounts.models import UserProfile
from apps.accounts.models import Site


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("info",)


class UserSerializer(UserDetailsSerializer):
    profile = UserProfileSerializer()

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ("profile",)


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        read_only_fields = ("id", "created_at")
        fields = ("id", "created_at", "title", "slug", "share")
