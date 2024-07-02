# Replace with your User model import
import json
import uuid
from django.contrib.auth import (
    get_user_model
)
from django.http import JsonResponse
from django.views import View
from core.models import (
    Incident,
    IncidentCategory,
    Project,
    IncidentImage,
)
from http import HTTPStatus
from .messages import MESSAGES
from core.utils import haversine
from core.utils import format_incident_data


class IncidentCategoryView(View):
    def get(self, request):
        lng = request.lng

        try:
            categories = IncidentCategory.objects.all()

            category_list = []
            for category in categories:
                category_icon_url = ''
                if category.icon:
                    category_icon_url = category.icon.url

                category_list.append({
                    'id': category._id,
                    'name': category.name,
                    'icon': category_icon_url,
                    'decription': category.description,
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
                .get('ERROR_MESSAGE_FOR_INCIDENT_CATEGORY').format(str(e)),
                'data': None,
                'error': True,
                'status': HTTPStatus.BAD_REQUEST
            }, status=HTTPStatus.OK)


class IncidentUpvoteView(View):
    def put(self, request):
        lng = request.lng
        try:
            incident_id = request.GET.get('id')
            user_info = request.user_info
            user_id = user_info.get('_id')

            user = get_user_model().objects.get(_id=user_id)
            incident = Incident.objects.get(_id=incident_id)

            if incident.voters.filter(_id=user._id):
                return JsonResponse({
                    'message': 'Already Upvoted Issue',
                    'data': None,
                    'error': True,
                    'status': HTTPStatus.OK
                }, status=HTTPStatus.OK)

            # add the user to the voters of the incident
            incident.voters.add(user)

            # increment the upvote_count of the incident
            incident.upvote_count += 1

            # upvote reached threshold
            if incident.upvote_count == 3:
                incident.status = 'PENDING'

            incident.save()

            incident = format_incident_data(incident)

            return JsonResponse({
                'message': MESSAGES[lng].get('SUCCESS_VOTE_MESSAGE'),
                'data': incident,
                'error': False,
                'status': HTTPStatus.OK
            }, status=HTTPStatus.OK)

        except Exception as e:
            print(e)
            return JsonResponse({
                'message': MESSAGES[lng].get('ERROR_VOTE_MESSAGE').
                format(str(e)),
                'data': None,
                'error': True,
                'status': HTTPStatus.INTERNAL_SERVER_ERROR
            }, status=HTTPStatus.OK)


class IncidentDeleteView(View):
    def delete(self, request):
        lng = request.lng
        incident_id = request.GET.get('id')
        incident = Incident.objects.get(_id=incident_id)

        if incident.status == 'ACTIVE':
            incident.is_active = False
            incident.save()
            incident = format_incident_data(incident)

            return JsonResponse({
                'message': MESSAGES[lng]
                .get('SUCCESS_MESSAGE_INCIDENT_DELETED'),
                'error': False,
                'data': incident,
                'status': HTTPStatus.OK
            }, status=HTTPStatus.OK)

        else:
            return JsonResponse({
                'message': MESSAGES[lng].get('SUCCESS'),
                'error': True,
                'data': None,
                'status': HTTPStatus.OK
            }, status=HTTPStatus.OK)


