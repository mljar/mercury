from django.db import models

from apps.notebooks.models import Notebook


class Task(models.Model):
    # task id from Celery
    task_id = models.CharField(max_length=128, blank=True)
    # web browser session id
    session_id = models.CharField(max_length=128)
    # notebook
    notebook = models.ForeignKey(
        Notebook,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # state of execution, can be: CREATED, RECEIVED, DONE, ERROR
    state = models.CharField(max_length=128, blank=True)
    # input params for task
    params = models.TextField(blank=True)
    # result of execution, should contain
    # the path with HTML notebook
    result = models.TextField(blank=True)
