from rest_framework import serializers
from apps.notebooks.models import Notebook


class NotebookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notebook
        read_only_fields = ("id", "created_at", "file_updated_at")
        fields = (
            "id",
            "created_at",
            "file_updated_at",
            "title",
            "slug",
            "path",
            "params",
            "state",
            "default_view_path",
        )
