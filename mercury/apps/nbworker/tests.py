import os

from django.test import LiveServerTestCase

# python manage.py test apps.nbworker -v 2

from apps.nbworker.rest import RESTClient

from apps.accounts.models import Site
from allauth.account.admin import EmailAddress
from django.contrib.auth.models import User
from apps.notebooks.models import Notebook
from apps.workers.models import Worker, WorkerState

from datetime import datetime
from django.utils.timezone import make_aware


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
