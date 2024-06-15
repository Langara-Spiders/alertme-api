from django.contrib import admin
from .models import (
    User,
    Organization,
    Project,
    Incident,
    IncidentCategory,
    IncidentImage,
    NotificationList
)


admin.register(
    User,
    Organization,
    Project,
    Incident,
    IncidentCategory,
    IncidentImage,
    NotificationList
)(admin.ModelAdmin)
