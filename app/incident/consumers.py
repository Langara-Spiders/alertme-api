import json
import threading
from http import HTTPStatus
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from urllib.parse import parse_qs


class NotificationConsumer(AsyncWebsocketConsumer):
    def get_user(self):
        from django.contrib.auth import (
            get_user_model
        )
        from core.utils import decode_jwt_token

        self.user = ''
        query_string = self.scope['query_string'].decode()
        params = parse_qs(query_string)
        token = params.get('token', [None])[0]

        # Check if token is present
        if token:
            response = decode_jwt_token(token)

            # Check error
            if not response.get('error'):
                # Get decoded token info
                data = response.get('data')
                # Attach user info to the scope
                self.scope['user_info'] = data
                user_id = data.get('_id')
                # Return the user object
                self.user = get_user_model().objects.filter(
                    _id=user_id, is_active=True).first()

    def update_user_coordinates(self):
        self.user.roaming_coordinates = self.coordinates
        self.user.save()

    async def connect(self):
        thread = threading.Thread(target=self.get_user)
        thread.start()
        thread.join()

        if not self.user:
            await self.close()
            return

        self.group_broadcast_name = 'broadcast_notification'
        self.group_single_name = f'user_{self.user._id}'

        # Register channel for single notifications
        await self.channel_layer.group_add(
            self.group_single_name,
            self.channel_name
        )

        # Register channel for broadcast notifications
        await self.channel_layer.group_add(
            self.group_broadcast_name,
            self.channel_name
        )

        # Accept request
        await self.accept()

    async def disconnect(self, close_code):
        if self.user:
            await self.channel_layer.group_discard(
                self.group_single_name,
                self.channel_name
            )

            await self.channel_layer.group_discard(
                self.group_broadcast_name,
                self.channel_name
            )

    async def receive(self, text_data):
        coordinates = json.loads(text_data)

        self.coordinates = Point(
            coordinates.get('lng'),
            coordinates.get('lat'),
            srid=4326
        )

        thread = threading.Thread(target=self.update_user_coordinates)
        thread.start()
        thread.join()

    async def send_notification(self, event):
        notification = event['notification']
        check_single = notification.get('type') == 'SINGLE'
        check_broadcast = notification.get('type') == 'BROADCAST'
        check_current_user = notification.get('user_id') == str(self.user._id)
        check_not_current_user = notification.get('user_id') != str(self.user._id)

        # Single notification
        if check_single and check_current_user:
            await self.send(text_data=json.dumps({
                'notification': notification
            }))

        # Broadcast notification
        elif check_broadcast and check_not_current_user:
            from django.contrib.gis.geos import Point
            from django.contrib.gis.measure import Distance

            # Check if user alert radius is within the range for notification
            lat = notification.get('lat')
            lng = notification.get('lng')

            notification_point = Point(lng, lat, srid=4326)
            user_point = self.user.roaming_coordinates

            distance = user_point.distance(notification_point)
            distance_in_km = Distance(m=distance).km
            user_alert_radius = self.user.alert_radius

            if user_alert_radius >= distance_in_km:
                await self.send(text_data=json.dumps({
                    'notification': notification
                }))
