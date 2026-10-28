from django.db import models
import uuid
from django.utils import timezone

# Import Models start
from account.models import *
from authentication.models import *


def default_working_days():
    return [0, 1, 2, 3, 4]


class ProjectModel(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    company = models.ForeignKey(
        CompanyProfileModel, on_delete=models.CASCADE, null=True, blank=True, related_name="projects")
    project_name = models.CharField(max_length=255, blank=True)
    client_name = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(null=True, blank=True)
    location = models.ForeignKey(
        AddressModel, on_delete=models.CASCADE, null=True, blank=True)
    latitude = models.CharField(max_length=255, blank=True)
    longitude = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active')
    cover_image = models.ImageField(
        upload_to="media/project_images/", null=True, blank=True)
    working_days = models.JSONField(
        default=default_working_days,
        blank=True
    )
    created_by = models.ForeignKey(
        'authentication.UserModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="created_by_user")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project_name} - {self.company.company_name}"


class ProjectUserModel(models.Model):
    STATUS_CHOICES = [
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        ]
    
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    project = models.ForeignKey(
        ProjectModel, on_delete=models.CASCADE, null=True, blank=True, related_name="project")
    project_user = models.ForeignKey(
        'authentication.UserModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="project_user")
    added_by = models.ForeignKey(
        'authentication.UserModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="added_by")
    removed_by = models.ForeignKey(
            'authentication.UserModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="removed_by")
    status = models.CharField(
            max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project_user.first_name} - {self.project_user.last_name} - {self.project.project_name}"

    

class ProjectContractor(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    project = models.ForeignKey(
        ProjectModel, on_delete=models.CASCADE, null=True, blank=True, related_name="projects")
    contractor = models.ForeignKey(
        CompanyProfileModel, on_delete=models.CASCADE, null=True, blank=True, related_name="contractor_projects")
    added_by = models.ForeignKey(
        UserModel, null=True, blank=True, on_delete=models.SET_NULL)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    STATUS_CHOICES = [
        ('pending', 'Pending Invitation'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contractor.company_name} - {self.project.project_name}"


class DeliveryModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    project = models.ForeignKey(
        ProjectModel, on_delete=models.CASCADE, null=True, blank=True,  related_name="deliveries",)
    reference = models.CharField(max_length=255, blank=True,)
    delivery_date = models.DateField()
    delivery_time = models.TimeField(null=True, blank=True,)
    supplier = models.CharField(max_length=255, blank=True,)
    item = models.CharField(max_length=255, blank=True,)
    quantity = models.CharField(max_length=100, blank=True,)
    notes = models.TextField(blank=True,)
    status = models.CharField(max_length=250, blank=True,)
    created_by = models.ForeignKey(
        UserModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_deliveries",)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.reference:

            last_delivery = (
                DeliveryModel.objects
                .filter(project=self.project)
                .order_by("-id")
                .first()
            )

            if last_delivery:
                number = last_delivery.id + 1
            else:
                number = 1

            self.reference = f"DEL-{number:06d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference}"


class DeliveredItemsModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    delivery = models.ForeignKey(
        DeliveryModel, on_delete=models.CASCADE, null=True, blank=True,  related_name="delivered_item",)
    item = models.CharField(max_length=255, blank=True,)
    quantity = models.DecimalField(
        max_digits=10000, decimal_places=2, blank=True,)
    unit = models.CharField(max_length=255, blank=True,)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item}"



class ProjectUploadedFiles(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    project = models.ForeignKey(ProjectModel, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='project_files_new')
    reference = models.CharField(max_length=255, blank=True,)
    photo = models.ImageField(
        upload_to="media/project_photos/", null=True, blank=True)
    file = models.FileField(
        upload_to="media/project_files/", null=True, blank=True,)
    caption = models.TextField(blank=True)
    incident = models.ForeignKey(
        'incidents.IncidentModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="incident_attachments")
    delivery = models.ForeignKey(
        'projects.DeliveryModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="delivery_attachments_new")
    report = models.ForeignKey(
        'report.DailyReportModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="report_attachments")
    issue_task = models.ForeignKey(
        'issues.IssueModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="issue_task_attachments")
    comment = models.ForeignKey(
        'issues.IssueCommentModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="comment_attachments")
    work_stage = models.ForeignKey(
            'issues.WorkStageModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="work_stage_attachments")
    uploaded_by_user = models.ForeignKey(
        'authentication.UserModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="uploaded_project_files_new")
    uploaded_by_contractor = models.ForeignKey(
            'account.CompanyProfileModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="uploaded_by_contractor")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def filesize(self):
        uploaded_file = self.photo or self.file

        if not uploaded_file:
            return ""

        size = uploaded_file.size

        if size < 1024:
            return f"{size} B"

        if size < 1024 ** 2:
            return f"{size / 1024:.1f} KB"

        if size < 1024 ** 3:
            return f"{size / (1024 ** 2):.1f} MB"

        return f"{size / (1024 ** 3):.1f} GB"

    def __str__(self):
        return f"{self.caption}"


class ActivityModel(models.Model):

    ACTIVITY_TYPES = [
        ("Project Created", "Project Created"),
        ("Project Updated", "Project Updated"),

        ("Inspection Started", "Inspection Started"),
        ("Inspection Completed", "Inspection Completed"),

        ("Issue Created", "Issue Created"),
        ("Issue Assigned", "Issue Assigned"),
        ("Issue Updated", "Issue Updated"),
        ("Issue Resolved", "Issue Resolved"),

        ("Task Created", "Task Created"),
        ("Task Assigned", "Task Assigned"),
        ("Task Completed", "Task Completed"),

        ("Daily Report Created", "Daily Report Created"),
        ("Daily Report Submitted", "Daily Report Submitted"),

        ("Photo Uploaded", "Photo Uploaded"),

        ("User Added", "User Added"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    company = models.ForeignKey(
        CompanyProfileModel, on_delete=models.CASCADE, related_name="activities", null=True, blank=True,)
    project = models.ForeignKey(
        ProjectModel, on_delete=models.CASCADE, related_name="activities", null=True, blank=True)
    user = models.ForeignKey(UserModel, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name="activities")
    activity_type = models.CharField(
        max_length=50, choices=ACTIVITY_TYPES, blank=True)
    description = models.CharField(max_length=500, blank=True)
    icon_type = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["project", "-created_at"]),
            models.Index(fields=["company", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["activity_type"]),
        ]

    def __str__(self):
        return f" {self.project.project_name} - {self.description}"