import os
from datetime import datetime

import requests
from allauth.account.admin import EmailAddress
from django.conf import settings
from django.contrib.auth.models import User
from django.test import LiveServerTestCase
from django.utils.timezone import make_aware

from apps.accounts.models import Site
from apps.nbworker.rest import RESTClient
from apps.notebooks.models import Notebook
from apps.storage.models import UploadedFile
from apps.storage.s3utils import S3
from apps.storage.storage import StorageManager
from apps.workers.models import Worker
from apps.workers.constants import WorkerState

# python manage.py test apps.nbworker -v 2


class RESTClientTestCase(LiveServerTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="developer",
            email="developer@example.com",
            password="developer",
        )
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True, primary=True
        )
        self.site = Site.objects.create(
            title="Mercury",
            slug="single-site",
            share=Site.PUBLIC,
            created_by=self.user,
        )

        self.nb = Notebook.objects.create(
            title="some",
            slug="some",
            path="some",
            created_by=self.user,
            hosted_on=self.site,
            file_updated_at=make_aware(datetime.now()),
        )

    def test_provision_uploaded_files(self):
        settings.STORAGE = settings.STORAGE_S3
        os.environ["MERCURY_SERVER_URL"] = self.live_server_url
        session_id = "some-string"

        worker = Worker.objects.create(session_id=session_id, notebook=self.nb)
        sm = StorageManager(session_id, worker.id, self.nb.id)

        fname = "test.txt"
        with open(fname, "w") as fout:
            fout.write("test")

        s3 = S3()
        bucket_key = f"test/{fname}"
        s3.upload_file(fname, bucket_key)

        f = UploadedFile.objects.create(
            filename=fname,
            filepath=bucket_key,
            filetype="txt",
            filesize=5,
            hosted_on=self.site,
            created_by=self.user,
        )

        os.remove(fname)
        self.assertFalse(os.path.exists(fname))

        sm.provision_uploaded_files()

        self.assertTrue(os.path.exists(fname))

    def test_sync_output_dir(self):
        settings.STORAGE = settings.STORAGE_S3
        os.environ["MERCURY_SERVER_URL"] = self.live_server_url
        session_id = "some-string"
        worker = Worker.objects.create(session_id=session_id, notebook=self.nb)
        sm = StorageManager(session_id, worker.id, self.nb.id)

        output_dir = sm.worker_output_dir()
        fname = "test.txt"
        fpath = os.path.join(output_dir, "test.txt")
        print(output_dir, fpath, fname)
        with open(fpath, "w") as fout:
            fout.write("test")

        sm.sync_output_dir()

        url = f"{self.live_server_url}/api/v1/worker-output-files/{session_id}/{worker.id}/{self.nb.id}"
        response = requests.get(url)
        print(response)
        print(response.json())

    def test_save_nb_html(self):
        settings.STORAGE = settings.STORAGE_S3
        os.environ["MERCURY_SERVER_URL"] = self.live_server_url

        nb_html = "<html>test</html>"
        session_id = "some-string"
        worker = Worker.objects.create(session_id=session_id, notebook=self.nb)

        sm = StorageManager(session_id, worker.id, self.nb.id)
        html_path, html_url = sm.save_nb_html(nb_html)
        response = requests.get(html_url)
        self.assertTrue(response.text, nb_html)

    def test_get_nb(self):
        session_id = "some-string"
        worker = Worker.objects.create(session_id=session_id, notebook=self.nb)

        os.environ["MERCURY_SERVER_URL"] = self.live_server_url
        client = RESTClient(self.nb.id, session_id, worker.id)
        client.load_notebook()
        self.assertTrue(client.notebook.id, self.nb.id)

        with self.assertRaises(SystemExit):
            wrong_nb_id = 2
            client = RESTClient(wrong_nb_id, session_id, worker.id)
            client.load_notebook()

        with self.assertRaises(SystemExit):
            wrong_session = "some-wrong-session"
            client = RESTClient(wrong_nb_id, wrong_session, worker.id)
            client.load_notebook()

    def test_save_worker_state(self):
        session_id = "some-string"
        worker = Worker.objects.create(
            session_id=session_id, notebook=self.nb, state=WorkerState.Unknown
        )

        os.environ["MERCURY_SERVER_URL"] = self.live_server_url
        client = RESTClient(self.nb.id, session_id, worker.id)

        client.set_worker_state(new_state=WorkerState.Busy)
        worker = Worker.objects.get(pk=worker.id)
        self.assertTrue(worker.state, WorkerState.Busy)
