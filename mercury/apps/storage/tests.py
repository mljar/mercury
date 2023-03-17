# Please run tests with below command
# python manage.py test apps.storage

import uuid

from allauth.account.admin import EmailAddress
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.client import encode_multipart
from django_drf_filepond.models import TemporaryUpload
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.accounts.models import Site
from apps.storage.s3utils import S3
from mercury.apps.storage.storage import StorageManager


class StorageTestCase(APITestCase):
    login_url = "/api/v1/auth/login/"
    upload_url = "/api/v1/fp/process/"

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

    def test_file_upload(self):
        fname = "test.txt"
        with open(fname, "w") as fout:
            fout.write("test file hello")

        data = None
        with open(fname, "rb") as fin:
            data = fin.read()

        file_spec = SimpleUploadedFile(fname, data)
        upload_form = {"filepond": file_spec}
        boundary = str(uuid.uuid4()).replace("-", "")

        encoded_form = encode_multipart(boundary, upload_form)
        content_type = "multipart/form-data; boundary=%s" % (boundary)

        # login as first user to get token
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        print("file upload", data)
        new_data = {"filepond": data}
        response = self.client.post(
            self.upload_url, data=encoded_form, content_type=content_type, **headers
        )
        print(response)
        print(response.data)

        tu = TemporaryUpload.objects.get(upload_id=response.data)
        print(tu)
        # tu.delete()

    def test_s3_live(self):
        fname = "test-file.txt"
        with open(fname, "w") as fout:
            fout.write("hello there")

        s3 = S3()
        bucket_key = "my-folder/test.txt"
        s3.upload_file(fname, bucket_key)
        new_fname = "test-file-2.txt"
        s3.download_file(bucket_key, new_fname)

        with open(new_fname, "r") as fin:
            print(fin.read())

        print(s3.list_files("my-folder"))

        s3.delete_file(bucket_key)

        print(s3.list_files("my-folder"))

        url = s3.get_presigned_url(bucket_key, "put_object")
        print(url)

        content = None
        with open(new_fname, "rb") as fin:
            content = fin.read()

        import requests

        response = requests.put(url, content)
        print(response)
