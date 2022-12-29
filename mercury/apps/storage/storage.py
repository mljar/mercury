import os
import shutil
from django.conf import settings

import logging

log = logging.getLogger(__name__)


class StorageManager:
    def __init__(self, session_id, worker_id):
        self.session_id = session_id
        self.worker_id = worker_id

    def worker_output_dir(self):
        if settings.STORAGE == settings.STORAGE_MEDIA:
            output_dir = os.path.join(
                str(settings.MEDIA_ROOT), self.session_id, f"output_{self.worker_id}"
            )
            if not os.path.exists(output_dir):
                try:
                    os.mkdir(output_dir)
                except Exception as e:
                    log.exception(f"Exception when create {output_dir}")
                    raise Exception(f"Cant create {output_dir}")
            log.debug(f"Worker output directory: {output_dir}")
            return output_dir
        raise Exception("Other methods for worker output directory are not implemented")

    def delete_worker_output_dir(self):
        if settings.STORAGE == settings.STORAGE_MEDIA:
            output_dir = self.worker_output_dir(self.session_id, self.worker_id)
            if os.path.exists(output_dir):
                try:
                    shutil.rmtree(output_dir, ignore_errors=True)
                except Exception as e:
                    log.exception(f"Exception when delete {output_dir}")
                    raise Exception(f"Cant delete {output_dir}")
            log.debug(f"Deleted worker output directory: {output_dir}")
            return output_dir
        raise Exception(
            "Other methods to delete worker output directory are not implemented"
        )


s
