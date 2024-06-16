"""
URL mappings for the user API
"""
from django.urls import path
from .views import (
    LoginView,
    SignupView,
    ProfileView,
)

app_name = 'user'

urlpatterns = [
    path('login', LoginView.as_view(), name='login'),
    path('signup', SignupView.as_view(), name='signup'),
    path('profile', ProfileView.as_view(), name='profile')
]
