from rest_framework import serializers

from apps.tasks.models import Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        read_only_fields = ("id", "created_at", "notebook_id")
        fields = (
            "id",
            "task_id",
            "session_id",
            "created_at",
            "state",
            "params",
            "result",
        )
