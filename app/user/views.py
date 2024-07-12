"""
Views for the user API
"""
import os
import json
import uuid
from itertools import chain
from django.db.models import F, Window
from django.db.models.functions import Rank
from django.views import View
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.http import JsonResponse
from http import HTTPStatus
from django.contrib.gis.geos import Point
from django.contrib.auth import (
    get_user_model
)
from core.models import (
    Incident
)
from core.utils import generate_jwt_token
from core.messages import Messages

client_id = {
    'web': 'GOOGLE_CLIENT_ID',
    'ios': 'GOOGLE_IOS_CLIENT_ID',
    'android': 'GOOGLE_ANDROID_CLIENT_ID',
}


class LoginView(View):
    def post(self, request):
        # Get platform info
        platform = request.GET.get('platform', 'web')
        try:
            data = json.loads(request.body)
            # Check if OAuth token was valid
            token_info = id_token.verify_oauth2_token(
                data.get('token'),
                google_requests.Request(),
                os.environ.get(client_id.get(platform))
            )

        # Token decode error
        except ValueError as e:
            print(e)

            return JsonResponse({
                'message': Messages.JWT_INAVLID_TOKEN,
                'data': None,
                'error': True,
                'status': HTTPStatus.BAD_REQUEST
            }, status=HTTPStatus.OK)

        user = get_user_model().objects\
            .filter(email=token_info.get('email'), is_active=True).first()

        # Check if user exists
        if not user:
            return JsonResponse({
                'message': Messages.ERROR,
                'data': None,
                'error': True,
                'status': HTTPStatus.UNAUTHORIZED
            }, status=HTTPStatus.OK)

        # Generate JWT token
        token = generate_jwt_token(
            _id=str(user._id),
            name=user.name,
            email=user.email,
            project_id=str(user.get_project_id()),
            is_staff=user.is_staff,
        )

        return JsonResponse({
            'message': Messages.SUCCESS,
            'data': {'token': token},
            'error': False,
            'status': HTTPStatus.OK
        }, status=HTTPStatus.OK)


class SignupView(View):
    def post(self, request):
        # Get platform info
        platform = request.GET.get('platform', 'web')
        try:
            data = json.loads(request.POST.get('user'))
            token = json.loads(request.POST.get('token'))
            picture = request.FILES.get('picture')

            # Check if OAuth token was valid
            try:
                token_info = id_token.verify_oauth2_token(
                    token,
                    google_requests.Request(),
                    os.environ.get(client_id.get(platform))
                )

            # Token decode exception
            except ValueError as e:
                print(e)

                return JsonResponse({
                    'message': Messages.ERROR_TOKEN,
                    'data': None,
                    'error': True,
                    'status': HTTPStatus.BAD_REQUEST
                }, status=HTTPStatus.OK)

            user = get_user_model().objects\
                .filter(email=token_info.get('email')).first()

            # Check if user exists
            if user:
                return JsonResponse({
                    'message': Messages.ERROR_ACCOUNT_EXISTS,
                    'data': None,
                    'error': True,
                    'status': HTTPStatus.CONFLICT
                }, status=HTTPStatus.OK)

            # create and return user
            user = get_user_model().objects.create(
                name=data.get('name'),
                email=token_info.get('email'),
                phone=data.get('phone'),
                address=data.get('address'),
                coordinates=Point(
                    data.get('coordinate').get('lng'),
                    data.get('coordinate').get('lat'),
                    srid=4326,
                ),
                roaming_coordinates=Point(
                    data.get('coordinate').get('lng'),
                    data.get('coordinate').get('lat'),
                    srid=4326,
                ),
            )

            if picture:
                user.save(
                    f"{uuid.uuid4()}_{picture.name}",
                    picture,
                    save=True
                )

            # Generate JWT token
            token = generate_jwt_token(
                _id=str(user._id),
                name=user.name,
                email=user.email,
                project_id=str(user.project_id._id),
                is_staff=user.is_staff,
            )

            return JsonResponse({
                'message': Messages.SUCCESS,
                'data': {'token': token},
                'error': False,
                'status': HTTPStatus.CREATED
            }, status=HTTPStatus.CREATED)

        # General exception
        except Exception as e:
            print(e)
            return JsonResponse({
                'message': Messages.ERROR,
                'data': None,
                'error': True,
                'status': HTTPStatus.INTERNAL_SERVER_ERROR
            }, status=HTTPStatus.OK)


