# Replace with your User model import
from core.models import Incident
from django.contrib.auth import (
    get_user_model
)
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
import google.auth.transport
import json
from django.forms.models import model_to_dict
from core.utils import upload_file_to_s3
from core.models import IncidentImage, Incident
from core.models import IncidentCategory
from django.shortcuts import get_object_or_404


# API Logic for Incident Category
class IncidentCategoryView(View):
    def get(self, request):
        lng = request.headers.get('Accept-Language', 'en-CA')
        try:
            categories = IncidentCategory.objects.all()
            # Change this to for loop readable
            category_list = [{'id': category._id,
                              'name': category.name, }
                             for category in categories]
            return JsonResponse({'categories': category_list})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# API Logic Incident
class IncidentView(View):

    # API Logic for retrieving single incident
    def get(self, request):
        # return JsonResponse({'message': 'Hello single report'})
        try:
            incident_id = request.params.get('id')
            incident = get_object_or_404(Incident, _id=incident_id)
            single_incident = {
                'id': str(incident._id),
                'user_id': str(incident.user_id._id),
                'user_reported': incident.user_id.username,
                'incident_category_id': str(incident.incident_category_id._id),
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
                'voters': incident.voters
            }
            return JsonResponse(single_incident, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # ***********  API logic for reporting an incident  *************************
    def post(self, request):
        lng = request.headers.get('Accept-Language', 'en-CA')
    # try:
        # Extract JSON data from POST

        print("This is json data")
        print(request.POST['json_data'])
        data = json.loads(request.POST['json_data'])

        uploaded_images = request.FILES.getlist('images')

        print(data)

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

        print(user_id)

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

        print(incident)

        # uploaded_images = request.FILES.getlist('images')

        for image in uploaded_images:
            # Upload image to S3 and get the URL
            file_url = upload_file_to_s3(image)

            # Create IncidentImage object and link to Incident
            incident_image = IncidentImage.objects.create(
                image=file_url
            )
            incident.images.add(incident_image)

        # Return success response
        return JsonResponse({'message': 'Incident reported successfully'}, status=201)

        # except Exception as e:
        #     return JsonResponse({'error': str(e)}, status=500)

    # API Logic for Voting an Incident

    def put(self, request):
        try:
            incident_id = request.params.get('id')
            user_info = request.user_info
            incident = get_object_or_404(Incident, _id=incident_id)

            if incident.voters.filter(id=user_info._id).exists():
                return JsonResponse({
                    'already_voted': True
                }, status=200)

            # Add the user to the voters of the incident
            incident.voters.add(user_info._id)

            # Increment the upvote_count of the incident
            incident.upvote_count += 1
            incident.save()

            return JsonResponse({
                'message': 'Your vote has been recorded.',
                'voted': True
            }, status=200)

        except Incident.DoesNotExist:
            return JsonResponse({
                'error': f'Incident with ID {incident_id} does not exist.'
            }, status=404)

        except Exception as e:
            return JsonResponse({
                'error': f'An error occurred while processing your vote: {str(e)}'
            }, status=500)
