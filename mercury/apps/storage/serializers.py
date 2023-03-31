from rest_framework import serializers

from dj_rest_auth.serializers import UserDetailsSerializer

from apps.storage.models import UploadedFile


class UploadedFileSerializer(serializers.ModelSerializer):
    created_by = UserDetailsSerializer(many=False, read_only=True)

    class Meta:
        model = UploadedFile
        read_only_fields = ("id", "created_at", "created_by")
        fields = ("id", "created_at", "created_by", "filename", "filesize", "filetype")
