"""
URL mappings for the incident API
"""
from django.urls import path
from .views import (
    IncidentView,
    IncidentCategoryView,
    GetNearbyReportForOrg,
    GetNearbyReportForUser,
    FilterReportsForUser,
    FilterReportsForOrg,
)

app_name = 'incident'

urlpatterns = [
    path('category', IncidentCategoryView.as_view(), name='incident-categories'),
    path('', IncidentView.as_view(), name='incidents'),
    path('nearby/org', GetNearbyReportForOrg.as_view(), name='get_nearby_report_for_org'),
    path('nearby/user', GetNearbyReportForUser.as_view(), name='get_nearby_report_for_user'),
    path('filter/user', FilterReportsForUser.as_view(), name='filter_reports_for_user'),
    path('filter/org', FilterReportsForOrg.as_view(), name='filter_reports_for_org'),
]
