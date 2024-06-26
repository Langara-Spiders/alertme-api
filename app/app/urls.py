"""
URL configuration for app project.
"""
from django.contrib import admin
from django.urls import path, re_path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('user.urls')),
    re_path(r'^api/incidents/?', include('incident.urls')),
]
