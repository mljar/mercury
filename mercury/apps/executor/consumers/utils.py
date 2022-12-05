CLIENT_SITE = "client"
WORKER_SITE = "worker"


def get_client_group(notebook_id, session_id):
    return f"{CLIENT_SITE}-{notebook_id}-{session_id}"


def get_worker_group(notebook_id, session_id):
    return f"{WORKER_SITE}-{notebook_id}-{session_id}"
