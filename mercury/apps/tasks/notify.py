import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage

from apps.notebooks.models import Notebook
from apps.tasks.tasks_export import export_to_pdf


def validate_notify(config: dict) -> str:
    """returns the string with error message from notify parsing"""

    if not config:
        return ""
    try:
        on_success, on_failure, attachment = parse_config(config)
        if not on_success and not on_failure:
            return (
                "Please specify `on_success` or `on_failure` in the `notify` parameter."
            )
        if attachment and not ("pdf" in attachment or "html" in attachment):
            return "Please specify `html` or `pdf` format in the `attachment` in the `notify`."
    except Exception as e:
        return "Error while parsing `notify` in the YAML config."
    return ""


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
    attachment = config.get("attachment", "")

    on_success = on_success.split(",")
    on_failure = on_failure.split(",")

    on_success = list_to_emails(on_success)
    on_failure = list_to_emails(on_failure)

    return on_success, on_failure, attachment


def notify(config, is_success, error_msg, notebook_id, notebook_url):
    try:
        if not config:
            # no config provided, skip notify step
            return

        on_success, on_failure, attachment = parse_config(config)

        notebook = Notebook.objects.get(pk=notebook_id)

        email = None
        if on_success and is_success:
            msg = f"""Notebook '{notebook.title}' executed successfully."""
            email = EmailMessage(
                "Notebook executed successfully",
                msg,
                None,  # use default from email (from django settings)
                on_success,
            )
        if on_failure and not is_success:
            msg = f"""Notebook '{notebook.title}' failed to execute. {error_msg}"""
            email = EmailMessage(
                "Notebook failed to execute",
                msg,
                None,  # use default from email (from django settings)
                on_failure,
            )
        if email is not None:
            notebook_html_path = os.path.join(
                *(
                    [settings.MEDIA_ROOT]
                    + notebook_url.replace(settings.MEDIA_URL, "", 1).split("/")
                )
            )

            if "html" in attachment and os.path.exists(notebook_html_path):
                email.attach_file(notebook_html_path)
            if "pdf" in attachment and os.path.exists(notebook_html_path):
                export_to_pdf(
                    {"notebook_id": notebook_id, "notebook_path": notebook_url}
                )
                notebook_pdf_path = notebook_html_path.replace(".html", ".pdf")
                email.attach_file(notebook_pdf_path)

            email.send(fail_silently=True)
    except Exception as e:
        print("Error in the notify step")
        print(str(e))
