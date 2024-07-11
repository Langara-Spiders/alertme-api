import json
import threading
from urllib.parse import parse_qs
from http import HTTPStatus
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D


class NotificationConsumer(AsyncWebsocketConsumer):
    def get_user(self):
        from django.contrib.auth import (
            get_user_model
        )

        self.user = get_user_model().objects.filter(_id=self.user_id).first()

    def get_latest_notification(self):
        # Imports
        from core.models import NotificationList

        recent_notifications_qs = NotificationList.objects.filter(
            coordinates__distance_lte=(self.coordinates, D(km=5))
        ).annotate(
            distance=Distance('coordinates', self.coordinates)
        ).filter(
            created_at__gt=timezone.now(),
            type='BROADCAST',
        ).exclude(
            user___id=self.user_id
        ).order_by('distance')

        for notification in recent_notifications_qs:
            self.user.notification.update({
                str(notification._id): {
                    'incident_id': str(notification.incident._id),
                    'title': notification.title,
                    'subject': notification.incident.subject,
                    'description': notification.incident.description,
                    'read_flag': False
                }
            })

        self.user.roaming_coordinates = self.coordinates
        self.user.save()

    async def connect(self):
        # Get user_id from query params
        query_string = self.scope['query_string'].decode()
        query_params = parse_qs(query_string)
        self.user_id = query_params.get('user_id', [None])[0]
        self.group_name = f'user_{self.user_id}'

        thread = threading.Thread(target=self.get_user)
        thread.start()
        thread.join()

        # Register channel
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Accept request
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        from core.utils import Messages

        coordinates = json.loads(text_data)

        self.coordinates = Point(
            coordinates.get('lng'),
            coordinates.get('lat'),
            srid=4326
        )

        thread = threading.Thread(target=self.get_latest_notification)
        thread.start()
        thread.join()

        # Send back the notification
        await self.send(text_data=json.dumps({
            'message': Messages.SUCCESS,
            'data': list(self.user.notification.values()),
            'error': False,
            'status': HTTPStatus.OK,
        }))
