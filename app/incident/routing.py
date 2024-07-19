from django.urls import path
from .consumers import NotificationConsumer

app_name = 'notification'

websocket_urlpatterns = [
    path('api/notifications', NotificationConsumer.as_asgi()),
]
