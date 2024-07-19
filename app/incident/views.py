import json
import threading
from django.contrib.auth import (
    get_user_model
)
from django.http import JsonResponse
from django.views import View
from core.models import (
    INCIDENT_STATUS_CHOICES,
    Incident,
    IncidentCategory,
    Project,
    IncidentImage,
)
from http import HTTPStatus
from core.messages import (
    NotificationMessages,
    Messages
)
from core.utils import (
    format_incident_data,
    create_notification,
)
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D


ALL_INCIDENT_STATUS = [s[0] for s in INCIDENT_STATUS_CHOICES]
INCIDENT_POINT_UPVOTE = 10
INCIDENT_POINT_ACCEPT = 50


# Get all Issue categories
class IncidentCategoryView(View):
    def get(self, request):
        try:
            # Get all the categories
            categories = IncidentCategory.objects.all()

            # Loop over categories
            # to format and create JSON objects
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
                'message': Messages.SUCCESS,
                'data': category_list,
                'error': False,
                'status': HTTPStatus.OK
            }, status=HTTPStatus.OK)

        # General exceprion
        except Exception as e:
            print(e)

            return JsonResponse({
                'message': Messages.ERROR,
                'data': None,
                'error': True,
                'status': HTTPStatus.INTERNAL_SERVER_ERROR
            }, status=HTTPStatus.OK)


