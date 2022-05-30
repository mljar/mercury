
from django.core.mail import send_mail

def valid_notify(config):
    return True

def list_to_emails():
    pass

def notify(config, is_success, error_msg, notebook_id, notebook_url_path):

    if not config:
        return

    on_success = config.get("on_success", [])
    on_failure = config.get("on_failure", [])
    attachment = config.get("attachment", [])
    

    
    if not is_success:
        pass

    send_mail(
        'Subject here',
        'Here is the message.',
        'from@example.com',
        ['to@example.com'],
        fail_silently=False,
    )
    