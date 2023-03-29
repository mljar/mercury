# Please run tests with below command
# python manage.py test apps.accounts
import os
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


# tests are disabled because they use live paddle api

# class SubscriptionTestCase(APITestCase):
#     register_url = "/api/v1/auth/register/"
#     verify_email_url = "/api/v1/auth/register/verify-email/"
#     login_url = "/api/v1/auth/login/"
#     user_details_url = "/api/v1/auth/user/"

#     subscription_url = "/api/v1/subscription"

#     def setUp(self):
#         #
#         # first user
#         #
#         self.user1_params = {
#             "username": "user1",  # it is optional to pass username
#             "email": "piotr@example.com",
#             "password": "verysecret",
#         }
#         self.user = User.objects.create_user(
#             username=self.user1_params["username"],
#             email=self.user1_params["email"],
#             password=self.user1_params["password"],
#         )
#         EmailAddress.objects.create(
#             user=self.user, email=self.user.email, verified=True, primary=True
#         )
#         #
#         # second user
#         #
#         self.user2_params = {
#             "username": "user2",  # it is optional to pass username
#             "email": "piotr2@example.com",
#             "password": "verysecret2",
#         }
#         self.user2 = User.objects.create_user(
#             username=self.user2_params["username"],
#             email=self.user2_params["email"],
#             password=self.user2_params["password"],
#         )
#         EmailAddress.objects.create(
#             user=self.user2, email=self.user2.email, verified=True, primary=True
#         )

#     def test_check_subscription(self):
#         # login as second user to get token
#         response = self.client.post(self.login_url, self.user1_params)
#         token = response.json()["key"]
#         headers = {"HTTP_AUTHORIZATION": "Token " + token}

#         new_data = {"action": "check", "checkoutId": "206702119-chre59f1e77e6ca-132bd39c55"}
#         response = self.client.post(self.subscription_url, new_data, **headers)
#         print(response)

#         user = User.objects.get(pk=1)
#         print(user.profile.info)


#     def test_is_active(self):
#         # login as second user to get token
#         response = self.client.post(self.login_url, self.user1_params)
#         token = response.json()["key"]
#         headers = {"HTTP_AUTHORIZATION": "Token " + token}

#         new_data = {"action": "check", "checkoutId": "206702119-chre59f1e77e6ca-132bd39c55"}
#         response = self.client.post(self.subscription_url, new_data, **headers)

#         user = User.objects.get(pk=1)
#         print(user.profile.info)

#         new_data = {"action": "is_active"}
#         response = self.client.post(self.subscription_url, new_data, **headers)
#         print(response)
#         print(response.json())

#         user = User.objects.get(pk=1)
#         print(user.profile.info)
