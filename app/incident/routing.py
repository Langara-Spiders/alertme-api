from django.urls import path
from .consumers import NotificationConsumer

app_name = 'notification'

websocket_urlpatterns = [
    path('v1/updates', NotificationConsumer.as_asgi()),
]
