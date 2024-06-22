from django.http import JsonResponse
from .utils import decode_jwt_token
from http import HTTPStatus
from django.urls import resolve
from .messages import MESSAGES


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get('Authorization', '')
        lng = request.headers.get('Accept-Language', 'en-CA')

        # URL patterns that should skip authentication
        excluded_paths = ['/api/users/login', '/api/users/signup']

        # URL patterns for admin dashboard
        path_info = request.path_info
        resolved_path = resolve(path_info)

        # Attach user language
        request.lng = lng

        # Check if current path is in excluded_paths or admin paths
        if (
            request.path_info in excluded_paths or
            (resolved_path and resolved_path.namespace == 'admin')
           ):
            return self.get_response(request)

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            response = decode_jwt_token(token, lng)

            # Check error
            if response.get('error'):
                return JsonResponse(response, status=response.get('status'))

            data = response.get('data')
            # Attach user info
            request.user_info = {
                "_id": data.get('_id'),
                "email": data.get('email'),
                "project_id": data.get('project_id'),
                "is_staff": data.get('is_staff'),
            }
            return self.get_response(request)

        return JsonResponse({
                'message': MESSAGES[lng].get('ERROR_MESSAGE_INVALID_JWT'),
                'data': None,
                'error': True,
                'status': HTTPStatus.UNAUTHORIZED
            },
            status=HTTPStatus.UNAUTHORIZED
        )
