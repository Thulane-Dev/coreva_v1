from django.db import models
import uuid

# Import Models start
from account.models import *
from authentication.models import *
from projects.models import ProjectModel


class DailyReportModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reference = models.CharField(max_length=200, null=True, blank=True)

    # =========================
    # PROJECT
    # =========================
    project = models.ForeignKey(
        ProjectModel, on_delete=models.CASCADE, related_name="daily_reports")
    report_date = models.DateField()

    # =========================
    # REPORT DETAILS
    # =========================
    foreman = models.CharField(max_length=200, null=True, blank=True)
    superintendent = models.CharField(max_length=200, null=True, blank=True)

    # =========================
    # WORK TIME
    # =========================
    work_start_time = models.TimeField(null=True, blank=True)
    work_end_time = models.TimeField(null=True, blank=True)

    # =========================
    # WEATHER
    # =========================
    weather_condition = models.CharField(max_length=100, blank=True,)

    weather_temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Current temperature in °C",
    )

    weather_min_temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum temperature in °C",
    )

    weather_max_temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum temperature in °C",
    )

    weather_rain_probability = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Maximum probability of rain (%)",
    )

    weather_rainfall = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Expected/recorded precipitation in millimetres",
    )

    weather_wind_speed = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Wind speed in km/h",
    )

    weather_humidity = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Relative humidity (%)",
    )

    weather_comment = models.TextField(
        blank=True,
    )

    # =========================
    # SITE ATTENDANCE
    # =========================
    workers_count = models.PositiveIntegerField(null=True, blank=True,default=0)
    workers_comment = models.TextField(blank=True)
    contractors_count = models.PositiveIntegerField(null=True, blank=True,default=0)
    contractors_comment = models.TextField(blank=True)
    visitors_count = models.PositiveIntegerField(null=True, blank=True,default=0)
    visitors_comment = models.TextField(blank=True)

    # =========================
    # AUDIT
    # =========================
    toolbox_talk_held = models.BooleanField(default=False, null=True)
    toolbox_talk_topic = models.CharField(max_length=200, blank=True)
    toolbox_attendees_count = models.PositiveIntegerField(null=True, blank=True,default=0)
    safety_issues = models.TextField(blank=True)

    # =========================
    # DAILY WORK
    # =========================
    work_completed = models.TextField(blank=True)

    # =========================
    # DELAYS
    # =========================
    delays = models.TextField(blank=True)

    # =========================
    # ADDITIONAL NOTES
    # =========================
    notes = models.TextField(blank=True)

    # =========================
    # STATUS
    # =========================
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('pending', 'Pending'),
    ]
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    

    # =========================
    # LATITUDE
    # =========================
    location_lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)

    # =========================
    # AUDIT
    # =========================
    created_by = models.ForeignKey(UserModel, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name="daily_reports_created")
    completed_by = models.ForeignKey(UserModel, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name="daily_reports_completed_by")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True,blank=True,)
    admin_sign_off = models.ForeignKey(
        'authentication.UserModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="report_sign_off")
    signed_off_at = models.DateTimeField(null=True, blank=True)
    is_missed_report = models.BooleanField(default=False)

    # =========================
    # META
    # =========================

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "report_date"],
                name="unique_daily_report_per_project"
            )
        ]

        ordering = [
            "-report_date",
            "-created_at"
        ]

    def __str__(self):
        return f"{self.project.project_name} - {self.report_date}"
