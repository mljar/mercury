from allauth.account.admin import EmailAddress
from celery import shared_task

from django.conf import settings
from django.core.mail import send_mail

from apps.accounts.models import Invitation, Membership, Site, SiteStatus
from apps.notebooks.models import Notebook
from apps.notebooks.tasks import task_init_notebook
from apps.storage.models import UploadedFile
from apps.storage.s3utils import S3
from apps.storage.utils import get_site_bucket_key


@shared_task(bind=True)
def task_init_site(self, job_params):
    site = Site.objects.get(pk=job_params["site_id"])
    site.status = SiteStatus.INITIALIZING
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

    site.status = SiteStatus.READY
    site.save()


def get_app_address(site):
    subdomain = site.slug
    domain = site.domain
    custom_domain = site.custom_domain

    if custom_domain is not None and custom_domain != "":
        return custom_domain

    return f"https://{subdomain}.{domain}"


@shared_task(bind=True)
def task_send_invitation(self, job_params):
    invitation_id = job_params["invitation_id"]
    invitation = Invitation.objects.get(pk=invitation_id)

    from_address = EmailAddress.objects.get(user=invitation.created_by, primary=True)
    invited_by = invitation.created_by

    send_mail(
        "Mercury Invitation",
        f"""Hi,

User {invited_by.username} invites you to {invitation.rights.lower()} web app at {get_app_address(invitation.hosted_on)}.

Please create a new account at https://cloud.runmercury.com to access app.

Thank you!
Mercury Team        
""",
        settings.DEFAULT_FROM_EMAIL,
        [invitation.invited],
        fail_silently=False,
    )


@shared_task(bind=True)
def task_send_new_member(self, job_params):
    membership_id = job_params["membership_id"]
    membership = Membership.objects.get(pk=membership_id)

    from_address = EmailAddress.objects.get(user=membership.created_by, primary=True)
    invited_by = membership.created_by

    send_mail(
        "Mercury Invitation",
        f"""Hi,

User {invited_by.username} invites you to {membership.rights.lower()} web app at {get_app_address(membership.host)}.

Thank you!
Mercury Team        
""",
        settings.DEFAULT_FROM_EMAIL,
        [membership.user.email],
        fail_silently=False,
    )
