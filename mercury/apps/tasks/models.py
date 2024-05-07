from django.db import models

from apps.notebooks.models import Notebook
from django.contrib.auth.models import User
from apps.accounts.fields import AutoLastModifiedField

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

class RestAPITask(models.Model):
    # web browser session id
    session_id = models.CharField(max_length=128)
    # notebook
    notebook = models.ForeignKey(
        Notebook,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = AutoLastModifiedField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # state of execution, can be: CREATED, RECEIVED, DONE, ERROR
    state = models.CharField(max_length=128, blank=True)
    # input params for task
    params = models.TextField(blank=True)
    # result of execution, should contain
    # the path with HTML notebook
    nb_html_path = models.TextField(blank=True)
    # PDF path
    nb_pdf_path = models.TextField(blank=True)
    # JSON response
    response = models.TextField(blank=True)