# Upvote a Issue
class IncidentUpvoteView(View):
    def put(self, request):
        try:
            incident_id = request.GET.get('id')
            user_info = request.user_info
            user_id = user_info.get('_id')

            # Get the user object
            user = get_user_model().objects.get(_id=user_id)
            # Get the incident object
            incident = Incident.objects.filter(_id=incident_id).first()

            # If incident object doesnot
            # exists for given incident id
            if not incident:
                return JsonResponse({
                    'message': Messages.ERROR_INVALID_INCIDENT_ID,
                    'data': None,
                    'error': True,
                    'status': HTTPStatus.BAD_REQUEST
                }, status=HTTPStatus.OK)

            if incident.voters.filter(_id=user._id):
                return JsonResponse({
                    'message': Messages.ERROR_ALREADY_UPVOTED,
                    'data': None,
                    'error': True,
                    'status': HTTPStatus.CONFLICT
                }, status=HTTPStatus.OK)

            # Get the incident reported user
            reported_user = incident.user
            # Add the user to the voters of the incident
            incident.voters.add(user)
            # Increment the upvote_count of the incident
            incident.upvote_count += 1

            # Upvote reached threshold
            if incident.upvote_count == 3:
                # Change status to pending
                incident.status = 'PENDING'
                # Update reported user points
                reported_user.points += INCIDENT_POINT_UPVOTE
                reported_user.save()
                # Generate a notification to reported user
                threading.Thread(
                    target=create_notification,
                    args=(
                        'SINGLE',
                        user,
                        incident,
                        NotificationMessages
                        .UPVOTE_THRESHOLD_REPORT
                    )
                ).start()

            else:
                # Generate a notification to reported user
                # that a upvote was made
                threading.Thread(
                    target=create_notification,
                    args=(
                        'SINGLE',
                        user,
                        incident,
                        NotificationMessages
                        .USER_UPVOTED_REPORT.format(user.name)
                    )
                ).start()

            # Save the incident info after upvote
            incident.save()
            # Format the result to JSON
            incident = format_incident_data(incident)

            return JsonResponse({
                'message': Messages.SUCCESS_UPVOTE,
                'data': incident,
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


# Delete a Issue
class IncidentDeleteView(View):
    def delete(self, request):
        try:
            user_info = request.user_info
            incident_id = request.GET.get('id')
            user_id = user_info.get('_id')

            # Get the incident object, it must belong
            # to current user to delete it
            incident = Incident\
                .objects.filter(_id=incident_id, user___id=user_id).first()

            # If incident object doesnot
            # exists for given incident id
            if not incident:
                return JsonResponse({
                    'message': Messages.ERROR_INVALID_INCIDENT_ID,
                    'data': None,
                    'error': True,
                    'status': HTTPStatus.BAD_REQUEST
                }, status=HTTPStatus.OK)

            # Delete is possible only when
            # incident is in ACTIVE status
            if incident.status == 'ACTIVE':
                # Soft delete, set is_active to False
                incident.is_active = False
                # Save the object
                incident.save()
                # Format the result to JSON
                incident = format_incident_data(incident)

                return JsonResponse({
                    'message': Messages.SUCCESS_DELETE,
                    'error': False,
                    'data': incident,
                    'status': HTTPStatus.OK
                }, status=HTTPStatus.OK)

            else:
                # Incident cannot be deleted
                # due to status other than ACTIVE
                return JsonResponse({
                    'message': Messages.ERROR_DELETE,
                    'data': None,
                    'error': True,
                    'status': HTTPStatus.CONFLICT
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


# Report or get a Issue
class IncidentReportView(View):
    def get(self, request):
        try:
            user_info = request.user_info
            incident_id = request.GET.get('id')

            # Get the incident object
            incident = Incident.objects\
                .filter(_id=incident_id,).first()

            # If incident object doesnot
            # exists for given incident id
            if not incident:
                return JsonResponse({
                    'message': Messages.ERROR_INVALID_INCIDENT_ID,
                    'data': None,
                    'error': True,
                    'status': HTTPStatus.BAD_REQUEST
                }, status=HTTPStatus.OK)

            # Format the result to JSON
            incident = format_incident_data(incident, user_info)

            return JsonResponse({
                "message": Messages.SUCCESS,
                "data": incident,
                "error": False,
                "status": HTTPStatus.OK,
            }, status=HTTPStatus.OK)

        # General exception
        except Exception as e:
            print(e)

            return JsonResponse({
                "message": Messages.ERROR,
                "data": None,
                "error": True,
                "status": HTTPStatus.INTERNAL_SERVER_ERROR,
            }, status=HTTPStatus.OK)

    def post(self, request):
        try:
            report = json.loads(request.POST.get('report'))
            category_id = report.get('category_id')
            subject = report.get('subject')
            description = report.get('description')
            coordinates = report.get('coordinates')
            incident_lat = float(coordinates.get('lat'))
            incident_lng = float(coordinates.get('lng'))
            address = report.get('address')
            is_internal_for_org = report.get('is_internal_for_org', False)
            # Get the images for the report
            pictures = request.FILES.getlist('pictures')[:3]
            # Create a point for given coordinates
            incident_point = Point(incident_lng, incident_lat, srid=4326)
            user_info = request.user_info
            is_staff = user_info.get('is_staff')

            # Get the user object
            user = get_user_model().objects\
                .get(_id=user_info.get('_id'))

            # Get the category object
            incident_category = IncidentCategory.objects\
                .filter(_id=category_id).first()

            # If invalid category ID is passed
            if not incident_category:
                return JsonResponse({
                    'message': Messages.ERROR_INVALID_CATEGORY_ID,
                    'data': None,
                    'error': True,
                    'status': HTTPStatus.BAD_REQUEST
                }, status=HTTPStatus.OK)

            # If is_internal_for_org flag is set
            # and user is regular user, undo the flag
            if is_internal_for_org and not is_staff:
                is_internal_for_org = False

            # Create a incident object
            incident = Incident(
                user=user,
                incident_category=incident_category,
                subject=subject,
                description=description,
                coordinates=incident_point,
                address=address,
                reported_by='ORG' if is_staff else 'USER',
                is_internal_for_org=is_internal_for_org,
            )

            # Find the nearby project within 100 meter radius
            nearby_project = Project.objects.filter(
                coordinates__distance_lte=(incident_point, D(km=1000000))
            ).annotate(
                distance=Distance('coordinates', incident_point)
            ).order_by('distance').first()

            # If we have a closeby project
            # assign the incident to that project
            if nearby_project:
                incident.project = nearby_project

            # Save the incident object
            incident.save()

            # Loop over images if present
            images = []
            for picture in pictures:
                incident_image = IncidentImage()
                incident_image.image = picture
                incident_image.image.name = picture.name
                # Save the images
                incident_image.save()
                images.append(incident_image)

            # Set the images to incident if present
            if images:
                incident.images.set(images)
                incident.save()

            # Create notification for nearby users
            threading.Thread(
                target=create_notification,
                args=(
                    'BROADCAST',
                    user,
                    incident,
                    NotificationMessages
                    .NEARBY_REPORT
                )
            ).start()

            # Format the result to JSON
            incident = format_incident_data(incident)

            return JsonResponse({
                "message": Messages.SUCCESS_REPORT,
                "data": incident,
                "error": False,
                "status": HTTPStatus.OK,
            }, status=HTTPStatus.OK)

        # General Exception
        except Exception as e:
            print(e)

            return JsonResponse({
                "message": Messages.ERROR,
                "data": None,
                "error": False,
                "status": HTTPStatus.INTERNAL_SERVER_ERROR,
            }, status=HTTPStatus.OK)


# Get nearby Issues
class IncidentNearbyView(View):
    def get(self, request):
        try:
            user_lat = float(request.GET.get("lat"))
            user_lng = float(request.GET.get("lng"))
            user_point = Point(user_lng, user_lat, srid=4326)
            user_info = request.user_info

            # Get user object
            user = get_user_model().objects\
                .get(_id=user_info.get('_id'))

            # Find the nearby incident within alert_radius provided by
            # user, fetch only ACTIVE, PENDING, FIXING status objects
            nearby_incidents_qs = Incident.objects.filter(
                coordinates__distance_lte=(
                    user_point, D(km=user.alert_radius)),
                is_active=True,
                status__in=['ACTIVE', 'PENDING', 'FIXING']
            ).annotate(
                distance=Distance('coordinates', user_point)
            ).order_by('distance')

            # Format to JSON and create array of nearby incidents
            nearby_incidents = []
            for incident in nearby_incidents_qs:
                nearby_incidents.append(format_incident_data(incident))

            return JsonResponse({
                "message": Messages.SUCCESS,
                "data": nearby_incidents,
                "error": False,
                "status": HTTPStatus.OK,
            }, status=HTTPStatus.OK)

        # General exception
        except Exception as e:
            print(e)

            return JsonResponse({
                "message": Messages.ERROR,
                "data": None,
                "error": True,
                "status": HTTPStatus.INTERNAL_SERVER_ERROR,
            }, status=HTTPStatus.OK)


class IncidentUserView(View):
    def get(self, request):
        try:
            filter_by = request.GET.get('filter_by', None)
            user_info = request.user_info

            # Get all incident objects reported by current user
            incidents = Incident.objects.all()\
                .filter(user___id=user_info.get('_id'))

            # If valid filter_by option is passed
            if filter_by and filter_by not in ALL_INCIDENT_STATUS:
                return JsonResponse({
                    "message": Messages.ERROR_INVALID_FILTERBY,
                    "data": None,
                    "error": True,
                    "status": HTTPStatus.BAD_REQUEST,
                }, status=HTTPStatus.OK)

            if filter_by:
                incidents = incidents.filter(status=filter_by)

            # Format to JSON and create array of user incidents
            user_incidents = []
            for incident in incidents:
                user_incidents\
                    .append(format_incident_data(incident))

            return JsonResponse({
                "message": Messages.SUCCESS,
                "data": user_incidents,
                "error": False,
                "status": HTTPStatus.OK,
            }, status=HTTPStatus.OK)

        # General exception
        except Exception as e:
            print(e)

            return JsonResponse({
                "message": Messages.ERROR,
                "data": None,
                "error": True,
                "status": HTTPStatus.INTERNAL_SERVER_ERROR,
            }, status=HTTPStatus.OK)


class IncidentSiteView(View):
    def get(self, request, reported_by):
        try:
            user_info = request.user_info
            filter_by = request.GET.get('filter_by', None)
            project = Project.objects\
                .get(_id=user_info.get('project_id'))
            reported_by = reported_by.upper()

            # Check reported_by field
            if reported_by not in ['USER', 'ORG']:
                return JsonResponse({
                    "message": Messages.ERROR_INVALID_REPORTEDBY,
                    "data": None,
                    "error": True,
                    "status": HTTPStatus.BAD_REQUEST,
                }, status=HTTPStatus.OK)

            # Get incident objects
            incidents = Incident.objects\
                .filter(
                    is_active=True,
                    project___id=project._id,
                    reported_by=reported_by,
                )

            ALL_OPTIONS = [*ALL_INCIDENT_STATUS, 'INTERNAL']

            # If valid filter_by option is passed
            if filter_by and filter_by not in ALL_OPTIONS:

                return JsonResponse({
                    "message": Messages.ERROR_INVALID_FILTERBY,
                    "data": None,
                    "error": True,
                    "status": HTTPStatus.BAD_REQUEST,
                }, status=HTTPStatus.OK)

            # Based on filter, filter-out the incident objects
            if filter_by == 'INTERNAL':
                incidents = incidents.filter(is_internal_for_org=True)
            elif filter_by:
                incidents = incidents.filter(status=filter_by)

            # Format to JSON and create array of site incidents
            site_incidents = []
            for incident in incidents:
                site_incidents.append(
                    format_incident_data(incident)
                )

            return JsonResponse({
                'message': Messages.SUCCESS,
                'data': site_incidents,
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

    def put(self, request, reported_by):
        try:
            status = request.GET.get('status')
            incident_id = request.GET.get('id')
            user_info = request.user_info
            is_staff = user_info.get('is_staff')

            # Not a org employee
            if not is_staff:
                return JsonResponse({
                    "message": Messages.ERROR_UNAUTHORIZED,
                    "data": None,
                    "error": True,
                    "status": HTTPStatus.UNAUTHORIZED,
                }, status=HTTPStatus.OK)

            # Get user object
            user = get_user_model().objects\
                .get(_id=user_info.get('_id'))

            # Get project object
            project = user.project

            if not project:
                return JsonResponse({
                    "message": Messages.ERROR_NO_PROJECT,
                    "data": None,
                    "error": True,
                    "status": HTTPStatus.BAD_REQUEST,
                }, status=HTTPStatus.OK)

            # Check provided status
            if status not in ['FIXING', 'REJECTED', 'RESOLVED']:
                return JsonResponse({
                    "message": Messages.ERROR_INVALID_STATUS,
                    "data": None,
                    "error": True,
                    "status": HTTPStatus.BAD_REQUEST,
                }, status=HTTPStatus.OK)

            incident = Incident.objects\
                .filter(_id=incident_id).first()

            # If incident object doesnot
            # exists for given incident id
            if not incident:
                return JsonResponse({
                    'message': Messages.ERROR_INVALID_INCIDENT_ID,
                    'data': None,
                    'error': True,
                    'status': HTTPStatus.BAD_REQUEST
                }, status=HTTPStatus.OK)

            if incident.status == status:
                return JsonResponse({
                    'message': Messages.ERROR_ALREADY_IN_STATUS,
                    'data': None,
                    'error': True,
                    'status': HTTPStatus.CONFLICT
                }, status=HTTPStatus.OK)

            # Get incident reported user
            reported_user = incident.user

            if status == 'FIXING':
                incident.is_accepted_by_org = True
                incident.project = user.project

                # Get the incident reported user
                reported_user = incident.user

                # Update reported user points
                reported_user.points += INCIDENT_POINT_ACCEPT
                reported_user.save()

                # Generate a notification to reported user
                threading.Thread(
                    target=create_notification,
                    args=(
                        'SINGLE',
                        user,
                        incident,
                        NotificationMessages
                        .ORG_ACCEPTED_REPORT
                        .format(project.organization.name)
                    )
                ).start()

                # Create notification for nearby users
                threading.Thread(
                    target=create_notification,
                    args=(
                        'BROADCAST',
                        user,
                        incident,
                        NotificationMessages
                        .NEARBY_REPORT_CONFIRMED
                    )
                ).start()

                incident.status = 'FIXING'

            elif status == 'RESOLVED':
                # Incident doesnot belong
                # to the current org to resolve
                if incident.project._id != project._id:
                    return JsonResponse({
                        'message': Messages.ERROR_UNAUTHORIZED_RESOLVE,
                        'data': None,
                        'error': True,
                        'status': HTTPStatus.UNAUTHORIZED
                    }, status=HTTPStatus.OK)

                # Generate a notification to reported user
                threading.Thread(
                    target=create_notification,
                    args=(
                        'SINGLE',
                        user,
                        incident,
                        NotificationMessages
                        .ORG_RESOLVED_REPORT
                        .format(project.organization.name)
                    )
                ).start()

                incident.status = 'RESOLVED'

            elif status == 'REJECTED':
                # Incident doesnot belong
                # to the current org to reject it
                if incident.project._id != project._id:
                    return JsonResponse({
                        'message': Messages.ERROR_UNAUTHORIZED_REJECT,
                        'data': None,
                        'error': True,
                        'status': HTTPStatus.UNAUTHORIZED
                    }, status=HTTPStatus.OK)

                # Generate a notification to reported user
                threading.Thread(
                    target=create_notification,
                    args=(
                        'SINGLE',
                        user,
                        incident,
                        NotificationMessages
                        .ORG_REJECTED_REPORT
                        .format(project.organization.name)
                    )
                ).start()

                incident.status = 'REJECTED'

            # Save the incident object
            incident.save()

            # Format the result to JSON
            incident = format_incident_data(incident)

            return JsonResponse({
                'message': Messages.SUCCESS,
                'data': incident,
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
