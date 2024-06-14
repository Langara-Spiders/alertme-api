from django.db import models  # noqa: F401
import uuid



# *************** DB Model for Incidents ***************

# This class defines an Incident model with various fields and relationships in alterme application.
class Incident(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    images = models.JSONField(blank=True, null=True) 
    incident_category = models.ForeignKey('IncidentCategory', on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    coordinates = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    votes = models.IntegerField(default=0)
    is_inactive_count = models.IntegerField(default=0)
    status = models.CharField(max_length=255)
    is_accepted = models.BooleanField(default=False)
    is_internal = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False, editable=False)
    voters = models.ManyToManyField(User, related_name='voted_incidents', blank=True)

    def save(self, *args, **kwargs):
        self.is_staff = self.user.is_staff
        super().save(*args, **kwargs)

    def __str__(self):
        return self.subject
    

# The `IncidentCategory` class defines a model with fields for id, name, and description for alterme
class IncidentCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name