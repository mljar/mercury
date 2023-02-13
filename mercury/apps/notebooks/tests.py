import os
import tempfile

import nbformat as nbf
from django.contrib.auth.models import User
from django.test import Client, TestCase
from pro.accounts.models import Membership, MercuryGroup
from rest_framework.reverse import reverse

from apps.notebooks.models import Notebook
from apps.notebooks.tasks import task_init_notebook

# python manage.py test apps


def create_notebook_without_yaml(filename, text="# Title", code="print(1)"):
    nb = nbf.v4.new_notebook()

    nb["cells"] = [nbf.v4.new_markdown_cell(text), nbf.v4.new_code_cell(code)]
    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        nbf.write(nb, f)


def create_notebook_with_yaml(
    filename, yaml="", text="# Title in md", code="print(1)", code2=""
):
    nb = nbf.v4.new_notebook()
    text = "# Title"
    nb["cells"] = [
        nbf.v4.new_raw_cell(yaml),
        nbf.v4.new_markdown_cell(text),
        nbf.v4.new_code_cell(code),
    ]
    if code2 != "":
        nb["cells"] += [nbf.v4.new_code_cell(code2)]

    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        nbf.write(nb, f)


class InitNotebookTestCase(TestCase):
    def test_init_notebook_without_yaml(self):
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_without_yaml(tmp.name + ".ipynb")
            task_init_notebook(tmp.name + ".ipynb")
            # in the case of missing YAML
            # notebook title should be 'Please provide title'
            nb = Notebook.objects.get(pk=1)
            self.assertEqual(nb.title, "Please provide title")

    def test_task_init_notebook(self):
        task_init_notebook(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "fixtures",
                "simple_notebook.ipynb",
            )
        )

    def test_init_notebook_with_empty_title(self):
        with tempfile.NamedTemporaryFile() as tmp:
            yaml = """---
title:
---"""
            create_notebook_with_yaml(tmp.name + ".ipynb", yaml)
            task_init_notebook(tmp.name + ".ipynb")

            # in the case of missing YAML
            # notebook title should be 'Please provide title'
            nb = Notebook.objects.get(pk=1)
            self.assertEqual(nb.title, "Please provide title")