class ProfileView(View):
    def get(self, request):
        try:
            # Get authorized user info
            user_info = request.user_info

            # Get user
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
                'coordinates': {
                    'latitude': user.coordinates.y,
                    'longitude': user.coordinates.x,
                },
            }

            return JsonResponse({
                'message': Messages.SUCCESS,
                'data': {'user': user_json},
                'error': False,
                'status': HTTPStatus.OK
            }, status=HTTPStatus.OK)

        # General exception
        except Exception as e:
            print(e)

            return JsonResponse({
                'message': Messages.ERROR,
                'data': None,
                'error': True,
                'status': HTTPStatus.INTERNAL_SERVER_ERROR
            }, status=HTTPStatus.OK)

    def post(self, request):
        try:
            data = json.loads(request.POST.get('user'))
            picture = request.FILES.get('picture')
            # Get user info
            user_info = request.user_info

            user = get_user_model().objects\
                .filter(_id=user_info.get('_id'))

            user.update(
                name=data.get('name'),
                phone=data.get('phone'),
                address=data.get('address'),
                coordinates=Point(
                    data.get('coordinates').get('lng'),
                    data.get('coordinates').get('lat'),
                    srid=4326,
                ),
            )

            user = user.first()

            # If profile picture has to be updated
            if picture:
                user.picture\
                    .save(f"{uuid.uuid4()}_{picture.name}", picture, save=True)

            # Generate JWT token
            token = generate_jwt_token(
                _id=str(user._id),
                name=user.name,
                email=user.email,
                project_id=str(user.get_project_id()),
                is_staff=user.is_staff,
            )

            # Send some default picture
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
                'coordinates': {
                    'lat': user.coordinates.y,
                    'lng': user.coordinates.x,
                },
            }

            return JsonResponse({
                'message': Messages.SUCCESS,
                'data': {
                    'token': token,
                    'user': user_json
                },
                'error': False,
                'status': HTTPStatus.CREATED
            }, status=HTTPStatus.OK)

        # General exception
        except Exception as e:
            print(e)

            return JsonResponse({
                'message': Messages.ERROR,
                'data': None,
                'error': True,
                'status': HTTPStatus.INTERNAL_SERVER_ERROR
            }, status=HTTPStatus.OK)


class RewardView(View):
    def get(self, request):
        try:
            # Get top three users based on points
            top_users_qs = get_user_model().objects\
                .order_by('-points', 'name')[:3]
            user_info = request.user_info

            top_users = []
            for user in top_users_qs:
                top_users.append({
                    'id': user._id,
                    'name': user.name,
                    'points': user.points,
                    'picture': user.picture.url if user.picture else ''
                })

            user_incidents_count = Incident.objects\
                .filter(user___id=user_info.get('_id'), is_active=True)\
                .count()

            user = get_user_model().objects\
                .filter(_id=user_info.get('_id'), is_active=True).first()

            user_details = {
                'id': user._id,
                'name': user.name,
                'picture': user.picture.url if user.picture else '',
                'points': user.points,
                'total_issues': user_incidents_count,
            }

            # Leaderboard
            user_rank = get_user_model().objects.annotate(
                rank=Window(
                    expression=Rank(),
                    order_by=F('points').desc()
                )
            ).get(_id=user_info.get('_id'))

            above_users = get_user_model().objects.annotate(
                rank=Window(
                    expression=Rank(),
                    order_by=F('points').desc()
                )
            ).filter(points__gt=user_rank.points).order_by('-points')[:3]

            below_users = get_user_model().objects.annotate(
                rank=Window(
                    expression=Rank(),
                    order_by=F('points').desc()
                )
            ).filter(points__lt=user_rank.points).order_by('-points')[:20]

            combined_users = list(chain(above_users, [user_rank], below_users))

            leaderboard = []
            for user in combined_users:
                leaderboard.append({
                    '_id': user._id,
                    'picture': user.picture.url if user.picture else '',
                    'name': user.name,
                    'points': user.points,
                })

            return JsonResponse({
                'message': Messages.SUCCESS,
                'data': {
                    'user_details': user_details,
                    'top_users': top_users,
                    'leaderboard': leaderboard
                },
                'error': True,
                'status': HTTPStatus.OK
            }, status=HTTPStatus.OK)

        except Exception as e:
            print(e)
            return JsonResponse({
                'message': Messages.ERROR,
                'data': None,
                'error': True,
                'status': HTTPStatus.INTERNAL_SERVER_ERROR
            }, status=HTTPStatus.OK)
