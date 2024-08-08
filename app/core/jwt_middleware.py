from django.http import JsonResponse
from .utils import decode_jwt_token
from http import HTTPStatus
from django.urls import resolve
from .messages import Messages
from django.contrib.auth import (
    get_user_model
)


class JWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Get auth token from headers
            auth_header = request.headers.get('Authorization', '')

            # URL patterns that should skip authentication
            excluded_paths = ['/v1/users/login', '/v1/users/signup']

            # URL patterns for admin dashboard
            path_info = request.path_info
            resolved_path = resolve(path_info)

            # Check if current path is in excluded_paths or admin paths
            if (
                request.path_info in excluded_paths or
                (resolved_path and resolved_path.namespace == 'admin')
            ):
                return self.get_response(request)

            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                response = decode_jwt_token(token)

                # Check error
                if response.get('error'):
                    return JsonResponse(response, status=HTTPStatus.OK)

                # Get decoded data from token
                data = response.get('data')

                # Get user object only if is_active is True
                user = get_user_model().objects\
                    .filter(_id=data.get('_id'), is_active=True).first()

                # If user account was deactivated / soft delete
                if not user:
                    return JsonResponse({
                        'message': Messages.ERROR_ACCOUNT_INACTIVE,
                        'data': None,
                        'error': True,
                        'status': HTTPStatus.UNAUTHORIZED
                    }, status=HTTPStatus.OK)

                # Attach user info
                request.user_info = {
                    "_id": user._id,
                    "email": user.email,
                    "project_id": user.get_project_id(),
                    "is_staff": user.is_staff,
                }
                return self.get_response(request)

            else:
                return JsonResponse({
                    'message': Messages.ERROR_UNAUTHORIZED,
                    'data': None,
                    'error': True,
                    'status': HTTPStatus.UNAUTHORIZED
                }, status=HTTPStatus.OK)

        # General exception
        except Exception:
            return JsonResponse({
                'message': Messages.ERROR_UNAUTHORIZED,
                'data': None,
                'error': True,
                'status': HTTPStatus.UNAUTHORIZED
            }, status=HTTPStatus.OK)
