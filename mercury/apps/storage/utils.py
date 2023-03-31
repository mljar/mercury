def get_bucket_key(site, user, filename):
    return f"site-{site.id}/user-{user.id}/{filename}"


def get_site_bucket_key(site, filename):
    return f"site-{site.id}/files/{filename}"


def get_worker_bucket_key(session_id, output_dir, filename):
    return f"session-{session_id}/{output_dir}/{filename}"


def get_user_upload_bucket_key(site_id, session_id, filename):
    return f"site-{site_id}/session-{session_id}/user-input/{filename}"
