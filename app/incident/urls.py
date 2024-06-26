"""
URL mappings for the incident API
"""

from django.urls import path
from .views import (
    IncidentReportView,
    IncidentCategoryView,
    IncidentSiteView,
    IncidentNearbyView,
    IncidentUserView,
    IncidentUpvoteView,
    IncidentDeleteView
)

app_name = 'incident'

urlpatterns = [
    path(
        'category',
        IncidentCategoryView.as_view(),
        name='incident-categories',
    ),
    path('site', IncidentSiteView.as_view(), name='incidents-site'),
    path('report', IncidentReportView.as_view(), name='incidents-report'),
    path('nearby', IncidentNearbyView.as_view(), name='incidents-nearby'),
    path('user', IncidentUserView.as_view(), name='incidents-user'),
    path('upvote', IncidentUpvoteView.as_view(), name='incidents-upvote'),
    path('delete', IncidentDeleteView.as_view(), name='incidents-delete'),
]
