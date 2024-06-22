import os
import jwt
from django.conf import settings
from datetime import (
    timedelta,
    datetime,
    timezone
)
from http import HTTPStatus
from .messages import MESSAGES
import boto3
from botocore.exceptions import ClientError
import uuid
from math import radians, cos, sin, asin, sqrt

# AWS S3 Configurations
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_S3_REGION_NAME
)


def upload_file_to_s3(file_obj):
    try:
        # Generate unique filename for S3
        file_name = f"{uuid.uuid4()}"

        # Upload file to S3 bucket
        s3_client.upload_fileobj(
            file_obj,
            AWS_STORAGE_BUCKET_NAME,
            file_name
        )

        # Return the URL of the uploaded file
        file_url = (
            f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}."
            f"amazonaws.com/{file_name}"
        )

        return file_url

    except ClientError as e:
        raise e


def generate_jwt_token(**kwargs):
    payload = {
        **kwargs,
        'exp': datetime.now(timezone.utc) +
        timedelta(days=int(os.environ.get('JWT_EXP_TIME'))),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=os.environ.get('JWT_ALGORITHM')
    )


def decode_jwt_token(token, lng):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[os.environ.get('JWT_ALGORITHM')]
        )

        return {
            'message': MESSAGES[lng].get('SUCCESS_MESSAGE_LOGIN'),
            'data': payload,
            'error': False,
            'status': HTTPStatus.OK
        }

    except jwt.ExpiredSignatureError:
        return {
            'message': MESSAGES[lng].get('ERROR_MESSAGE_JWT_EXP'),
            'data': None,
            'error': True,
            'status': HTTPStatus.UNAUTHORIZED
        }

    except jwt.InvalidTokenError:
        return {
            'message': MESSAGES[lng].get('ERROR_MESSAGE_INVALID_JWT'),
            'data': None,
            'error': True,
            'status': HTTPStatus.UNAUTHORIZED
        }


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great-circle distance in kilometers between two points
    on the earth (specified in decimal degrees).
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of Earth in kilometers. Use 3956 for miles.
    return c * r
