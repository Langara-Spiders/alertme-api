"""
URL configuration for app project.
"""
from django.contrib import admin
from django.urls import path, re_path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('v1/users/', include('user.urls')),
    path(r'^v1/incidents/?', include('incident.urls')),
]