class IncidentReportView(View):
    def get(self, request):
        lng = request.lng

        try:
            incident_id = request.GET.get('id')
            user_lat = float(request.GET.get("lat"))
            user_lng = float(request.GET.get("lng"))

            incident = Incident.objects.get(
                _id=incident_id,
                is_active=True
            )

            incident_lat = float(incident.coordinate.get('lat'))
            incident_lng = float(incident.coordinate.get('lng'))

            distance = haversine(
                user_lat,
                user_lng,
                incident_lat,
                incident_lng
            )

            incident = format_incident_data(incident, distance)

            return JsonResponse({
                "message": MESSAGES[lng].get(
                    "SUCCESS"
                ),
                "data": incident,
                "error": False,
                "status": HTTPStatus.OK,
            }, status=HTTPStatus.OK)

        except Exception as e:
            print(e)
            return JsonResponse({
                "message": MESSAGES[lng].get(
                    "ERROR"
                ),
                "data": None,
                "error": False,
                "status": HTTPStatus.INTERNAL_SERVER_ERROR,
            }, status=HTTPStatus.OK)

    def post(self, request):
        lng = request.lng
        user_info = request.user_info

        try:
            report = json.loads(request.POST.get('report'))
            category_id = report.get('category_id')
            subject = report.get('subject')
            description = report.get('description')
            coordinate = report.get('coordinate')
            incident_lat = float(coordinate.get('lat'))
            incident_lng = float(coordinate.get('lng'))
            address = report.get('address')
            is_internal_for_org = report.get('is_internal_for_org', False)
            pictures = request.FILES.getlist('pictures')[:3]
            nearest_project = ''

            user = get_user_model().objects\
                .get(_id=user_info.get('_id'), is_active=True)

            incident_category = IncidentCategory.objects.get(_id=category_id)

            # check if user has a project
            if is_internal_for_org and not user_info.get('is_staff'):
                is_internal_for_org = False

            # site user is reporting issue
            if user_info.get('is_staff') and user_info.get('project_id'):
                # map the project
                nearest_project = Project.objects\
                    .get(_id=user_info.get('project_id'))
            else:
                # find nearest project for the given incident coordinate
                projects = Project.objects.all().filter(is_active=True)
                nearest_project = projects.first()
                nearest_project_coordinate = nearest_project.coordinate
                nearest_project_distance = haversine(
                    incident_lat,
                    incident_lng,
                    float(nearest_project_coordinate.get('lat')),
                    float(nearest_project_coordinate.get('lng'))
                )

                for project in projects:
                    project_lat = float(project.coordinate.get('lat'))
                    project_lng = float(project.coordinate.get('lng'))

                    distance = haversine(
                        incident_lat,
                        incident_lng,
                        project_lat,
                        project_lng
                    )

                    if nearest_project_distance > distance:
                        nearest_project_distance = distance
                        nearest_project = project

            incident = Incident.objects.create(
                user=user,
                project=nearest_project,
                incident_category=incident_category,
                subject=subject,
                description=description,
                coordinate=coordinate,
                address=address,
                is_internal_for_org=is_internal_for_org
            )

            # loop over images if present
            images = []
            for picture in pictures:
                incident_image = IncidentImage()
                incident_image.image = picture
                incident_image.image.name = f'{uuid.uuid4()}_{picture.name}'

                incident_image.save()
                images.append(incident_image)

            # if images are present
            if images:
                incident.images.set(images)

            incident = format_incident_data(incident)

            return JsonResponse({
                "message": MESSAGES[lng].get(
                    "SUCCESS_MESSAGE_FOR_NEARBY_INCIDENTS"
                ),
                "data": incident,
                "error": False,
                "status": HTTPStatus.OK,
            }, status=HTTPStatus.OK)

        except Exception as e:
            print(e)
            JsonResponse({
                "message": MESSAGES[lng].get(
                    "ERROR"
                ),
                "data": None,
                "error": False,
                "status": HTTPStatus.INTERNAL_SERVER_ERROR,
            }, status=HTTPStatus.OK)


