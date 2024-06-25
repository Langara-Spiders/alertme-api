"""
Views for the user API
"""
import os
import json
import uuid
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


client_id = {
    'web': 'GOOGLE_CLIENT_ID',
    'ios': 'GOOGLE_IOS_CLIENT_ID',
    'android': 'GOOGLE_ANDROID_CLIENT_ID',
}


class LoginView(View):
    def post(self, request):
        # get language support
        lng = request.lng
        # get platform info
        platform = request.GET.get('platform', 'web')
        try:
            data = json.loads(request.body)
            # check if OAuth token was valid
            token_info = id_token.verify_oauth2_token(
                data.get('token'),
                google_requests.Request(),
                os.environ.get(client_id.get(platform))
            )

        except ValueError as e:
            return JsonResponse({
                'message': MESSAGES[lng]
                .get('ERROR_MESSAGE_INVALID_TOKEN').format(e),
                'data': None,
                'error': True,
                'status': HTTPStatus.BAD_REQUEST
            }, status=HTTPStatus.OK)

        # check if user exists
        try:
            user = get_user_model()\
                .objects.get(email=token_info.get('email'), is_active=True)

        except get_user_model().DoesNotExist:
            return JsonResponse({
                'message': MESSAGES[lng]
                .get('ERROR_MESSAGE_UNAUTHORIZED'),
                'data': None,
                'error': True,
                'status': HTTPStatus.UNAUTHORIZED
            }, status=HTTPStatus.OK)

        # generate JWT token
        token = generate_jwt_token(
            _id=str(user._id),
            name=user.name,
            email=user.email,
            project_id=str(user.get_project_id()),
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
        # get platform info
        platform = request.GET.get('platform', 'web')
        try:
            data = json.loads(request.POST.get('user'))
            token = json.loads(request.POST.get('token'))
            picture = request.FILES.get('picture')

            # check if OAuth token was valid
            token_info = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                os.environ.get(client_id.get(platform))
            )

            # check if user exists
            try:
                user = get_user_model().objects\
                    .get(email=token_info.get('email'))
                # hardcoded the message for now
                return JsonResponse({
                    'message': "User already exists, please try to login",
                    'data': None,
                    'error': False,
                    'status': HTTPStatus.OK
                }, status=HTTPStatus.OK)

            except get_user_model().DoesNotExist:
                pass

            # create and return user
            user = get_user_model().objects.create(
                name=data.get('name'),
                email=token_info.get('email'),
                phone=data.get('phone'),
                address=data.get('address'),
                coordinate=data.get('coordinate'),
            )

            if picture:
                user.save(
                    f"{uuid.uuid4()}_{picture.name}",
                    picture,
                    save=True
                )

            # generate JWT token
            token = generate_jwt_token(
                _id=str(user._id),
                name=user.name,
                email=user.email,
                project_id=str(user.project_id._id),
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
            }, status=HTTPStatus.OK)

        except Exception as e:
            print(e)
            return JsonResponse({
                'message': MESSAGES[lng].get('ERROR_MESSAGE_CREATE_USER'),
                'data': None,
                'error': True,
                'status': HTTPStatus.INTERNAL_SERVER_ERROR
            }, status=HTTPStatus.OK)


class ProfileView(View):
    def get(self, request):
        lng = request.lng
        try:
            # get authorized user info
            user_info = request.user_info

            # get user
            user = get_user_model().objects\
                .get(_id=user_info.get('_id'), is_active=True)

            # send some default picture
            picture_url = ''

            if user.picture:
                picture_url = user.picture.url

            user_json = {
                'id': user._id,
                'name': user.name,
                'picture': picture_url,
                'email': user.email,
                'phone': user.phone,
                'project_id': user.get_project_id(),
                'address': user.address,
                'coordinate': user.coordinate,
            }

            return JsonResponse({
                'message': MESSAGES[lng].get('SUCCESS'),
                'data': {'user': user_json},
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
            }, status=HTTPStatus.OK)

    def post(self, request):
        lng = request.lng
        try:
            data = json.loads(request.POST.get('user'))
            picture = request.FILES.get('picture')

            # get authorized user info
            user_info = request.user_info

            user = get_user_model().objects\
                .filter(_id=user_info.get('_id'), is_active=True)

            user.update(
                name=data.get('name'),
                phone=data.get('phone'),
                address=data.get('address'),
                coordinate=data.get('coordinate')
            )

            # take the first user of queryset
            user = user[0]

            # if profile picture has to be updated
            if picture:
                user.picture\
                    .save(f"{uuid.uuid4()}_{picture.name}", picture, save=True)

            # generate JWT token
            token = generate_jwt_token(
                _id=str(user._id),
                name=user.name,
                email=user.email,
                project_id=str(user.get_project_id()),
                is_staff=user.is_staff,
            )

            # send some default picture
            picture_url = ''
            if user.picture:
                picture_url = user.picture.url

            user_json = {
                'id': user._id,
                'name': user.name,
                'picture': picture_url,
                'email': user.email,
                'phone': user.phone,
                'project_id': user.get_project_id(),
                'address': user.address,
                'coordinate': user.coordinate,
            }

            return JsonResponse({
                'message': MESSAGES[lng].get('SUCCESS_MESSAGE_UPDATE_USER'),
                'data': {
                    'token': token,
                    'user': user_json
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
            }, status=HTTPStatus.OK)
