from django.contrib.auth.models import User
from django.db import models

from apps.accounts.fields import AutoCreatedField, AutoLastModifiedField
from apps.accounts.models import Site


# Create your models here.
class UploadedFile(models.Model):
    filename = models.CharField(max_length=1024, blank=False, null=False)

    filepath = models.CharField(max_length=1024, blank=False, null=False)

    filetype = models.CharField(max_length=128, blank=False, null=False)

    hosted_on = models.ForeignKey(Site, on_delete=models.CASCADE)
    created_at = AutoCreatedField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
