from django.db import models


class Notebook(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    file_updated_at = models.DateTimeField(blank=True)
    title = models.CharField(max_length=512, blank=False)
    slug = models.CharField(max_length=512, blank=True)
    path = models.CharField(max_length=1024, blank=False)
    share = models.TextField(blank=True)
    params = models.TextField(blank=True)
    state = models.CharField(max_length=128, blank=True)
    default_view_path = models.CharField(max_length=1024, blank=True)
    output = models.CharField(max_length=128, blank=True)
    format = models.CharField(max_length=1024, blank=True)
    schedule = models.CharField(max_length=128, blank=True)
    notify = models.TextField(blank=True)
    errors = models.TextField(blank=True)