class IncidentNearbyView(View):
    def get(self, request):
        lng = request.lng

        try:
            filter_by = request.GET.get('filter_by')
            user_lat = float(request.GET.get("lat"))
            user_lng = float(request.GET.get("lng"))
            radius = float(request.GET.get("r"))

            incidents = Incident.objects.all()\
                .filter(is_active=True)

            if filter_by == 'ORG':
                incidents = incidents.filter(reported_by='ORG')
            elif filter_by == 'USER':
                incidents = incidents.filter(reported_by='USER')

            nearby_incidents = []
            for incident in incidents:
                incident_lat = incident.coordinate.get('lat')
                incident_lng = incident.coordinate.get('lng')

                distance = haversine(
                    user_lng, user_lat, incident_lng, incident_lat
                )
                if distance <= radius:
                    nearby_incidents\
                        .append(format_incident_data(incident, distance))

            return JsonResponse({
                "message": MESSAGES[lng].get(
                    "SUCCESS_MESSAGE_FOR_NEARBY_INCIDENTS"
                ),
                "data": nearby_incidents,
                "error": False,
                "status": HTTPStatus.OK,
            }, status=HTTPStatus.OK)

        except Exception as e:
            return JsonResponse({
                "message": MESSAGES[lng]
                .get("ERROR_MESSAGE_FOR_NEARBY_INCIDENTS")
                .format(str(e)),
                "data": None,
                "error": True,
                "status": HTTPStatus.INTERNAL_SERVER_ERROR,
            }, status=HTTPStatus.OK)


class IncidentUserView(View):
    def get(self, request):
        lng = request.lng
        user_info = request.user_info

        try:
            filter_by = request.GET.get('filter_by', None)
            user_lat = float(request.GET.get("lat"))
            user_lng = float(request.GET.get("lng"))

            incidents = Incident.objects.all()\
                .filter(user___id=user_info.get('_id'))

            if filter_by is not None:
                incidents = incidents.filter(status=filter_by)

            user_incidents = []
            for incident in incidents:
                incident_lat = incident.coordinate.get('lat')
                incident_lng = incident.coordinate.get('lng')

                distance = haversine(
                    user_lng, user_lat, incident_lng, incident_lat
                )

                user_incidents\
                    .append(format_incident_data(incident, distance))

            return JsonResponse({
                "message": MESSAGES[lng].get(
                    "SUCCESS_MESSAGE_FOR_NEARBY_INCIDENTS"
                ),
                "data": user_incidents,
                "error": False,
                "status": HTTPStatus.OK,
            }, status=HTTPStatus.OK)

        except Exception as e:
            return JsonResponse({
                "message": MESSAGES[lng]
                .get("ERROR_MESSAGE_FOR_NEARBY_INCIDENTS")
                .format(str(e)),
                "data": None,
                "error": True,
                "status": HTTPStatus.INTERNAL_SERVER_ERROR,
            }, status=HTTPStatus.OK)


class IncidentSiteView(View):
    def get(self, request):
        lng = request.lng
        user_info = request.user_info

        try:
            filter_by = request.GET.get('filter_by', None)
            project = Project.objects\
                .get(_id=user_info.get('project_id'))

            incidents = Incident.objects\
                .filter(
                    project___id=project._id,
                    is_active=True
                )

            if filter_by is not None:
                incidents = incidents.filter(status=filter_by)

            project_lat = float(project.coordinate.get('lat'))
            project_lng = float(project.coordinate.get('lng'))

            site_incidents = []
            for incident in incidents:
                incident_lat = float(incident.coordinate.get('lat'))
                incident_lng = float(incident.coordinate.get('lng'))

                distance = haversine(
                    incident_lat,
                    incident_lng,
                    project_lat,
                    project_lng
                )

                site_incidents.append(
                    format_incident_data(incident, distance)
                )

            return JsonResponse({
                'message': MESSAGES[lng].get(
                    'SUCCESS_MESSAGE_FOR_INCIDENT_SITE'),
                'data': site_incidents,
                'error': False,
                'status': HTTPStatus.OK
            }, status=HTTPStatus.OK)

        except Exception as e:
            print(e)
            return JsonResponse({
                'message': MESSAGES[lng].get('ERROR_REPORT_MESSAGE'),
                'data': None,
                'error': True,
                'status': HTTPStatus.INTERNAL_SERVER_ERROR
            }, status=HTTPStatus.OK)
