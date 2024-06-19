# Replace with your User model import
from django.contrib.auth import (
    get_user_model
)
from django.http import JsonResponse
from django.views import View
import json
from core.utils import upload_file_to_s3
from core.models import IncidentImage, Incident
from core.models import IncidentCategory
from django.shortcuts import get_object_or_404
from http import HTTPStatus
from .messages import MESSAGES


# API Logic for Incident Category
class IncidentCategoryView(View):
    def get(self, request):
        lng = request.lng
        try:
            categories = IncidentCategory.objects.all()
            category_list = []
            for category in categories:
                category_list.append({
                    'id': category._id,
                    'name': category.name,
                })
            return JsonResponse({
                'message': MESSAGES[lng].
                get('SUCCESS_MESSAGE_FOR_INCIDENT_CATEGORY'),
                'data': category_list,
                'error': False,
                'status': HTTPStatus.OK
            }, status=HTTPStatus.OK)
        except Exception as e:
            return JsonResponse({
                'message': MESSAGES[lng]
                .get('ERROR_MESSAGE_INVALID_TOKEN').format(str(e)),
                'data': None,
                'error': True,
                'status': HTTPStatus.BAD_REQUEST
            }, status=HTTPStatus.BAD_REQUEST)


# API Logic Incident reports
class IncidentView(View):
    # Code logic to retrieve incidents
    def get(self, request):
        lng = request.lng
        try:
            incident_id = request.GET.get('id')
            if not incident_id:
                raise ValueError("Incident ID is required")

            incident = get_object_or_404(Incident, _id=incident_id)
            voters_list = list(incident.voters.values_list('_id', flat=True))
            images_list = list(incident.images.
                               values_list('image', flat=True))

            single_incident = {
                'id': str(incident._id),
                'user_id': str(incident.user_id._id),
                'user_reported': str(incident.user_id.name),
                'incident_category_id':
                    str(incident.incident_category_id._id),
                'incident_category_name': incident.incident_category_id.name,
                'subject': incident.subject,
                'description': incident.description,
                'coordinate': incident.coordinate,
                'upvote_count': incident.upvote_count,
                'report_count': incident.report_count,
                'status': incident.status,
                'is_accepted_by_org': incident.is_accepted_by_org,
                'is_internal_for_org': incident.is_internal_for_org,
                'is_active': incident.is_active,
                'reported_by': incident.reported_by,
                'created_at': incident.created_at.isoformat(),
                'updated_at': incident.updated_at.isoformat(),
                'voters': voters_list,
                'images': images_list
            }
            return JsonResponse({
                'message': MESSAGES[lng].
                get('SUCCESS_MESSAGE_TO_RETRIEVE_INCIDENT'),
                'data': single_incident,
                'error': False,
                'status': HTTPStatus.OK
            }, status=HTTPStatus.OK)
        except ValueError as ve:
            return JsonResponse({
                'message': MESSAGES[lng].get('ERROR_MESSAGE_INVALID_TOKEN').
                format(str(ve)),
                'data': None,
                'error': True,
                'status': HTTPStatus.BAD_REQUEST
            }, status=HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return JsonResponse({
                'message': MESSAGES[lng].get('ERROR_MESSAGE_INVALID_TOKEN').
                format(str(e)),
                'data': None,
                'error': True,
                'status': HTTPStatus.INTERNAL_SERVER_ERROR
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    # Code logic to report an incident
    def post(self, request):
        lng = request.lng
        try:
            data = json.loads(request.POST['json_data'])

            uploaded_images = request.FILES.getlist('images')

            user_info = request.user_info
            incident_category_id = data.get('incident_category_id')
            subject = data.get('subject')
            description = data.get('description')
            coordinate = data.get('coordinate')
            status = data.get('status')
            is_active = data.get('is_active', True)
            reported_by = data.get('reported_by')
            is_internal_for_org = data.get('is_internal_for_org', False)

            user_id = get_user_model().objects.get(_id=user_info.get('_id'))
            incident_category = IncidentCategory.objects.get(
                _id=incident_category_id)

            incident = Incident.objects.create(
                user_id=user_id,
                incident_category_id=incident_category,
                subject=subject,
                description=description,
                coordinate=coordinate,
                status=status,
                is_active=is_active,
                reported_by=reported_by,
                is_internal_for_org=is_internal_for_org
            )

            for image in uploaded_images:
                # Upload image to S3 and get the URL
                file_url = upload_file_to_s3(image)

                # Create IncidentImage object and link to Incident
                incident_image = IncidentImage.objects.create(
                    image=file_url
                )
                incident.images.add(incident_image)

            # Return success response
            return JsonResponse({
                'message': MESSAGES[lng].get('SUCCESS_REPORT_MESSAGE'),
                'data': {'incident_id': str(incident._id)},
                'error': False,
                'status': HTTPStatus.CREATED
            }, status=HTTPStatus.CREATED)
        except json.JSONDecodeError as jde:
            return JsonResponse({
                'message': MESSAGES[lng].get('ERROR_MESSAGE_INVALID_DATA').
                format(str(jde)),
                'data': None,
                'error': True,
                'status': HTTPStatus.BAD_REQUEST
            }, status=HTTPStatus.BAD_REQUEST)
        except get_user_model().DoesNotExist:
            return JsonResponse({
                'message': MESSAGES[lng].get('ERROR_MESSAGE_NOT_FOUND').
                format('User'),
                'data': None,
                'error': True,
                'status': HTTPStatus.NOT_FOUND
            }, status=HTTPStatus.NOT_FOUND)
        except IncidentCategory.DoesNotExist:
            return JsonResponse({
                'message': MESSAGES[lng].get('ERROR_MESSAGE_NOT_FOUND').
                format('Incident Category'),
                'data': None,
                'error': True,
                'status': HTTPStatus.NOT_FOUND
            }, status=HTTPStatus.NOT_FOUND)
        except Exception as e:
            return JsonResponse({
                'message': MESSAGES[lng].get('ERROR_MESSAGE_INVALID_TOKEN').
                format(str(e)),
                'data': None,
                'error': True,
                'status': HTTPStatus.INTERNAL_SERVER_ERROR
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    # Code Logic for Voting an Incident
    def put(self, request):
        lng = request.lng
        try:
            incident_id = request.GET.get('id')
            if not incident_id:
                return JsonResponse({
                    'message': MESSAGES[lng].get('ERROR_MESSAGE_NOT_FOUND').
                    format('Incident ID is required'),
                    'data': None,
                    'error': True,
                    'status': HTTPStatus.BAD_REQUEST
                }, status=HTTPStatus.BAD_REQUEST)

            user_info = request.user_info
            current_user_id = user_info.get('_id')
            incident = get_object_or_404(Incident, _id=incident_id)

            if incident.voters.filter(_id=current_user_id).exists():
                return JsonResponse({
                    'message': MESSAGES[lng].get('ALREADY_VOTED_MESSAGE'),
                    'already_voted': True,
                    'error': False,
                    'status': HTTPStatus.OK
                }, status=HTTPStatus.OK)

            # Add the user to the voters of the incident
            incident.voters.add(current_user_id)

            # Increment the upvote_count of the incident
            incident.upvote_count += 1
            incident.save()

            return JsonResponse({
                'message': MESSAGES[lng].get('SUCCESS_VOTE_MESSAGE'),
                'voted': True,
                'error': False,
                'status': HTTPStatus.OK
            }, status=HTTPStatus.OK)

        except Incident.DoesNotExist:
            return JsonResponse({
                'message': MESSAGES[lng].get('ERROR_MESSAGE_NOT_FOUND').
                format(f'Incident with ID {incident_id} does not exist'),
                'data': None,
                'error': True,
                'status': HTTPStatus.NOT_FOUND
            }, status=HTTPStatus.NOT_FOUND)

        except Exception as e:
            return JsonResponse({
                'message': MESSAGES[lng].get('ERROR_MESSAGE_INVALID_TOKEN').
                format(str(e)),
                'data': None,
                'error': True,
                'status': HTTPStatus.INTERNAL_SERVER_ERROR
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    # Code Logic for Deleting an Incident
    def delete(self, request):
        lng = request.lng
        incident_id = request.GET.get('id')
        if not incident_id:
            return JsonResponse({
                'message': MESSAGES[lng].get('ERROR_MESSAGE_NOT_FOUND').
                format('Incident ID is required'),
                'data': None,
                'error': True,
                'status': HTTPStatus.BAD_REQUEST
            }, status=HTTPStatus.BAD_REQUEST)

        incident = get_object_or_404(Incident, _id=incident_id)

        # Delete related images
        for image in incident.images.all():
            incident.images.remove(image)
            image.delete()

        incident.voters.clear()

        # Delete the incident itself
        incident.delete()

        return JsonResponse({
            'message': MESSAGES[lng].get('SUCCESS_MESSAGE_INCIDENT_DELETED'),
            'error': False,
            'status': HTTPStatus.OK
        }, status=HTTPStatus.OK)
