import json
import os
import tempfile

import yaml as yaml_lib
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from rest_framework.reverse import reverse

from apps.notebooks.models import Notebook
from apps.notebooks.tasks import task_init_notebook
from apps.notebooks.tests import create_notebook_with_yaml
from apps.tasks.models import Task
from apps.tasks.notify import notify
from apps.tasks.tasks import sanitize_string, task_execute

# python manage.py test apps.tasks.tests -v 2


class SanitizeTestCase(TestCase):
    def test_CJK(self):
        input_string = """テスト(){}
                        asdfasdf"()"[]''{}:"""

        output_string = sanitize_string(input_string)

        self.assertTrue("(" not in output_string)
        self.assertTrue("[" not in output_string)
        self.assertTrue(output_string.startswith("テスト"))
        self.assertTrue(output_string.endswith("asdfasdf:"))


class ExecuteNotebookTestCase(TestCase):
    def setUp(self):
        task_init_notebook(
            "apps/notebooks/fixtures/third_notebook.ipynb", render_html=False
        )

    def test_task_execute_notebook(self):
        Task.objects.create(notebook_id=1, session_id="test")

        job_params = {
            "db_id": 1,
        }

        task_execute(job_params)


class ExecuteNotebookAuthorizationTestCase(TestCase):
    def test_check_private(self):
        yaml = """---
share: private
---"""
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_with_yaml(tmp.name + ".ipynb", yaml=yaml)
            task_init_notebook(tmp.name + ".ipynb")

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

        # try to execute the notebook as anonymous user
        params = {"session_id": "some_session_id", "params": {}}
        response = self.client.post("/api/v1/execute/1", params)
        self.assertEqual(response.status_code, 404)

        # try to execute the notebook as logged user
        params = {"session_id": "some_session_id", "params": {}}
        response = self.client.post("/api/v1/execute/1", params, **headers)
        self.assertEqual(response.status_code, 201)

        task = Task.objects.get(pk=1)
        self.assertEqual(task.notebook.id, 1)


class RunNotebookRestAPITestCase(TestCase):
    def test_run(self):
        yaml = """---
title: test2
output: rest api
slug: test1
---"""
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_with_yaml(tmp.name + ".ipynb", yaml=yaml)
            task_init_notebook(tmp.name + ".ipynb")

        # execute the notebook
        params = {"a": "b", "c": "d"}
        response = self.client.post(
            "/run/test1", params, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

        task = Task.objects.get(pk=1)
        self.assertEqual(task.notebook.id, 1)

    def test_run_wrong_slug(self):
        yaml = """---
title: test2
output: rest api
slug: test1
---"""
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_with_yaml(tmp.name + ".ipynb", yaml=yaml)
            task_init_notebook(tmp.name + ".ipynb")

        # execute the notebook
        params = {"a": "b", "c": "d"}
        response = self.client.post(
            "/run/test123", params, content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)

    def test_run_not_authenticated(self):
        yaml = """---
title: test2
output: rest api
slug: test1
share: private
---"""
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_with_yaml(tmp.name + ".ipynb", yaml=yaml)
            task_init_notebook(tmp.name + ".ipynb")

        # execute the notebook
        params = {"a": "b", "c": "d"}
        response = self.client.post(
            "/run/test1", params, content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)

    def test_run_authenticated(self):
        yaml = """---
title: test2
output: rest api
slug: test1
share: private
---"""
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_with_yaml(tmp.name + ".ipynb", yaml=yaml)
            task_init_notebook(tmp.name + ".ipynb")

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

        # execute the notebook
        params = {"a": "b", "c": "d"}
        response = self.client.post(
            "/run/test1", params, content_type="application/json", **headers
        )
        self.assertEqual(response.status_code, 201)


class GetTaskRestAPITestCase(TestCase):
    def test_get(self):
        yaml = """---
title: test2
output: rest api
slug: test1
---"""
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_with_yaml(tmp.name + ".ipynb", yaml=yaml)
            task_init_notebook(tmp.name + ".ipynb")

        session_id = "my_session_id"
        Task.objects.create(
            state="CREATED", session_id=session_id, notebook=Notebook.objects.get(pk=1)
        )

        response = self.client.get(f"/get/{session_id}")
        self.assertEqual(response.status_code, 202)

    def test_get_wrong_session_id(self):
        yaml = """---
title: test2
output: rest api
slug: test1
---"""
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_with_yaml(tmp.name + ".ipynb", yaml=yaml)
            task_init_notebook(tmp.name + ".ipynb")

        session_id = "my_session_id"
        Task.objects.create(session_id=session_id, notebook=Notebook.objects.get(pk=1))

        response = self.client.get(f"/get/{session_id}-wrong-id")
        self.assertEqual(response.status_code, 404)

    def test_get_and_run(self):
        yaml = """---
title: test2
output: rest api
slug: test1
params:
    rest_response:
        output: response
---"""
        code = "rest_response = 'example.json'"

        code2 = """
import os
with open(rest_response, "w") as fout:
    fout.write('{"hello": "world"}')        
"""
        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_with_yaml(
                tmp.name + ".ipynb", yaml=yaml, code=code, code2=code2
            )
            task_init_notebook(tmp.name + ".ipynb")

        params = {"a": "b", "c": "d"}
        response = self.client.post(
            "/run/test1", params, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

        task = Task.objects.get(pk=1)
        self.assertEqual(task.notebook.id, 1)

        response = self.client.get(f"/get/{task.session_id}")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["state"], "running")

        task_execute(job_params={"db_id": 1})

        response = self.client.get(f"/get/{task.session_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"hello": "world"})


class NotifyTestCase(TestCase):
    def test_notify(self):
        User.objects.create_user(
            username="username1", password="password", email="contact@example.com"
        )
        config = """---
title: my notebook
schedule: '* * * * *'
notify:
    on_success: username1, contact@example.com
    attachment: html   
---"""

        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_with_yaml(
                tmp.name + ".ipynb", yaml=config, code="print('hello')"
            )
            task_init_notebook(tmp.name + ".ipynb")

            Task.objects.create(notebook_id=1, session_id="test")
            job_params = {"db_id": 1}
            task_execute(job_params)

            notebook = Notebook.objects.get(pk=1)
            task = Task.objects.get(pk=1)

            # notify(json.loads(notebook.notify), True, "", notebook.id, task.result)

        print(mail.outbox[0].subject)
        # print(mail.outbox[1].subject)
        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the subject of the first message is correct.
        self.assertTrue("success" in mail.outbox[0].subject)
