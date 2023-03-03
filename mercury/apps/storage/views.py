from django.http import JsonResponse
from rest_framework.views import APIView

import boto3
import requests
from django.conf import settings


class ListFiles(APIView):
    def get(self, request, site_id, format=None):
        return JsonResponse([], safe=False)


def link():
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION_NAME,
    )
    client_method = "put_object"
    
    method_parameters = {"Bucket": settings.AWS_BUCKET_NAME, "Key": "filename.txt"}
    
    expires_in = 100
    
    url = s3_client.generate_presigned_url(
        ClientMethod=client_method, Params=method_parameters, ExpiresIn=expires_in
    )
    print(url)
    fname = "filename.txt"
    with open(fname, "w") as fout:
        fout.write("test")
    content = None
    with open(fname, "rb") as fin:
        content = fin.read()
    #response = requests.put(url, content)
    #print(response)

class GetPresignedUrl(APIView):
    def get(self, request, site_id, format=None):
        return JsonResponse({}, safe=False)
