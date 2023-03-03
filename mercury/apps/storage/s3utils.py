import logging
import boto3
from botocore.exceptions import ClientError
from django.conf import settings


log = logging.getLogger(__name__)

class S3:

    def __init__(self):
        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION_NAME,
            )
        except Exception:
            log.exception("Cant create S3 client")

    def get_presigned_url(self, bucket_key, client_method="put_object", expires_in=6*3600):
        try:
            method_parameters = {"Bucket": settings.AWS_BUCKET_NAME, "Key": "filename.txt"}
            url = self.s3_client.generate_presigned_url(
                ClientMethod=client_method, Params=method_parameters, ExpiresIn=expires_in
            )
        except Exception:
            log.exception(f"Exception when get presigned url, {bucket_key}, {client_method}")

    def download_file(self, bucket_key, file_name):
        try:
            self.s3_client.download_file(settings.AWS_BUCKET_NAME, bucket_key, file_name)
        except Exception:
            log.exception(f"Exception when downloading file {bucket_key}")


    def upload_file(self, file_name, bucket_key):
        try:
            self.s3_client.upload_file(file_name, settings.AWS_BUCKET_NAME, bucket_key)
        except Exception:
            log.exception(f"Exception when uploading file {file_name}")
            

    def delete_file(self, bucket_key):
        try:
            self.s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=bucket_key)
        except Exception:
            log.exception(f"Exception when delete file {bucket_key}")
            