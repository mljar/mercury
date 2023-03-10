import os

from django.test import LiveServerTestCase

# python manage.py test apps.nbworker -v 2

from apps.nbworker.db import DBClient

from apps.accounts.models import Site
from allauth.account.admin import EmailAddress
from django.contrib.auth.models import User
from apps.notebooks.models import Notebook
from apps.workers.models import Worker

from datetime import datetime
from django.utils.timezone import make_aware


class RESTClient(LiveServerTestCase):
    def test_get_nb(self):
        user = User.objects.create_user(
            username="developer",
            email="developer@example.com",
            password="developer",
        )
        EmailAddress.objects.create(
            user=user, email=user.email, verified=True, primary=True
        )
        site = Site.objects.create(
            title="Mercury",
            slug="single-site",
            share=Site.PUBLIC,
            created_by=user,
        )

        nb = Notebook.objects.create(
            title="some",
            slug="some",
            path="some",
            created_by=user,
            hosted_on=site,
            file_updated_at=make_aware(datetime.now()),
        )
        session_id = "some-string"
        worker = Worker.objects.create(session_id=session_id, notebook=nb)

        os.environ["MERCURY_SERVER_URL"] = self.live_server_url
        client = DBClient(nb.id, session_id, worker.id)
        client.load_notebook()
        self.assertTrue(client.notebook.id, nb.id)

        with self.assertRaises(SystemExit):
            wrong_nb_id = 2
            client = DBClient(wrong_nb_id, session_id, worker.id)
            client.load_notebook()
        
        with self.assertRaises(SystemExit):
            wrong_session = "some-wrong-session"
            client = DBClient(wrong_nb_id, wrong_session, worker.id)
            client.load_notebook()
