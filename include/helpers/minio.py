from minio import Minio
from airflow.hooks.base import BaseHook

# For more information, see:
# https://min.io/docs/minio/linux/developers/python/API.html#
# https://github.com/minio/minio-py/tree/master/examples
def get_minio_client():
    minio = BaseHook.get_connection('minio').extra_dejson
    client = Minio(
        endpoint=minio['endpoint_url'].split('//')[1],
        access_key=minio['aws_access_key_id'],
        secret_key=minio['aws_secret_access_key'],
        secure=False
    )
    return client