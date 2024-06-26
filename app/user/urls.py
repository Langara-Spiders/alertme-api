"""
URL mappings for the user API
"""
from django.urls import path
from .views import (
    LoginView,
    SignupView,
    ProfileView,
    RewardView
)

app_name = 'user'

urlpatterns = [
    path('login', LoginView.as_view(), name='login'),
    path('signup', SignupView.as_view(), name='signup'),
    path('profile', ProfileView.as_view(), name='profile'),
    path('reward', RewardView.as_view(), name='reward')
]
