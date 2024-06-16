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
