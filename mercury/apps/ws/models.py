from django.db import models

from apps.notebooks.models import Notebook


class Worker(models.Model):
    # machine unique id
    machine_id = models.CharField(max_length=128, blank=True)

    # web browser session id
    session_id = models.CharField(max_length=128)

    # notebook
    notebook = models.ForeignKey(
        Notebook,
        on_delete=models.CASCADE,
    )

    state = models.CharField(max_length=128, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
