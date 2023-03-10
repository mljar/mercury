from celery import shared_task

from apps.accounts.models import Site, SiteState
from apps.storage.models import UploadedFile
from apps.storage.s3utils import S3
from apps.notebooks.tasks import task_init_notebook
from apps.storage.views import get_site_bucket_key
from apps.notebooks.models import Notebook


@shared_task(bind=True)
def task_init_site(self, job_params):
    site = Site.objects.get(pk=job_params["site_id"])
    site.status = SiteState.Initializing
    site.save()

    files = UploadedFile.objects.filter(hosted_on=site)

    any_notebooks = len([f for f in files if f.filetype == "ipynb"]) > 0

    if any_notebooks:
        # clear previous notebooks
        # just delete them
        Notebook.objects.filter(hosted_on=site).delete()
        s3 = S3()
        for f in files:
            print(f"Download {f.filepath}")
            s3.download_file(f.filepath, f.filename)
            if f.filetype == "ipynb":
                task_init_notebook(
                    f.filename,
                    bucket_key=get_site_bucket_key(site, "<replace>"),
                    site=site,
                    user=f.created_by,
                )

    site.status = SiteState.Ready
    site.save()


@shared_task(bind=True)
def task_send_invitation(self, job_params):
    print("TODO: send invitation")
    print(job_params["db_id"])
