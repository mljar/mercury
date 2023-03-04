from django.contrib.auth.models import User
from django.db import models

from apps.accounts.fields import AutoCreatedField, AutoLastModifiedField
from apps.accounts.models import Site


class UploadedFile(models.Model):
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
