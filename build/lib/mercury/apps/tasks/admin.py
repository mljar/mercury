from django.contrib import admin

# Register your models here.
from .models import Task


class TaskModelAdmin(admin.ModelAdmin):
    list_display = ("id", "session_id", "notebook", "state")

    class Meta:
        model = Task


admin.site.register(Task, TaskModelAdmin)
