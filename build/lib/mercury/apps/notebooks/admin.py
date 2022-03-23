from django.contrib import admin

from apps.notebooks.models import Notebook


class NotebookModelAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "slug", "state", "path")

    class Meta:
        model = Notebook


admin.site.register(Notebook, NotebookModelAdmin)
