"""
Database models
"""
from django.db import models
import uuid
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)



# The `INCIDENT_STATUS_CHOICES` constant is defining a list of choices for the status of an incident.
# Each choice is a tuple where the first element is the value stored in the database and the second
# element is a human-readable representation of that value.
INCIDENT_STATUS_CHOICES = [
    ('NONE', 'None'),
    ('ACTIVE', 'Active'),
    ('PENDING', 'Pending'),
    ('FIXING', 'Fixing'),
    ('RESOLVED', 'Resolved'),
]

# The `REPORTED_BY_CHOICES` constant is defining a list of choices for the reported by field in the
# database models. It provides a set of options for who reported an incident, with each choice
# represented as a tuple. The first element of the tuple is the value that will be stored in the
# database, and the second element is a human-readable representation of that value.
REPORTED_BY_CHOICES = [
    ('USER', 'User'),
    ('ORG', 'Org'),
]



class Organization(models.Model):
    _id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, unique=True)
    address = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        db_table = 'organizations'


class Project(models.Model):
    _id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=100)
    address = models.JSONField(default=dict)
    description = models.CharField(max_length=500)
    coordinate = models.JSONField(default=dict)
    organization_id = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        null=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        db_table = 'projects'


class UserManager(BaseUserManager):
    """Manager for users"""
    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user"""
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system"""
    _id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    picture = models.URLField(max_length=200, blank=True)
    name = models.CharField(max_length=25)
    email = models.EmailField(max_length=255, unique=True)
    phone = models.CharField(max_length=15)
    address = models.JSONField(default=dict)
    coordinate = models.JSONField(default=dict)
    notification = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project_id = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']
        db_table = 'users'

    objects = UserManager()
    USERNAME_FIELD = 'email'
    
    
    
    
class IncidentCategory(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=25)
    icon = models.FileField(upload_to='incident_category_icons/')
    description = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        db_table = 'incident_categories'
        verbose_name = "Incident Category"
        verbose_name_plural = "Incident Categories"
        
        
class IncidentImage(models.Model):
    image = models.FileField(upload_to='incident_images')
    class Meta:
        db_table = 'incident_images'
        
        
class Incident(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(User, on_delete=models.PROTECT)
    images = models.ForeignKey(IncidentImage, on_delete=models.PROTECT, null=True, blank=True)
    incident_category_id = models.ForeignKey(IncidentCategory, on_delete=models.PROTECT)
    subject = models.CharField(max_length=30)
    description = models.CharField(max_length=300)
    coordinate = models.JSONField(default=dict)
    upvote_count = models.IntegerField(default=0)
    report_count = models.IntegerField(default=0)
    status = models.CharField(
        max_length=10,
        choices=INCIDENT_STATUS_CHOICES,
        default=INCIDENT_STATUS_CHOICES[0][0]
    )
    is_accepted_by_org = models.BooleanField(default=False)
    is_internal_for_org = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    reported_by = models.CharField(
        max_length=4,
        choices=REPORTED_BY_CHOICES,
        default=REPORTED_BY_CHOICES[0][0]
    )
    voters = models.ManyToManyField(User, related_name='voted_incidents', blank=True, )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        db_table = 'incidents'
    
    
class NotificationList(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(User, on_delete=models.PROTECT)
    incident_id = models.ForeignKey(Incident, on_delete=models.PROTECT)
    subject = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        db_table = 'notifications_list'
        verbose_name = "Notification List"
        verbose_name_plural = "Notifications List"

