from django.contrib import admin
from .models import (
    User,
    Organization,
    Project,
)


admin.register(
    User,
    Organization,
    Project,
)(admin.ModelAdmin)
