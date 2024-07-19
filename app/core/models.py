"""
Database models
"""

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
import uuid
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


NOTIFICATION_TYPE_CHOICES = [
    ('BROADCAST', 'Broadcast'),
    ('SINGLE', 'Single')
]


# Choices for the "status" field in the Incident model
INCIDENT_STATUS_CHOICES = [
    ("ACTIVE", "Active"),
    ("PENDING", "Pending"),
    ("FIXING", "Fixing"),
    ("RESOLVED", "Resolved"),
    ("REJECTED", "Rejected"),
]


# Choices for the "reported_by" field in the Incident model
REPORTED_BY_CHOICES = [
    ("USER", "User"),
    ("ORG", "Org"),
]


# Model representing an organization with fields
class Organization(models.Model):
    _id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, unique=True)
    address = models.JSONField(default=dict)
    coordinates = gis_models.PointField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # def __str__(self):
    #     return f'id: {self._id} | name: {self.name}'

    class Meta:
        ordering = ["-name"]
        db_table = "organizations"


# Model representing a project associated with an organization
class Project(models.Model):
    _id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    address = models.JSONField(default=dict)
    description = models.CharField(max_length=500)
    coordinates = gis_models.PointField(blank=True, null=True)
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, null=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # def __str__(self):
    #     return f'id: {self._id} | name: {self.name}'

    class Meta:
        ordering = ["-name"]
        db_table = "projects"


# Custom manager for the User model
class UserManager(BaseUserManager):
    """Manager for users"""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user"""
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# Custom user model with fields for user profile information
class User(AbstractBaseUser, PermissionsMixin):
    """User in the system"""

    _id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    picture = models.FileField(upload_to="user_images/", blank=True)
    name = models.CharField(max_length=25)
    email = models.EmailField(max_length=255, unique=True)
    phone = models.CharField(max_length=15)
    address = models.JSONField(default=dict)
    coordinates = gis_models.PointField(
        default=Point(0.0, 0.0), blank=True, null=True)
    roaming_coordinates = gis_models.PointField(
        default=Point(0.0, 0.0), blank=True, null=True)
    alert_radius = models.FloatField(default=3)
    notification = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    points = models.IntegerField(default=0)
    password = models.CharField(max_length=128, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    def get_project_id(self):
        return self.project._id if self.project else ''

    # def __str__(self):
    #     coords = self.roaming_coordinates
    #     return f'id: {self._id} | name: {self.name} \
    #         | email: {self.email} \
    #         {"| ORG" if self.is_staff else ""} \
    #         | coords: {coords.y}, {coords.x}'

    class Meta:
        ordering = ["-name"]
        db_table = "users"

    objects = UserManager()
    USERNAME_FIELD = "email"


# Model representing incident categories
class IncidentCategory(models.Model):
    _id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=25)
    icon = models.FileField(upload_to="incident_category_icons/")
    description = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # def __str__(self):
    #     return f'id: {self._id} | name: {self.name}'

    class Meta:
        ordering = ["created_at"]
        db_table = "incident_categories"
        verbose_name = "Incident Category"
        verbose_name_plural = "Incident Categories"


# Model for storing incident images
class IncidentImage(models.Model):
    _id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    image = models.FileField(upload_to="incident_images/")

    class Meta:
        db_table = "incident_images"


# Model representing an incident reported by users
class Incident(models.Model):
    _id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    project = models.ForeignKey(
        Project, on_delete=models.PROTECT, blank=True, null=True
    )
    images = models.ManyToManyField(
        IncidentImage, related_name="incidents", blank=True
    )
    incident_category = models.ForeignKey(
        IncidentCategory, on_delete=models.PROTECT)
    subject = models.CharField(max_length=30)
    description = models.CharField(max_length=200)
    coordinates = gis_models.PointField(blank=True, null=True)
    address = models.JSONField(default=dict)
    upvote_count = models.IntegerField(default=0)
    report_count = models.IntegerField(default=0)
    status = models.CharField(
        max_length=10,
        choices=INCIDENT_STATUS_CHOICES,
        default=INCIDENT_STATUS_CHOICES[0][0],
    )
    is_accepted_by_org = models.BooleanField(default=False)
    is_internal_for_org = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    reported_by = models.CharField(
        max_length=4,
        choices=REPORTED_BY_CHOICES,
        default=REPORTED_BY_CHOICES[0][0]
    )
    voters = models.ManyToManyField(
        User,
        related_name="voted_incidents",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        coords = self.coordinates
        return f'id: {self._id} | subject: {self.subject} \
            | created by: {self.user.name} \
            ({ "ORG" if self.user.is_staff else "USER"}) \
            | coords: {coords.y}, {coords.x}'

    class Meta:
        ordering = ["-created_at"]
        db_table = "incidents"


# Model representing a notification list for users
class NotificationList(models.Model):
    _id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(
        max_length=10,
        choices=NOTIFICATION_TYPE_CHOICES
    )
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    incident = models.ForeignKey(Incident, on_delete=models.PROTECT)
    coordinates = gis_models.PointField(blank=True, null=True)
    title = models.CharField(max_length=70)
    subject = models.CharField(max_length=30)
    description = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     coords = self.coordinates
    #     return f'id: {self._id} | subject: {self.subject} \
    #         | coords: {coords.y}, {coords.x}'

    class Meta:
        ordering = ["-created_at"]
        db_table = "notifications_list"
        verbose_name = "Notification List"
        verbose_name_plural = "Notifications List"


@receiver(post_save, sender=NotificationList)
def trigger_notification(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        if instance.type == 'BROADCAST':
            group_name = 'broadcast_notification'
        else:
            group_name = f"user_{instance.user._id}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_notification',
                'notification': {
                    'id': str(instance._id),
                    'type': instance.type,
                    'incident_id': str(instance.incident._id),
                    'user_id': str(instance.user._id),
                    'title': instance.title,
                    'subject': instance.incident.subject,
                    'description': instance.incident.description,
                    'lat': instance.coordinates.x,
                    'lng': instance.coordinates.y,
                    'created_at': str(instance.created_at)
                }
            }
        )
