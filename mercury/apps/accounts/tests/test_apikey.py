# Please run tests with below command
# python manage.py test apps.accounts.tests.test_apikey

from allauth.account.admin import EmailAddress
from django.contrib.auth.models import User

from rest_framework.test import APITestCase

from apps.accounts.models import Site, ApiKey


class ApiKeyTestCase(APITestCase):
    register_url = "/api/v1/auth/register/"
    login_url = "/api/v1/auth/login/"
    get_api_key_url = "/api/v1/auth/api-key"
    regenerate_api_key_url = "/api/v1/auth/regenerate-api-key"

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
            title="First site", slug="first-site", created_by=self.user
        )

    def test_get_api_key(self):
        # login
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}
        
        self.assertEqual(len(ApiKey.objects.all()), 0)

        response = self.client.post(
            self.get_api_key_url,
        )
        self.assertEqual(response.status_code, 401)

        response = self.client.post(
            self.get_api_key_url, **headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("apiKey" in response.json())
        # there should 1 api key for each use
        response2 = self.client.post(
            self.get_api_key_url, **headers
        )
        self.assertEqual(len(ApiKey.objects.all()), 1)
        # and it should be unchanged
        self.assertEqual(response.json()["apiKey"], response2.json()["apiKey"])


    def test_regenerate_api_key(self):
        # login
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}
        self.assertEqual(len(ApiKey.objects.all()), 0)
        response = self.client.post(
            self.get_api_key_url, **headers
        )
        self.assertEqual(len(ApiKey.objects.all()), 1)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("apiKey" in response.json())
        # regenerate
        response2 = self.client.post(
            self.regenerate_api_key_url, **headers
        )
        # there should 1 api key for each use
        response3 = self.client.post(
            self.get_api_key_url, **headers
        )
        print(ApiKey.objects.all())
        self.assertEqual(len(ApiKey.objects.all()), 1)
        # after regenerate there should be change
        self.assertNotEqual(response.json()["apiKey"], response2.json()["apiKey"])
        # but in next request it should be unchanged
        self.assertEqual(response2.json()["apiKey"], response3.json()["apiKey"])

        