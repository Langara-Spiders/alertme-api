"""
URL mappings for the incident API
"""

from django.urls import path
from .views import (
    IncidentView,
    IncidentCategoryView,
)

app_name = "incident"

urlpatterns = [
    path(
        "category",
        IncidentCategoryView.as_view(),
        name="incident-categories",
    ),
    path("", IncidentView.as_view(), name="incidents"),
]
