from datetime import datetime
from datetime import timedelta
from django_drf_filepond.models import TemporaryUpload
from django.utils.timezone import make_aware

def clean_service():
    # clean temporary uploads older than 1 day
    # delete in DB remove files from storage as well
    tus = TemporaryUpload.objects.filter(uploaded__lte=make_aware(datetime.now() - timedelta(days=1)))
    tus.delete()