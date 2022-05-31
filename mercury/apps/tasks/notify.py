import os
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from apps.tasks.tasks_export import export_to_pdf


def valid_notify(config):
    return True


def username_to_email(username):
    users = User.objects.filter(username=username)
    if not users:
        return ""
    # not worry about duplicates in username
    return users[0].email


def list_to_emails(contacts):
    emails = []
    for contact in contacts:
        contact = contact.strip()
        if "@" in contact:
            emails += [contact]
        else:
            email_address = username_to_email(contact)
            if email_address:
                emails += [email_address]
    return list(set(emails))


def parse_config(config):
    on_success = config.get("on_success", "")
    on_failure = config.get("on_failure", "")
    attachment = config.get("attachment", "html")

    on_success = on_success.split(",")
    on_failure = on_failure.split(",")

    on_success = list_to_emails(on_success)
    on_failure = list_to_emails(on_failure)

    return on_success, on_failure, attachment


def notify(config, is_success, error_msg, notebook_id, notebook_url_path):

    if not config:
        # no config provided, skip notify step
        return

    on_success, on_failure, attachment = parse_config(config)

    print(on_success, on_failure, attachment)

    notebook_os_path = os.path.join(
        *(
            [settings.MEDIA_ROOT]
            + notebook_url_path.replace(settings.MEDIA_URL, "", 1).split("/")
        )
    )
    notebook_os_path_pdf = ""
    if "pdf" in attachment:
        export_to_pdf({"notebook_id": notebook_id, "notebook_path": notebook_url_path})
        notebook_os_path_pdf = notebook_os_path.replace(".html", ".pdf")

    print(notebook_os_path)
    print(notebook_os_path_pdf)

    if on_success and is_success:
        msg = """Your notebook executed successfully"""
        send_mail(
            "Notebook executed successfully",
            msg,
            None,  # use default from email (from django settings)
            on_success,
            fail_silently=True,
        )
    if on_failure and not is_success:
        msg = """Your Notebook failed to execute"""
        send_mail(
            "Notebook failed to execute",
            msg,
            None,  # use default from email (from django settings)
            on_failure,
            fail_silently=True,
        )
