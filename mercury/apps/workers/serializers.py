from rest_framework import serializers

from apps.workers.models import Worker


class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        read_only_fields = ("id", "created_at", "updated_at")
        fields = ("id", "created_at", "updated_at", "state")
