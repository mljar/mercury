import logging
import os
import shutil
import sys
import uuid

import requests

from apps.nbworker.utils import stop_event
from apps.storage.utils import get_worker_bucket_key
from apps.tasks.export_pdf import to_pdf
from apps.storage.utils import STORAGE, STORAGE_MEDIA, STORAGE_S3, MEDIA_ROOT, MEDIA_URL


log = logging.getLogger(__name__)


class StorageManager:
    def __init__(self, session_id, worker_id, notebook_id):
        self.session_id = session_id
        self.worker_id = worker_id
        self.notebook_id = notebook_id
        self.server_url = os.environ.get("MERCURY_SERVER_URL", "http://127.0.0.1:8000")
        if STORAGE not in [STORAGE_MEDIA, STORAGE_S3]:
            log.error(f"{STORAGE} not implemented")
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
        log.info(f"Provision uploaded files")
        if STORAGE == STORAGE_MEDIA:
            pass
        elif STORAGE == STORAGE_S3:
            # get links
            url = f"{self.server_url}/api/v1/worker/uploaded-files-urls/{self.session_id}/{self.worker_id}/{self.notebook_id}"
            response = requests.get(url, timeout=5)
            download_urls = response.json().get("urls")
            # download files
            for url in download_urls:
                f = StorageManager.download_file(url)
                log.info(f"Downloaded {f}")

    @staticmethod
    def create_dir(dir_path):
        if not os.path.exists(dir_path):
            try:
                log.info(f"Create directory {dir_path}")
                os.mkdir(dir_path)
            except Exception as e:
                log.exception(f"Exception when create {dir_path}")
                raise Exception(f"Cant create {dir_path}")
        else:
            log.info(f"Directory {dir_path} already exists")

    @staticmethod
    def delete_dir(dir_path):
        if os.path.exists(dir_path):
            try:
                log.info(f"Delete directory {dir_path}")
                shutil.rmtree(dir_path, ignore_errors=True)
            except Exception as e:
                log.exception(f"Exception when delete {dir_path}")
                raise Exception(f"Cant delete {dir_path}")

    def worker_output_dir(self):
        if STORAGE == STORAGE_MEDIA:
            first_dir = os.path.join(str(MEDIA_ROOT), self.session_id)
            StorageManager.create_dir(first_dir)
            output_dir = os.path.join(
                str(MEDIA_ROOT), self.session_id, f"output_{self.worker_id}"
            )
            StorageManager.create_dir(output_dir)
            log.info(f"Worker output directory: {output_dir}")
            return output_dir
        elif STORAGE == STORAGE_S3:
            output_dir = f"output_{self.worker_id}"
            StorageManager.create_dir(output_dir)
            return output_dir

    def delete_worker_output_dir(self):
        if STORAGE == STORAGE_MEDIA:
            first_dir = os.path.join(str(MEDIA_ROOT), self.session_id)
            log.info(f"Delete Worker output directory: {first_dir}")
            StorageManager.delete_dir(first_dir)
        elif STORAGE == STORAGE_S3:
            output_dir = f"output_{self.worker_id}"
            StorageManager.delete_dir(output_dir)

    def sync_output_dir(self):
        if STORAGE == STORAGE_MEDIA:
            # nothing to do
            pass
        elif STORAGE == STORAGE_S3:
            # list all files in directory
            local_files = []
            output_dir = self.worker_output_dir()
            with os.scandir(output_dir) as entries:
                for entry in entries:
                    if entry.is_file():
                        print(entry, entry.path)
                        local_files += [entry]
            log.info(f"Sync {local_files}")

            action = "put_object"
            for entry in local_files:
                # upload them to s3
                url = f"{self.server_url}/api/v1/worker/presigned-url/{action}/{self.session_id}/{self.worker_id}/{self.notebook_id}/{output_dir}/{entry.name}"
                response = requests.get(url, timeout=5)
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
                response = requests.post(url, data, timeout=5)
                # that's all

    def list_worker_files_urls(self):
        files_urls = []
        if STORAGE == STORAGE_MEDIA:
            output_dir = self.worker_output_dir()
            for f in os.listdir(output_dir):
                if os.path.isfile(os.path.join(output_dir, f)):
                    files_urls += [
                        f"{MEDIA_URL}/{self.session_id}/output_{self.worker_id}/{f}"
                    ]
        elif STORAGE == STORAGE_S3:
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

        if STORAGE == STORAGE_MEDIA:
            html_path = os.path.join(self.worker_output_dir(), fname)
            with open(html_path, "w", encoding="utf-8", errors="ignore") as fout:
                fout.write(nb_html_body)
            html_url = f"{MEDIA_URL}/{self.session_id}/output_{self.worker_id}/{fname}"
        elif STORAGE == STORAGE_S3:
            # 1.
            # get upload link
            action = "put_object"
            output_dir = "downdload-html"
            url = f"{self.server_url}/api/v1/worker/presigned-url/{action}/{self.session_id}/{self.worker_id}/{self.notebook_id}/{output_dir}/{fname}"
            response = requests.get(url, timeout=15)
            upload_url = response.json().get("url")
            # 2.
            # upload file
            response = requests.put(upload_url, nb_html_body.encode("utf-8"), timeout=15)
            if response.status_code != 200:
                raise Exception(f"Notebook not uploaded {response}")
            # 3.
            # get download link
            action = "get_object"
            output_dir = "downdload-html"
            url = f"{self.server_url}/api/v1/worker/presigned-url/{action}/{self.session_id}/{self.worker_id}/{self.notebook_id}/{output_dir}/{fname}"
            response = requests.get(url, timeout=15)
            html_url = response.json().get("url")

        return html_path, html_url

    def save_nb_pdf(self, nb_html_body, is_presentation):
        pdf_path, pdf_url = None, None
        fname = f"download-notebook-{self.some_hash()}.pdf"
        if STORAGE == STORAGE_MEDIA:
            # save HTML
            html_path, html_url = self.save_nb_html(nb_html_body)

            # check if we need postfix
            slides_postfix = "?print-pdf" if is_presentation else ""

            # export to PDF
            pdf_path = html_path.replace(".html", ".pdf")
            pdf_url = html_url.replace(".html", ".pdf")
            log.info(f"Export {html_path}{slides_postfix} to PDF {pdf_path}")
            to_pdf(f"{html_path}{slides_postfix}", pdf_path)

        elif STORAGE == STORAGE_S3:
            # 0. first lets create HTML file
            html_fname = fname.replace(".pdf", ".html")
            html_path = os.path.abspath(
                os.path.join(self.worker_output_dir(), html_fname)
            )
            pdf_path = os.path.abspath(os.path.join(self.worker_output_dir(), fname))

            log.info(f"Dump to HTML {html_path}")
            with open(html_path, "w", encoding="utf-8", errors="ignore") as fout:
                fout.write(nb_html_body)
            # check if we need postfix
            slides_postfix = "?print-pdf" if is_presentation else ""
            # export to PDF
            log.info(f"Export HTML {html_path}{slides_postfix} to PDF {pdf_path}")
            to_pdf(f"{html_path}{slides_postfix}", pdf_path)

            # 1.
            # get upload link
            action = "put_object"
            output_dir = "downdload-pdf"
            url = f"{self.server_url}/api/v1/worker/presigned-url/{action}/{self.session_id}/{self.worker_id}/{self.notebook_id}/{output_dir}/{fname}"
            response = requests.get(url, timeout=15)
            upload_url = response.json().get("url")
            # 2.
            # upload file
            with open(pdf_path, "rb") as fout:
                response = requests.put(upload_url, fout.read())
                if response.status_code != 200:
                    raise Exception(f"PDF notebook not uploaded {response}")
            # 3.
            # get download link
            action = "get_object"
            output_dir = "downdload-pdf"
            url = f"{self.server_url}/api/v1/worker/presigned-url/{action}/{self.session_id}/{self.worker_id}/{self.notebook_id}/{output_dir}/{fname}"
            response = requests.get(url, timeout=15)
            pdf_url = response.json().get("url")

        return pdf_path, pdf_url

    def some_hash(self):
        h = uuid.uuid4().hex.replace("-", "")
        return h[:8]

    def get_user_uploaded_file(self, value):
        log.info("get user uploaded file " * 33)
        if STORAGE == STORAGE_MEDIA:
            log.info(f"Get file {value[0]} from id={value[1]}")
            import django

            django.setup()
            from django_drf_filepond.models import TemporaryUpload

            tu = TemporaryUpload.objects.get(upload_id=value[1])
            value[1] = tu.get_file_path()
            value[1] = value[1].replace("\\", "\\\\")
            log.info(f"File path is {value[1]}")
        elif STORAGE == STORAGE_S3:
            # get link

            url = f"{self.server_url}/api/v1/worker/user-uploaded-file/{self.session_id}/{self.worker_id}/{self.notebook_id}/{value[0]}"
            print(url)
            response = requests.get(url, timeout=15)
            download_url = response.json().get("url")
            # download file
            f = StorageManager.download_file(download_url)
            log.info(f"Downloaded {f}")
            value[1] = f
        return value
