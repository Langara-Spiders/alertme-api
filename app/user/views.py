"""
Views for the user API
"""
import os
import json
from django.views import View
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.http import JsonResponse
from http import HTTPStatus
from django.contrib.auth import (
    get_user_model
)
from core.utils import generate_jwt_token
from .messages import MESSAGES


class LoginView(View):
    def post(self, request):
        lng = request.lng

        try:
            data = json.loads(request.body)
            # Check if OAuth token was valid
            token_info = id_token.verify_oauth2_token(
                data.get('token'),
                google_requests.Request(),
                os.environ.get('GOOGLE_CLIENT_ID')
            )

        except ValueError as e:
            return JsonResponse({
                'message': MESSAGES[lng]
                .get('ERROR_MESSAGE_INVALID_TOKEN').format(e),
                'data': None,
                'error': True,
                'status': HTTPStatus.BAD_REQUEST
            }, status=HTTPStatus.BAD_REQUEST)

        # Check if user exists
        try:
            user = get_user_model().objects.get(email=token_info.get('email'))

        except get_user_model().DoesNotExist:
            return JsonResponse({
                'message': MESSAGES[lng]
                .get('ERROR_MESSAGE_UNAUTHORIZED'),
                'data': None,
                'error': True,
                'status': HTTPStatus.UNAUTHORIZED
            }, status=HTTPStatus.UNAUTHORIZED)

        # Generate JWT token
        token = generate_jwt_token(
            _id=str(user._id),
            name=user.name,
            email=user.email,
            project_id=user.project_id,
            is_staff=user.is_staff,
        )

        return JsonResponse({
            'message': MESSAGES[lng].get('SUCCESS_MESSAGE_LOGIN'),
            'data': {'token': token},
            'error': False,
            'status': HTTPStatus.OK
        }, status=HTTPStatus.OK)


class SignupView(View):
    def post(self, request):
        lng = request.lng

        try:
            data = json.loads(request.body)

            # Check if OAuth token was valid
            token_info = id_token.verify_oauth2_token(
                data.get('token'),
                google_requests.Request(),
                os.environ.get('GOOGLE_CLIENT_ID')
            )

            data.pop('token')

            # Create and return user
            user = get_user_model().objects.create(
                **data,
                email=token_info.get('email')
            )

            # Generate JWT token
            token = generate_jwt_token(
                _id=str(user._id),
                name=user.name,
                email=user.email,
                project_id=user.project_id,
                is_staff=user.is_staff,
            )

            return JsonResponse({
                'message': MESSAGES[lng].get('SUCCESS_MESSAGE_CREATE_USER'),
                'data': {'token': token},
                'error': False,
                'status': HTTPStatus.CREATED
            }, status=HTTPStatus.CREATED)

        except ValueError as e:
            return JsonResponse({
                'message': MESSAGES[lng]
                .get('ERROR_MESSAGE_INVALID_TOKEN').format(e),
                'data': None,
                'error': True,
                'status': HTTPStatus.BAD_REQUEST
            }, status=HTTPStatus.BAD_REQUEST)

        except Exception as e:
            print(e)

        return JsonResponse({
            'message': MESSAGES[lng].get('ERROR_MESSAGE_CREATE_USER'),
            'data': None,
            'error': True,
            'status': HTTPStatus.INTERNAL_SERVER_ERROR
        }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


class ProfileView(View):
    def get(self, request):
        lng = request.lng

        try:
            # Get authorized user info
            user_info = request.user_info

            # Get user
            user = get_user_model().objects.get(_id=user_info.get('_id'))

            return JsonResponse({
                'message': MESSAGES[lng].get('SUCCESS'),
                'data': {
                    'user': {
                        'picture': user.picture,
                        'name': user.name,
                        'address': user.address,
                        'coordinate': user.coordinate,
                        'phone': user.phone
                    }
                },
                'error': False,
                'status': HTTPStatus.OK
            }, status=HTTPStatus.OK)

        except Exception as e:
            print(e)

        return JsonResponse({
            'message': MESSAGES[lng].get('ERROR'),
            'data': None,
            'error': True,
            'status': HTTPStatus.INTERNAL_SERVER_ERROR
        }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def put(self, request):
        lng = request.headers.get('Accept-Language', 'en-CA')

        try:
            data = json.loads(request.body)
            # Get authorized user info
            user_info = request.user_info

            # Update and return user
            get_user_model().objects.filter(
                _id=user_info.get('_id')).update(**data)
            user = get_user_model().objects.get(_id=user_info.get('_id'))

            # Generate JWT token
            token = generate_jwt_token(
                _id=str(user._id),
                name=user.name,
                email=user.email,
                project_id=user.project_id,
                is_staff=user.is_staff,
            )

            return JsonResponse({
                'message': MESSAGES[lng].get('SUCCESS_MESSAGE_UPDATE_USER'),
                'data': {
                    'token': token,
                    'user': {
                        'picture': user.picture,
                        'name': user.name,
                        'address': user.address,
                        'coordinate': user.coordinate,
                        'phone': user.phone
                    }
                },
                'error': False,
                'status': HTTPStatus.OK
            }, status=HTTPStatus.OK)

        except Exception as e:
            print(e)

        return JsonResponse({
            'message': MESSAGES[lng].get('ERROR_MESSAGE_UPDATE_USER'),
            'data': None,
            'error': True,
            'status': HTTPStatus.INTERNAL_SERVER_ERROR
        }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
