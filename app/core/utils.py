import os
import jwt
from django.conf import settings
from datetime import (
    timedelta,
    datetime,
    timezone
)
from http import HTTPStatus
from .messages import Messages
from .models import NotificationList
from django.contrib.auth import (
    get_user_model
)
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance


# Helper to create single notification
def create_notification(user, reported_user, incident, title):
    notification = NotificationList.objects.create(
        type='SINGLE',
        user=user,
        incident=incident,
        coordinates=incident.coordinates,
        title=title,
        subject=incident.subject,
        description=incident.description,
    )

    reported_user.notification.update({
        str(notification._id): {
            'incident_id': str(incident._id),
            'title': title,
            'subject': incident.subject,
            'description': incident.description,
            'created_at': notification.created_at,
            'read_flag': False
        }
    })

    reported_user.save()


# Helper to create 1 to many notification
def create_notification_stream(user, incident, title):
    # Create a notification
    notification = NotificationList.objects.create(
        type='BROADCAST',
        user=user,
        incident=incident,
        coordinates=incident.coordinates,
        title=title,
        subject=incident.subject,
        description=incident.description,
    )

    # Find nearby users to the incident within 50Km range for testing, reduce to 5Km
    nearby_users_qs = get_user_model().objects.filter(
        roaming_coordinates__distance_lte=(incident.coordinates, D(km=50))
    ).annotate(
        distance=Distance('coordinates', incident.coordinates)
    ).order_by('distance')

    # For each nearby user within 5Km range
    for nearby_user in nearby_users_qs:
        user_to_incident_distance = user.roaming_coordinates\
            .distance(incident.coordinates)
        # Do not notify the user who reported the incident and
        # Notify only user within the alert radius
        # that they set if incident comes within that radius
        if user._id != nearby_user._id and nearby_user.alert_radius >= user_to_incident_distance:
            nearby_user.notification.update({
                str(notification._id): {
                    'incident_id': str(incident._id),
                    'title': title,
                    'subject': incident.subject,
                    'description': incident.description,
                    'created_at': notification.created_at,
                    'read_flag': False
                }
            })

            nearby_user.save()


# Helper to generate JWT token
def generate_jwt_token(**kwargs):
    payload = {
        **kwargs,
        'exp': datetime.now(timezone.utc) +
        timedelta(days=int(os.environ.get('JWT_EXP_TIME', 1))),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=os.environ.get('JWT_ALGORITHM')
    )


# Helper to decode JWT token
def decode_jwt_token(token):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[os.environ.get('JWT_ALGORITHM')]
        )

        return {
            'message': Messages.JWT_SUCCESS,
            'data': payload,
            'error': False,
            'status': HTTPStatus.OK
        }

    except jwt.ExpiredSignatureError:
        return {
            'message': Messages.JWT_EXPIRED_TOKEN,
            'data': None,
            'error': True,
            'status': HTTPStatus.UNAUTHORIZED
        }

    except jwt.InvalidTokenError:
        return {
            'message': Messages.JWT_INAVLID_TOKEN,
            'data': None,
            'error': True,
            'status': HTTPStatus.UNAUTHORIZED
        }


# Helper to format incident object to JSON
def format_incident_data(incident, current_user_info=None):
    images_db_list = incident.images.all()
    voters_db_list = incident.voters.all()[:3]

    current_user_has_voted = False
    # Check if current user is in the voters list
    if current_user_info:
        current_user_has_voted = incident.voters\
                .filter(_id=current_user_info.get('_id')).exists()

    user = incident.user
    project = incident.project
    images = []
    voters = []

    for incident_image in images_db_list:
        images.append(incident_image.image.url)

    for voter in voters_db_list:
        voters.append({
            'id': str(voter._id),
            'name': voter.name,
            'picture': voter.picture.url if voter.picture else ''
        })

    incident = {
        'id': str(incident._id),
        'project_id': str(project._id) if project else '',
        'project_name': str(project.name) if project else '',
        'user_id': str(user._id),
        'user_name': str(user.name),
        'user_picture': user.picture.url if user.picture else '',
        'category_id': str(incident.incident_category._id),
        'category_name': incident.incident_category.name,
        'category_icon': incident.incident_category.icon.url
        if incident.incident_category.icon else '',
        'subject': incident.subject,
        'description': incident.description,
        'coordinates': {
            'lat': incident.coordinates.y,
            'lng': incident.coordinates.x,
        },
        'address': incident.address,
        'upvote_count': incident.upvote_count,
        'current_user_has_voted': current_user_has_voted,
        'report_count': incident.report_count,
        'status': incident.status,
        'is_accepted_by_org': incident.is_accepted_by_org,
        'is_internal_for_org': incident.is_internal_for_org,
        'is_active': incident.is_active,
        'reported_by': incident.reported_by,
        'created_at': incident.created_at,
        'updated_at': incident.updated_at,
        'voters': voters,
        'images': images,
    }

    return incident
