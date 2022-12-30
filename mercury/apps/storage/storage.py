import logging
import os
import shutil

from django.conf import settings

log = logging.getLogger(__name__)


class StorageManager:
    def __init__(self, session_id, worker_id):
        self.session_id = session_id
        self.worker_id = worker_id

    @staticmethod
    def create_dir(dir_path):
        if not os.path.exists(dir_path):
            try:
                log.debug(f"Create directory {dir_path}")
                os.mkdir(dir_path)
            except Exception as e:
                log.exception(f"Exception when create {dir_path}")
                raise Exception(f"Cant create {dir_path}")
        else:
            log.debug(f"Directory {dir_path} already exists")

    @staticmethod
    def delete_dir(dir_path):
        if os.path.exists(dir_path):
            try:
                log.debug(f"Delete directory {dir_path}")
                shutil.rmtree(dir_path, ignore_errors=True)
            except Exception as e:
                log.exception(f"Exception when delete {dir_path}")
                raise Exception(f"Cant delete {dir_path}")

    def worker_output_dir(self):
        if settings.STORAGE == settings.STORAGE_MEDIA:
            first_dir = os.path.join(str(settings.MEDIA_ROOT), self.session_id)
            StorageManager.create_dir(first_dir)
            output_dir = os.path.join(
                str(settings.MEDIA_ROOT), self.session_id, f"output_{self.worker_id}"
            )
            StorageManager.create_dir(output_dir)
            log.debug(f"Worker output directory: {output_dir}")
            return output_dir
        raise Exception("Other methods for worker output directory are not implemented")

    def delete_worker_output_dir(self):
        if settings.STORAGE == settings.STORAGE_MEDIA:
            output_dir = self.worker_output_dir(self.session_id, self.worker_id)
            StorageManager.delete_dir(output_dir)
            log.debug(f"Deleted worker output directory: {output_dir}")
            return output_dir
        raise Exception(
            "Other methods to delete worker output directory are not implemented"
        )

    def list_worker_files_urls(self):
        files_urls = []
        if settings.STORAGE == settings.STORAGE_MEDIA:
            output_dir = self.worker_output_dir()
            for f in os.listdir(output_dir):
                if os.path.isfile(os.path.join(output_dir, f)):
                    files_urls += [
                        f"{settings.MEDIA_URL}/{self.session_id}/output_{self.worker_id}/{f}"
                    ]
        return files_urls
