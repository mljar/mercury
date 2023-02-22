# Please run tests with below command
# python manage.py test apps.accounts

from allauth.account.admin import EmailAddress
from django.contrib.auth.models import User
from django.core import mail
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class AccountsTestCase(APITestCase):

    register_url = "/api/v1/auth/register/"
    verify_email_url = "/api/v1/auth/register/verify-email/"
    login_url = "/api/v1/auth/login/"
    user_details_url = "/api/v1/auth/user/"
    logout_url = "/api/v1/auth/logout/"
    delete_account_url = "/api/v1/auth/delete-account/"
    change_password_url = "/api/v1/auth/password/change/"
    reset_password_url = "/api/v1/auth/password/reset/"
    reset_password_confirm_url = "/api/v1/auth/password/reset/confirm/"

    def setUp(self):
        self.user1_params = {
            "username": "user1",  # it is optional to pass username
            "email": "piotr@example.com",
            "password": "verysecret",
        }
        # create user and verified email
        user = User.objects.create_user(
            username=self.user1_params["username"],
            email=self.user1_params["email"],
            password=self.user1_params["password"],
        )
        EmailAddress.objects.create(
            user=user, email=user.email, verified=True, primary=True
        )

    def test_register(self):

        # register data
        data = {
            "email": "user2@example-email.com",
            "password1": "verysecret",
            "password2": "verysecret",
        }
        # send POST request to "/api/auth/register/"
        response = self.client.post(self.register_url, data)
        # check the response status and data
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["detail"], "Verification e-mail sent.")

        # try to login - should fail, because email is not verified
        login_data = {
            "email": data["email"],
            "password": data["password1"],
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            "E-mail is not verified." in response.json()["non_field_errors"]
        )

        # expected one email to be send
        # parse email to get token
        self.assertEqual(len(mail.outbox), 1)
        email_lines = mail.outbox[0].body.splitlines()
        activation_line = [l for l in email_lines if "verify-email" in l][0]
        activation_link = activation_line.split("go to ")[1]
        activation_key = activation_link.split("/")[4]

        response = self.client.post(self.verify_email_url, {"key": activation_key})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["detail"], "ok")

        # lets login after verification to get token key
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("key" in response.json())

    def test_get_user_details(self):
        # login to get token
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        # set headers
        headers = {"HTTP_AUTHORIZATION": "Token " + token}
        # get user details
        response = self.client.get(self.user_details_url, **headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        print(data)
        for k in ["username", "email", "profile"]:
            self.assertTrue(k in data)
        self.assertTrue("info" in data["profile"])
        