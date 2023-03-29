from django.contrib.auth.models import User
from django.db import models

from apps.accounts.fields import AutoCreatedField, AutoLastModifiedField
from apps.accounts.models import Site
from apps.workers.models import Worker
from apps.notebooks.models import Notebook


class UploadedFile(models.Model):
    """Files that are uploaded in Dashboard"""

    filename = models.CharField(max_length=1024, blank=False, null=False)
    filepath = models.CharField(max_length=1024, blank=False, null=False)
    filetype = models.CharField(max_length=128, blank=False, null=False)
    filesize = models.IntegerField(blank=False, null=False)  # size in B
    hosted_on = models.ForeignKey(Site, on_delete=models.CASCADE)
    created_at = AutoCreatedField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )


class WorkerFile(models.Model):
    """Files created in worker (saved in output dir)"""

    filename = models.CharField(max_length=1024, blank=False, null=False)
    filepath = models.CharField(max_length=1024, blank=False, null=False)
    output_dir = models.CharField(max_length=1024, blank=False, null=False)
    local_filepath = models.CharField(max_length=1024, blank=False, null=False)
    created_at = AutoCreatedField()
    created_by = models.ForeignKey(
        Worker,
        on_delete=models.CASCADE,
    )


class UserUploadedFile(models.Model):
    """Files that are uploaded in notebook by users"""

    filename = models.CharField(max_length=1024, blank=False, null=False)
    filepath = models.CharField(max_length=1024, blank=False, null=False)

    hosted_on = models.ForeignKey(Site, on_delete=models.CASCADE)
    # web browser session id
    session_id = models.CharField(max_length=128)

    created_at = AutoCreatedField()
