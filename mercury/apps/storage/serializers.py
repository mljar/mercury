from rest_framework import serializers

from apps.storage.models import UploadedFile


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        read_only_fields = ("id", "created_at", "created_by")
        fields = ("id", "created_at", "created_by", "filename", "filesize", "filetype")
