import logging
import os
import shutil
import sys
import uuid

import requests
from django.conf import settings
from execnb.nbio import write_nb

from apps.nbworker.utils import stop_event
from apps.storage.models import UploadedFile

from apps.tasks.export_pdf import to_pdf
from apps.storage.views import get_worker_bucket_key

log = logging.getLogger(__name__)


class StorageManager:
    def __init__(self, session_id, worker_id, notebook_id):
        self.session_id = session_id
        self.worker_id = worker_id
        self.notebook_id = notebook_id
        self.server_url = os.environ.get("MERCURY_SERVER_URL", "http://127.0.0.1:8000")
        if settings.STORAGE not in [settings.STORAGE_MEDIA, settings.STORAGE_S3]:
            log.error(f"{settings.STORAGE} not implemented")
            stop_event.set()
            sys.exit(1)

    @staticmethod
    def download_file(url):
        local_filename = url.split("?")[0].split("/")[-1]
        with requests.get(url, stream=True) as r:
            with open(local_filename, "wb") as f:
                shutil.copyfileobj(r.raw, f)

        return local_filename

    def provision_uploaded_files(self):
        log.debug(f"Provision uploaded files")
        if settings.STORAGE == settings.STORAGE_MEDIA:
            pass
        elif settings.STORAGE == settings.STORAGE_S3:
            # get links
            url = f"{self.server_url}/api/v1/worker/uploaded-files-urls/{self.session_id}/{self.worker_id}/{self.notebook_id}"
            response = requests.get(url)
            download_urls = response.json().get("urls")
            # download files
            for url in download_urls:
                f = StorageManager.download_file(url)
                log.debug(f"Downloaded {f}")

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
        elif settings.STORAGE == settings.STORAGE_S3:
            output_dir = f"output_{self.worker_id}"
            StorageManager.create_dir(output_dir)
            return output_dir

    def sync_output_dir(self):
        if settings.STORAGE == settings.STORAGE_MEDIA:
            # nothing to do
            pass
        elif settings.STORAGE == settings.STORAGE_S3:
            # list all files in directory
            local_files = []
            output_dir = self.worker_output_dir()
            with os.scandir(output_dir) as entries:
                for entry in entries:
                    if entry.is_file():
                        print(entry, entry.path)
                        local_files += [entry]
            log.debug(f"Sync {local_files}")

            action = "put_object"
            for entry in local_files:
                # upload them to s3
                url = f"{self.server_url}/api/v1/worker/presigned-url/{action}/{self.session_id}/{self.worker_id}/{self.notebook_id}/{output_dir}/{entry.name}"
                response = requests.get(url)
                upload_url = response.json().get("url")

                with open(entry.path, "rb") as fin:
                    response = requests.put(upload_url, fin.read())

                # create db objects
                url = f"{self.server_url}/api/v1/worker/add-file"
                data = {
                    "worker_id": self.worker_id,
                    "session_id": self.session_id,
                    "notebook_id": self.notebook_id,
                    "filename": entry.name,
                    "filepath": get_worker_bucket_key(
                        self.session_id, output_dir, entry.name
                    ),
                    "output_dir": output_dir,
                    "local_filepath": entry.path,
                }
                response = requests.post(url, data)
                # that's all

    def list_worker_files_urls(self):
        files_urls = []
        if settings.STORAGE == settings.STORAGE_MEDIA:
            output_dir = self.worker_output_dir()
            for f in os.listdir(output_dir):
                if os.path.isfile(os.path.join(output_dir, f)):
                    files_urls += [
                        f"{settings.MEDIA_URL}/{self.session_id}/output_{self.worker_id}/{f}"
                    ]
        elif settings.STORAGE == settings.STORAGE_S3:
            pass

        return files_urls

    # def save_nb(self, nb):
    #     fpath = None
    #     if settings.STORAGE == settings.STORAGE_MEDIA:
    #         fpath = os.path.join(
    #             self.worker_output_dir(), f"nb-{self.some_hash()}.ipynb"
    #         )
    #         write_nb(nb, fpath)
    #     return fpath

    def save_nb_html(self, nb_html_body):
        html_path, url = None, None
        fname = f"download-notebook-{self.some_hash()}.html"

        if settings.STORAGE == settings.STORAGE_MEDIA:
            html_path = os.path.join(self.worker_output_dir(), fname)
            with open(html_path, "w", encoding="utf-8", errors="ignore") as fout:
                fout.write(nb_html_body)
            html_url = f"{settings.MEDIA_URL}/{self.session_id}/output_{self.worker_id}/{fname}"
        elif settings.STORAGE == settings.STORAGE_S3:
            # 1.
            # get upload link
            action = "put_object"
            output_dir = "downdload-html"
            url = f"{self.server_url}/api/v1/worker/presigned-url/{action}/{self.session_id}/{self.worker_id}/{self.notebook_id}/{output_dir}/{fname}"
            response = requests.get(url)
            upload_url = response.json().get("url")
            # 2.
            # upload file
            response = requests.put(upload_url, nb_html_body)
            if response.status_code != 200:
                raise Exception(f"Notebook not uploaded {response}")
            # 3.
            # get download link
            action = "get_object"
            output_dir = "downdload-html"
            url = f"{self.server_url}/api/v1/worker/presigned-url/{action}/{self.session_id}/{self.worker_id}/{self.notebook_id}/{output_dir}/{fname}"
            response = requests.get(url)
            html_url = response.json().get("url")

        return html_path, html_url

    def save_nb_pdf(self, nb_html_body, is_presentation):
        pdf_path, pdf_url = None, None
        if settings.STORAGE == settings.STORAGE_MEDIA:
            # save HTML
            html_path, html_url = self.save_nb_html(nb_html_body)

            # check if we need postfix
            slides_postfix = "?print-pdf" if is_presentation else ""

            # export to PDF
            pdf_path = html_path.replace(".html", ".pdf")
            pdf_url = html_url.replace(".html", ".pdf")
            log.debug(f"Export {html_path}{slides_postfix} to PDF {pdf_path}")
            to_pdf(f"{html_path}{slides_postfix}", pdf_path)

        return pdf_path, pdf_url

    def some_hash(self):
        h = uuid.uuid4().hex.replace("-", "")
        return h[:8]
