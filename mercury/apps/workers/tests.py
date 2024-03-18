from django.test import TestCase

from django.contrib.auth.models import User
from apps.accounts.models import Site
from apps.notebooks.models import Notebook
from apps.workers.models import Machine, WorkerSession
from apps.workers.constants import WorkerSessionState
from apps.workers.utils import get_running_machines, shuffle_machines


from datetime import datetime

from allauth.account.admin import EmailAddress
from django.contrib.auth.models import User
from django.core import mail
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.accounts.models import Membership, Secret, Site
from apps.notebooks.models import Notebook
from apps.workers.models import Worker

# Create your tests here.
# python manage.py test apps.workers -v 2


class ManageMachinesTestCase(TestCase):
    def test_get_running_machines(self):
        ms = get_running_machines()
        self.assertEqual(len(ms), 0)

        Machine.objects.create(ipv4="0.0.0.0", state="Running")
        ms = get_running_machines()
        self.assertEqual(len(ms), 1)

    def test_shuffle_machines(self):
        Machine.objects.create(ipv4="0.0.0.0", state="Running")
        Machine.objects.create(ipv4="0.0.0.0", state="Running")

        ms = get_running_machines()
        self.assertEqual(len(ms), 2)
        ms = shuffle_machines(ms)
        self.assertEqual(len(ms), 2)


class WorkerSessionTestCase(TestCase):
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
        self.user2 = User.objects.create_user(
            username="developer2",
            email="developer2@example.com",
            password="developer2",
        )
        EmailAddress.objects.create(
            user=self.user2, email=self.user2.email, verified=True, primary=True
        )

    def test_create(self):
        WorkerSession.objects.create(
            ipv4="0.0.0.0",
            state=WorkerSessionState.Running,
            owned_by=self.user,
            site=self.site,
            notebook=self.nb,
        )
        self.assertEqual(len(WorkerSession.objects.all()), 1)

        WorkerSession.objects.create(
            ipv4="0.0.0.0",
            state=WorkerSessionState.Running,
            owned_by=self.user,
            run_by=self.user2,
            site=self.site,
            notebook=self.nb,
        )
        self.assertEqual(len(WorkerSession.objects.all()), 2)

    def test_update(self):
        WorkerSession.objects.create(
            ipv4="0.0.0.0",
            state=WorkerSessionState.Running,
            owned_by=self.user,
            site=self.site,
            notebook=self.nb,
        )
        self.assertEqual(len(WorkerSession.objects.all()), 1)

        ws = WorkerSession.objects.get(pk=1)
        prev_created_at, prev_updated_at = ws.created_at, ws.updated_at
        ws.save()

        self.assertEqual(prev_created_at, ws.created_at)
        self.assertNotEqual(prev_updated_at, ws.updated_at)


# python manage.py test apps.workers.tests.WorkerGetUserInfoTestCase -v 2
class WorkerGetUserInfoTestCase(TestCase):
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

        self.user2 = User.objects.create_user(
            username="developer2",
            email="developer2@example.com",
            password="developer2",
        )
        EmailAddress.objects.create(
            user=self.user2, email=self.user2.email, verified=True, primary=True
        )

    def test_get_owner(self):
        wrk = Worker.objects.create(
            machine_id="some-id", session_id="session-some-id", notebook=self.nb
        )
        url = f"/api/v1/worker/{wrk.session_id}/{wrk.id}/{self.nb.id}/owner-and-user"
        response = self.client.get(url)

        self.assertTrue("owner" in response.data)
        self.assertTrue("username" in response.data["owner"])
        self.assertTrue("email" in response.data["owner"])
        self.assertTrue("plan" in response.data["owner"])
        # there should be user information but it should be empty dict
        self.assertTrue("user" in response.data)
        self.assertTrue(not response.data["user"])  # empty dict = user not logged

    def test_get_user(self):
        wrk = Worker.objects.create(
            machine_id="some-id",
            session_id="session-some-id",
            notebook=self.nb,
            run_by=self.user2,
        )
        url = f"/api/v1/worker/{wrk.session_id}/{wrk.id}/{self.nb.id}/owner-and-user"
        response = self.client.get(url)

        self.assertTrue("user" in response.data)
        self.assertTrue("username" in response.data["user"])
        self.assertTrue("email" in response.data["user"])
