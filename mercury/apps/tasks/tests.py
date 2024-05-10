#
# python manage.py test apps.tasks.tests -v 2

from django.test import TestCase
from allauth.account.admin import EmailAddress
from django.contrib.auth.models import User

from rest_framework.test import APITestCase

from apps.accounts.models import Membership, Site

from apps.tasks.tasks import sanitize_string


from datetime import datetime
from django.utils.timezone import make_aware
from apps.notebooks.models import Notebook


class SanitizeTestCase(TestCase):
    def test_CJK(self):
        input_string = """テスト(){}
                        asdfasdf"()"[]''{}:"""

        output_string = sanitize_string(input_string)

        self.assertTrue("(" not in output_string)
        self.assertTrue("[" not in output_string)
        self.assertTrue(output_string.startswith("テスト"))
        self.assertTrue(output_string.endswith("asdfasdf:"))



class CreateRestApiTaskTestCase(APITestCase):
    register_url = "/api/v1/auth/register/"
    login_url = "/api/v1/auth/login/"
    get_api_key_url = "/api/v1/auth/api-key"
    create_rest_api_task_url = "/api/v1/{}/run/{}" # site_id, notebook_slug

    def setUp(self):
        self.user1_params = {
            "username": "user1",  # it is optional to pass username
            "email": "piotr@example.com",
            "password": "verysecret",
        }
        self.user = User.objects.create_user(
            username=self.user1_params["username"],
            email=self.user1_params["email"],
            password=self.user1_params["password"],
        )
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True, primary=True
        )
        self.site = Site.objects.create(
            title="First site", slug="public-site", created_by=self.user
        )
        self.private_site = Site.objects.create(
            title="First site", slug="private-site", created_by=self.user, share=Site.PRIVATE
        )

        self.notebook = Notebook.objects.create(
            title="some",
            slug="some",
            path="some",
            created_by=self.user,
            hosted_on=self.site,
            file_updated_at=make_aware(datetime.now()),
        )
        self.private_notebook = Notebook.objects.create(
            title="some",
            slug="some",
            path="some",
            created_by=self.user,
            hosted_on=self.private_site,
            file_updated_at=make_aware(datetime.now()),
        )

        #
        # second user
        #
        self.user2_params = {
            "username": "user2",  # it is optional to pass username
            "email": "piotr2@example.com",
            "password": "verysecret2",
        }
        self.user2 = User.objects.create_user(
            username=self.user2_params["username"],
            email=self.user2_params["email"],
            password=self.user2_params["password"],
        )
        EmailAddress.objects.create(
            user=self.user2, email=self.user2.email, verified=True, primary=True
        )
        

    def test_create_task_with_api_key(self):
        # login
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}
        # get apiKey 
        response = self.client.post(
            self.get_api_key_url, **headers
        )
        apiKey = response.json()["apiKey"]
        print(apiKey)

        
        wrong_headers = {"HTTP_AUTHORIZATION": "Token wrong-token"}
        bearer_headers = {"HTTP_AUTHORIZATION": "Bearer " + apiKey}
        wrong_bearer_headers = {"HTTP_AUTHORIZATION": "Bearer wrong-api-key"}
        
        # public site
        response = self.client.post(self.create_rest_api_task_url.format(self.site.id, self.notebook.slug), **headers)
        self.assertEqual(response.status_code, 201)
        response = self.client.post(self.create_rest_api_task_url.format(self.site.id, self.notebook.slug), **wrong_headers)
        self.assertEqual(response.status_code, 401)
        response = self.client.post(self.create_rest_api_task_url.format(self.site.id, self.notebook.slug))
        self.assertEqual(response.status_code, 201)
        response = self.client.post(self.create_rest_api_task_url.format(self.private_site.id, self.private_notebook.slug), **bearer_headers)
        self.assertEqual(response.status_code, 201)
        response = self.client.post(self.create_rest_api_task_url.format(self.private_site.id, self.private_notebook.slug), **wrong_bearer_headers)
        self.assertEqual(response.status_code, 404)
        # private site
        response = self.client.post(self.create_rest_api_task_url.format(self.private_site.id, self.private_notebook.slug), **headers)
        self.assertEqual(response.status_code, 201)
        response = self.client.post(self.create_rest_api_task_url.format(self.private_site.id, self.private_notebook.slug), **wrong_headers)
        self.assertEqual(response.status_code, 401)
        response = self.client.post(self.create_rest_api_task_url.format(self.private_site.id, self.private_notebook.slug))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(self.create_rest_api_task_url.format(self.private_site.id, self.private_notebook.slug), **bearer_headers)
        self.assertEqual(response.status_code, 201)
        response = self.client.post(self.create_rest_api_task_url.format(self.private_site.id, self.private_notebook.slug), **wrong_bearer_headers)
        self.assertEqual(response.status_code, 404)
        

        # login user 2
        response = self.client.post(self.login_url, self.user2_params)
        token2 = response.json()["key"]
        headers2 = {"HTTP_AUTHORIZATION": "Token " + token2}
        # get apiKey for user 2 
        response = self.client.post(
            self.get_api_key_url, **headers2
        )
        apiKey2 = response.json()["apiKey"]
        bearer_headers2 = {"HTTP_AUTHORIZATION": "Bearer " + apiKey2}

        response = self.client.post(self.create_rest_api_task_url.format(self.private_site.id, self.private_notebook.slug), **bearer_headers2)
        self.assertEqual(response.status_code, 404)
        
        # add rights to view 
        Membership.objects.create(
            user=self.user2, host=self.private_site, rights=Membership.VIEW, created_by=self.user
        )

        response = self.client.post(self.create_rest_api_task_url.format(self.private_site.id, self.private_notebook.slug), **bearer_headers2)
        self.assertEqual(response.status_code, 201)
