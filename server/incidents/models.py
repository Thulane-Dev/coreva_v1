from django.db import models
import uuid

# Import Models start
from account.models import *
from authentication.models import *
from projects.models import *


class IncidentModel(models.Model):
    SEVERITY_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    )

    TYPE_CHOICES = (
        ("near Miss", "Near Miss"),
        ("first Aid", "First Aid "),
        ("medical Treatment", "Medical Treatment"),
        ("lost Time Injury", "Lost Time Injury "),
        ("property Damage", "Property Damage"),
        ("environmental Incident", "Environmental Incident "),
        ("Vehicle Accident", "Medical Treatment"),

    )

    STATUS_CHOICES = (
        ("open", "Open"),
        ("resolved", "Resolved"),
    )

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    project = models.ForeignKey(
        ProjectModel, on_delete=models.CASCADE, null=True, blank=True, related_name="incidents")
    incident_date = models.DateField()
    incident_time = models.TimeField(null=True, blank=True,)
    title = models.CharField(max_length=255, blank=True,)
    work = models.CharField(max_length=255, blank=True,)
    description = models.TextField(blank=True, null=True)
    injuries = models.TextField(blank=True, null=True)
    action_taken = models.TextField(blank=True, null=True)
    severity = models.CharField(
        max_length=20, choices=SEVERITY_CHOICES, default="medium",)
    incident_type = models.CharField(
        max_length=100, choices=TYPE_CHOICES)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="open", null=True)
    weather_conditions = models.CharField(max_length=255, blank=True,)
    location = models.CharField(max_length=255, blank=True,)
    assigned_to = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, null=True, blank=True, related_name="assigned_incident")
    created_by = models.ForeignKey(
        UserModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_incidents",)
    created_at = models.DateTimeField(auto_now_add=True,)
    updated_at = models.DateTimeField(auto_now=True,)

    def __str__(self):
        return f"{self.title} - {self.project}"


class InjuredPersonModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    incident = models.ForeignKey(
        IncidentModel, on_delete=models.CASCADE, null=True, blank=True, related_name="injured_person")
    first_name = models.CharField(max_length=255, blank=True,)
    last_name = models.CharField(max_length=255, blank=True,)
    injury = models.CharField(max_length=255, blank=True,)
    body_part = models.CharField(max_length=255, blank=True,)
    treatment = models.CharField(max_length=255, blank=True,)
    created_at = models.DateTimeField(auto_now_add=True,)

    def __str__(self):
        return f"{self.first_name} - {self.last_name}"


class WitnessModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    incident = models.ForeignKey(
        IncidentModel, on_delete=models.CASCADE, null=True, blank=True, related_name="witness")
    full_name = models.CharField(max_length=255, blank=True,)
    contract = models.CharField(max_length=255, blank=True,)
    created_at = models.DateTimeField(auto_now_add=True,)

    def __str__(self):
        return f"{self.full_name}"