class ShareNotebookTestCase(TestCase):
    def test_share_public(self):
        yaml = """---
share: public
---"""
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_without_yaml(tmp.name + ".ipynb")
            task_init_notebook(tmp.name + ".ipynb")

        response = self.client.get("/api/v1/notebooks/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_share_private(self):
        self.assertEqual(Notebook.objects.all().count(), 0)

        yaml = """---
share: private
---"""
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_with_yaml(tmp.name + ".ipynb", yaml=yaml)
            task_init_notebook(tmp.name + ".ipynb")

        # not logged user should see 0 notebooks
        response = self.client.get("/api/v1/notebooks/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        # create user and login
        user = {
            "username": "piotrek",
            "password": "verysecret",
        }
        User.objects.create_user(username=user["username"], password=user["password"])
        response = self.client.post(
            reverse("rest_login"), user, content_type="application/json"
        )
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}
        # logged user with token in headers should see 1 notebook
        response = self.client.get("/api/v1/notebooks/", **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_share_username(self):
        # create user and login
        user = {
            "username": "piotrek",
            "password": "verysecret",
        }
        User.objects.create_user(username=user["username"], password=user["password"])
        response = self.client.post(
            reverse("rest_login"), user, content_type="application/json"
        )
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        self.assertEqual(Notebook.objects.all().count(), 0)

        yaml = f"""---
share: {user["username"]}
---"""
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_with_yaml(tmp.name + ".ipynb", yaml=yaml)
            task_init_notebook(tmp.name + ".ipynb")

        # not logged user should see 0 notebooks
        response = self.client.get("/api/v1/notebooks/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        # logged should see 1 notebook
        response = self.client.get("/api/v1/notebooks/", **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

        # create second user
        user2 = {
            "username": "piotrek2",
            "password": "verysecret2",
        }
        User.objects.create_user(username=user2["username"], password=user2["password"])
        response = self.client.post(
            reverse("rest_login"), user2, content_type="application/json"
        )
        token2 = response.json()["key"]
        headers2 = {"HTTP_AUTHORIZATION": "Token " + token2}

        # logged by different user should see 0 notebooks
        response = self.client.get("/api/v1/notebooks/", **headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_share_group(self):
        # create user and login
        user = {
            "username": "piotrek",
            "password": "verysecret",
        }
        user_obj1 = User.objects.create_user(
            username=user["username"], password=user["password"]
        )
        response = self.client.post(
            reverse("rest_login"), user, content_type="application/json"
        )
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        # create second user
        user2 = {
            "username": "piotrek2",
            "password": "verysecret2",
        }
        user_obj2 = User.objects.create_user(
            username=user2["username"], password=user2["password"]
        )
        response = self.client.post(
            reverse("rest_login"), user2, content_type="application/json"
        )
        token2 = response.json()["key"]
        headers2 = {"HTTP_AUTHORIZATION": "Token " + token2}

        # create third user
        user3 = {
            "username": "piotrek3",
            "password": "verysecret3",
        }
        user_obj3 = User.objects.create_user(
            username=user3["username"], password=user3["password"]
        )
        response = self.client.post(
            reverse("rest_login"), user3, content_type="application/json"
        )
        token3 = response.json()["key"]
        headers3 = {"HTTP_AUTHORIZATION": "Token " + token3}

        #
        # create a group and add first and second used
        #
        group = MercuryGroup(name="group1")
        group.save()

        Membership(user=user_obj1, group=group).save()
        Membership(user=user_obj2, group=group).save()

        self.assertEqual(Notebook.objects.all().count(), 0)

        yaml = f"""---
share: {group.name}
---"""
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_with_yaml(tmp.name + ".ipynb", yaml=yaml)
            task_init_notebook(tmp.name + ".ipynb")

        # not logged user should see 0 notebooks
        response = self.client.get("/api/v1/notebooks/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        # logged as first user should see 1 notebook
        response = self.client.get("/api/v1/notebooks/", **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

        # logged as second user should see 1 notebook
        response = self.client.get("/api/v1/notebooks/", **headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

        # logged as third user should see 0 notebooks
        response = self.client.get("/api/v1/notebooks/", **headers3)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_get_single_notebook(self):
        # create user and login
        user = {
            "username": "piotrek",
            "password": "verysecret",
        }
        User.objects.create_user(username=user["username"], password=user["password"])
        response = self.client.post(
            reverse("rest_login"), user, content_type="application/json"
        )
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        # create second user
        user2 = {
            "username": "piotrek2",
            "password": "verysecret2",
        }
        user_obj2 = User.objects.create_user(
            username=user2["username"], password=user2["password"]
        )
        response = self.client.post(
            reverse("rest_login"), user2, content_type="application/json"
        )
        token2 = response.json()["key"]
        headers2 = {"HTTP_AUTHORIZATION": "Token " + token2}

        self.assertEqual(Notebook.objects.all().count(), 0)

        yaml = f"""---
share: {user2["username"]}
---"""
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_with_yaml(tmp.name + ".ipynb", yaml=yaml)
            task_init_notebook(tmp.name + ".ipynb")

        yaml = f"""---
share: private
---"""
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_with_yaml(tmp.name + ".ipynb", yaml=yaml)
            task_init_notebook(tmp.name + ".ipynb")

        # first user should see see 1 notebook
        response = self.client.get("/api/v1/notebooks/", **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

        # second user should see see 2 notebooks
        response = self.client.get("/api/v1/notebooks/", **headers2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

        # first user can not get first notebook
        response = self.client.get("/api/v1/notebooks/1/", **headers)
        self.assertEqual(response.status_code, 404)
        # first user can get first notebook
        response = self.client.get("/api/v1/notebooks/2/", **headers)
        self.assertEqual(response.status_code, 200)

        # second user can access both notebooks
        for i in [1, 2]:
            response = self.client.get(f"/api/v1/notebooks/{i}/", **headers2)
            self.assertEqual(response.status_code, 200)
