from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
import requests
from django.db.models import Q
from itertools import groupby

# htmx
from django.http import HttpResponse
import json

# Models Import
from .models import *
from authentication.models import *
from account.models import AddressModel
from incidents.models import *
from issues.models import *

# Services Import
from .services.projects_view import (
    get_project_data
)

from issues.services.issues_view import (
    get_all_project_issues_data,
    get_all_project_tasks_data,
)



# ============= Projects View =============
def ProjectsView(request):

    context = {
        "page": "projects/projects.html",
    }

    if request.htmx:
        return render(request, "projects/projects.html", context)
    return render(request, "client/base.html", context)


# ============= Add Project =============
def AddProjectView(request):
    work_days = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    context = {
        "work_days": work_days,
        "page": "projects/add_project.html",
    }

    if request.htmx:
        return render(request, "projects/add_project.html", context)
    return render(request, "client/base.html", context)


# ============= Save New Project Post =============
@require_POST
def save_new_project(request):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company

    # =============== check if estimate date is selected  ===============
    end_date_estimate = request.POST.get("end_date")
    if end_date_estimate:
        end_date = request.POST.get("end_date")
    else:
        end_date = None

    # =============== check if cover image is added ===============
    cover_image = request.FILES.get("cover_image")
    if cover_image:
        project_image = request.FILES.get("cover_image")
    else:
        project_image = None

    # =============== Save Location ===============
    project_location = AddressModel.objects.create(
        street_address=request.POST.get("street_address"),
        city=request.POST.get("city"),
        province=request.POST.get("province"),
        postal_code=request.POST.get("postal_code"),
        country=request.POST.get("country"),
    )

    # =============== Project Working Days ===============
    working_days = request.POST.getlist("working_days")

    working_days = [
        int(day) for day in working_days
    ]

    # =============== Save Project Object ===============
    project = ProjectModel.objects.create(
        company=company,
        created_by=current_user,
        project_name=request.POST.get("project_name"),
        start_date=request.POST.get("start_date"),
        end_date=end_date,
        location=project_location,
        cover_image=project_image,
        latitude=request.POST.get("latitude"),
        longitude=request.POST.get("longitude"),
        working_days=working_days,
    )


    # =============== Save Project User ===============
    ProjectUserModel.objects.create(
        project=project,
        project_user=current_user,
        added_by=current_user,
    )

    messages.success(
        request,
        f"✅ {project.project_name} added successfully."
    )

    # 🎯 Redirect To Projects
    url = reverse('dashboard:today')
    return redirect(f"{url}#project-{project.id}")



# ============= Projects Settings =============
def ProjectSettingsView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(
        ProjectModel.objects.select_related(
            "company",
            "location",
        ),
        uuid=project_uuid,
    )

    context = {
        "project" : project,
        "page": "projects/project_setting.html",
    }

    if request.htmx:
        return render(request, "projects/project_setting.html", context)
    return render(request, "client/base.html", context)


# ============= SAVE PROJECT UPDATES =============
@require_POST
def save_projects_updates(request,project_uuid):
    project = get_object_or_404(
        ProjectModel.objects.select_related(
            "company",
            "location",
        ),
        uuid=project_uuid,
    )

    project.project_name = request.POST.get(
        "project_name",
        ""
    ).strip()

    project.client_name = request.POST.get(
        "client_name",
        ""
    ).strip()


    # Project Status 
    project.status = request.POST.get(
        "status",
        project.status
    )


    # Project Dates 
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")

    project.start_date = start_date or None
    project.end_date = end_date or None


    # Working Days 
    working_days = request.POST.getlist("working_days")
    project.working_days = [
        int(day)
        for day in working_days
        if day.isdigit() and 0 <= int(day) <= 6
    ]


    # Cover Image 
    cover_image = request.FILES.get("cover_image")
    if cover_image:
        project.cover_image = request.FILES.get("cover_image")

    # Project Address 
    location = project.location 
    location.street_address = request.POST.get("street")
    location.city = request.POST.get("city")
    location.province = request.POST.get("province")
    location.country = request.POST.get("country")
    location.save()

    project.save()

    messages.success(
        request,
        "Project settings updated successfully."
    )

    # 🎯 Redirect To Project Profile
    url = reverse('projects:project-setting', args=[project.uuid, ])
    return redirect(url)



def post(self, request, project_uuid):
    project = get_object_or_404(
        ProjectModel.objects.select_related(
            "company",
            "location",
        ),
        uuid=project_uuid,
    )

    project.project_name = request.POST.get(
        "project_name",
        ""
    ).strip()

    project.client_name = request.POST.get(
        "client_name",
        ""
    ).strip()

    project.status = request.POST.get(
        "status",
        project.status
    )

    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")

    project.start_date = start_date or None
    project.end_date = end_date or None

    working_days = request.POST.getlist("working_days")

    project.working_days = [
        int(day)
        for day in working_days
        if day.isdigit() and 0 <= int(day) <= 6
    ]

    project.save()

    messages.success(
        request,
        "Project settings updated successfully."
    )

    return redirect(
        "projects:project-settings",
        project_uuid=project.uuid,
    )



# ============= PROJECT DETAILS VIEW =============
def ProjectDetailsPreviewDetails(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    project_data = get_project_data(project=project, current_user=current_user)
    today = timezone.now().date()
    inspection = project_data['inspection']
    report = project_data['report']
    incidents = project_data['incidents']
    incidents_count = incidents.count()
    deliveries = project_data['deliveries']
    deliveries_count = deliveries.count()
    project_activity = project_data['grouped_activities']
    site_attachments = ProjectUploadedFiles.objects.filter(Q(project=project) & Q(reference='Site Activity') & Q(created_at=today)).order_by("-created_at")

    
    team_members = UserModel.objects.filter(
        company=current_user.company
    ).filter(
        Q(role="admin") |
        Q(project_user__project=project)
    ).distinct()
    project_contractors = (
        ProjectContractor.objects
        .filter(project=project)
        .order_by("-created_at")
    )

    
    # next_url = request.GET.get("next")
    next_url = request.get_full_path()

    # HTMX Target ID'S 
    delivery_target_id = "DeliveriesSession"
    incidents_target_id = "IncidentsSession"
    issues_target_id = "IssuesSection"
    tasks_target_id = "TaskSession"


    context = {
        "current_user": current_user,
        "project": project,
        "project_data": project_data,
        "today": today,
        "incidents": incidents,
        "incidents_count": incidents_count,
        "deliveries": deliveries,
        "deliveries_count": deliveries_count,
        "project_activity": project_activity,
        "team_members": team_members,
        "project_contractors": project_contractors,
        "inspection" : inspection,
        "report" : report,
        "next_url": next_url,
        "site_attachments": site_attachments,

        "incidents_target_id": incidents_target_id,
        "delivery_target_id": delivery_target_id,
        "issues_target_id": issues_target_id,
        "tasks_target_id": tasks_target_id,
        "page": "projects/project_preview_details.html",
    }

    if request.htmx:
        return render(request, "projects/project_preview_details.html", context)
    return render(request, "client/base.html", context)


# ============= ADD PROJECT DELIVERY  =============
def LogProjectDeliveryView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now()

    context = {
        "current_user": current_user,
        "project": project,
        "today": today,
        "page": "projects/log_project_delivery.html",
    }

    if request.htmx:
        return render(request, "projects/log_project_delivery.html", context)
    return render(request, "client/base.html", context)


# ============= SAVE NEW DELIVERY POST METHOD =============
def save_new_delivery(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now()

    if request.method == "POST":
        # Create Delivery Object
        delivery = DeliveryModel.objects.create(
            project=project,
            delivery_date=request.POST.get("delivery_date"),
            delivery_time=request.POST.get("delivery_time"),
            supplier=request.POST.get("supplier"),
            notes=request.POST.get("notes"),
            status=request.POST.get("status"),
            created_by=current_user,
        )

        # =============== DELIVERIES ITEMS ===============
        delivery_items = request.POST.getlist("delivery_item[]")
        delivery_quantities = request.POST.getlist("delivery_quantity[]")
        delivery_units = request.POST.getlist("delivery_unit[]")

        for item, quantity, unit in zip(
            delivery_items,
            delivery_quantities,
            delivery_units,
        ):
            DeliveredItemsModel.objects.create(
                delivery=delivery,
                item=item,
                quantity=quantity,
                unit=unit,
            )


        # =============== FILES ===============
        attachments = request.FILES.getlist("project_deliveries__attachments")
        for attachment in attachments:
            if attachment.content_type.startswith("image/"):
                ProjectUploadedFiles.objects.create(
                    delivery=delivery,
                    caption=delivery.reference,
                    photo=attachment,
                    project=project,
                    uploaded_by_user=current_user,
                )
            else:
                ProjectUploadedFiles.objects.create(
                    delivery=delivery,
                    caption=delivery.reference,
                    file=attachment,
                    project=project,
                    uploaded_by_user=current_user,
                )

        # =============== CREATE PROJECT TIMELINE ===============
        ActivityModel.objects.create(
            company=company,
            project=project,
            user=current_user,
            activity_type='Delivery Created',
            description=f'{current_user.first_name} {current_user.last_name} added a delivery - {delivery.reference}',
            icon_type='delivery',
        )


        messages.success(
            request,
            f"✅ Delivery successfully logged."
        )

        # 🎯 Redirect To Projects
        url = reverse('projects:project-view', args=[project.uuid, ])
        return redirect(f"{url}#Deliveries")

    

# ============= Project Deliveries =============
def ProjectDeliveriesPageView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now()
    next_url = request.get_full_path()

    # ==================================================
    # Deliveries
    # ==================================================
    deliveries = DeliveryModel.objects.filter(
        Q(project=project)).order_by('-created_at')
    todays_deliveries_count = deliveries.filter(
                created_at__date=today
            ).count()

    delivery_target_id = "DeliveriesSessionList"

    context = {
        "current_user": current_user,
        "project": project,
        "deliveries": deliveries,
        "todays_deliveries_count"  : todays_deliveries_count,
        "delivery_target_id": delivery_target_id,
        "next_url": next_url,
        "today": today,
        "page": "projects/project_deliveries.html",
    }

    if request.htmx:
        return render(request, "projects/project_deliveries.html", context)
    return render(request, "client/base.html", context)


# ============= Delivery Details View =============
def DeliveryDetailsView(request, delivery_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    delivery = get_object_or_404(DeliveryModel,uuid = delivery_uuid)

    delivered_items = (
        delivery.delivered_item
        .all()
        .order_by("created_at")
    )

    attachments = (
        delivery.delivery_attachments_new
        .all()
        .select_related("uploaded_by_user")
    )


    context = {
        "current_user": current_user,
        "delivery": delivery,
        "delivered_items": delivered_items,
        "attachments": attachments,
        "page": "projects/delivery_details.html",
    }

    if request.htmx:
        return render(request, "projects/delivery_details.html", context)
    return render(request, "client/base.html", context)


# ============= Project Activity =============
def ProjectActivityDetailsPageView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)

    activities = ActivityModel.objects.filter(
        Q(project=project)).order_by('-created_at')

    grouped_activities = []

    for index, (date, activities_on_date) in enumerate(
        groupby(
            activities,
            key=lambda activity: timezone.localtime(activity.created_at).date()
        ),
        start=1
    ):
        grouped_activities.append({
            "id": index,
            "date": date,
            "activities": list(activities_on_date),
        })

    context = {
        "current_user": current_user,
        "project": project,
        "project_activity": grouped_activities,
        "page": "projects/project_activity.html",
    }

    if request.htmx:
        return render(request, "projects/project_activity.html", context)
    return render(request, "client/base.html", context)



# ============= Save Issue Offcanvas Partial =============
def SaveIssueOffcanvasView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now().date()
    issues_target_id = request.POST.get('issues_target_id', '')
    next_url = request.POST.get('next_url', '')
    

    assigned_to = request.POST.get('assigned_to', '').strip()
    assigned_user = None
    assigned_contractor = None
    activity_assignment = None

    if assigned_to != 'None':
        assignment_type, assignment_id = assigned_to.split('_', 1)
        if assignment_type == 'user':
            assigned_user = UserModel.objects.filter(id=assignment_id).first()
            activity_assignment = f"{assigned_user.first_name} {assigned_user.last_name}"
        elif assignment_type == 'contractor':
            assigned_contractor = ProjectContractor.objects.filter(id=assignment_id).first()
            activity_assignment = assigned_contractor.contractor.company_name

     # =============== Save New Issue ===============
    issue = IssueModel.objects.create(
        project=project,
        type='issue',
        title=request.POST.get("title"),
        description=request.POST.get("description"),
        priority=request.POST.get("priority"),
        due_date=request.POST.get("due_date"),
        assigned_to=assigned_user,
        assigned_contractor = assigned_contractor,
        created_by=current_user,
    )

    # =============== FILES ===============
    attachments = request.FILES.getlist("new-issue-attachments")
    for attachment in attachments:
        if attachment.content_type.startswith("image/"):
            ProjectUploadedFiles.objects.create(
                project=project,
                issue_task=issue,
                caption=issue.title,
                photo=attachment,
                uploaded_by_user=current_user,
            )
        else:
            ProjectUploadedFiles.objects.create(
                project=project,
                issue_task=issue,
                caption=issue.title,
                file=attachment,
                uploaded_by_user=current_user,
            )

    # =============== CREATE PROJECT TIMELINE ===============
    if activity_assignment:
        activity_description = (
            f"{current_user.first_name} {current_user.last_name} "
            f"created “{issue.title}” and assigned it to {activity_assignment}."
        )
    else:
        activity_description = (
            f"{current_user.first_name} {current_user.last_name} "
            f"created “{issue.title}”."
        )
    

    ActivityModel.objects.create(
        company=company,
        project=project,
        user=current_user,
        activity_type="Issue Created",
        description=activity_description,
        icon_type='issues',
    )

    if issues_target_id == 'IssuesSection':
        # GET UPDATED DATA 
        project_data = get_project_data(project=project, current_user=current_user)
        response = render(
            request,
            "issues_templates/issues_target_partial.html",
            {
                "project": project,
                "project_data":project_data,
                "current_user": current_user,
                "next_url": next_url,
                "issues_target_id":issues_target_id,
            },
        )
    else:
        project_issues = get_all_project_issues_data(project=project,current_user=current_user)
        issues = project_issues['issues_list']
        issues.sort(
            key=lambda item: item['issue'].status != 'open'
        )

        response = render(
            request,
            "partials/all_issues_partial.html",
            {
                "today": today,
                "current_user": current_user,
                "project": project,
                "project_issues": project_issues,
                "issues": issues,
                "next_url": next_url,
                "issues_target_id": issues_target_id,
            },
        )

    response["HX-Trigger"] = json.dumps({
        "corevaToast": {
            "title": "Issue Created",
            "message": "Issue successfully created."
        }
    })

    return response


# ============= Save Tasks Offcanvas Partial =============
def SaveTaskOffcanvasView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now().date()
    tasks_target_id = request.POST.get('tasks_target_id', '')
    next_url = request.POST.get('next_url', '')

    assigned_to = request.POST.get('assigned_to', '').strip()
    assigned_user = None
    assigned_contractor = None
    activity_assignment = None

    if assigned_to != 'None':
        assignment_type, assignment_id = assigned_to.split('_', 1)
        if assignment_type == 'user':
            assigned_user = UserModel.objects.filter(id=assignment_id).first()
            activity_assignment = f"{assigned_user.first_name} {assigned_user.last_name}"
        elif assignment_type == 'contractor':
            assigned_contractor = ProjectContractor.objects.filter(id=assignment_id).first()
            activity_assignment = assigned_contractor.contractor.company_name

     # =============== Save New Issue ===============
    issue = IssueModel.objects.create(
        project=project,
        type='task',
        title=request.POST.get("title"),
        description=request.POST.get("description"),
        priority=request.POST.get("priority"),
        due_date=request.POST.get("due_date"),
        assigned_to=assigned_user,
        assigned_contractor = assigned_contractor,
        created_by=current_user,
    )

    # =============== FILES ===============
    attachments = request.FILES.getlist("new-issue-attachments")
    for attachment in attachments:
        if attachment.content_type.startswith("image/"):
            ProjectUploadedFiles.objects.create(
                project=project,
                issue_task=issue,
                caption=issue.title,
                photo=attachment,
                uploaded_by_user=current_user,
            )
        else:
            ProjectUploadedFiles.objects.create(
                project=project,
                issue_task=issue,
                caption=issue.title,
                file=attachment,
                uploaded_by_user=current_user,
            )

    # =============== CREATE PROJECT TIMELINE ===============
    if activity_assignment:
        activity_description = (
            f"{current_user.first_name} {current_user.last_name} "
            f"created “{issue.title}” and assigned it to {activity_assignment}."
        )
    else:
        activity_description = (
            f"{current_user.first_name} {current_user.last_name} "
            f"created “{issue.title}”."
        )
    

    ActivityModel.objects.create(
        company=company,
        project=project,
        user=current_user,
        activity_type="Task Created",
        description=activity_description,
        icon_type='tasks',
    )

    if tasks_target_id == 'TaskSession':
        # GET UPDATED DATA 
        project_data = get_project_data(project=project, current_user=current_user)

        response = render(
            request,
            "tasks_templates/tasks_target_partial.html",
            {
                "project": project,
                "project_data":project_data,
                "current_user": current_user,
                "next_url": next_url,
                "tasks_target_id": tasks_target_id,
            },
        )
    else:
        project_tasks = get_all_project_tasks_data(project=project,current_user=current_user)
        tasks = project_tasks['tasks_list']
        tasks.sort(
            key=lambda item: item['task'].status != 'open'
        )

        response = render(
            request,
            "partials/all_tasks_partial.html",
            {
                "today": today,
                "current_user": current_user,
                "project": project,
        
                # NEW DATA 
                "project_tasks": project_tasks,
                "tasks": tasks,
                "next_url": next_url,
                "tasks_target_id": tasks_target_id,
            },
        )

    response["HX-Trigger"] = json.dumps({
        "corevaToast": {
            "title": "Task Created",
            "message": "Task successfully created."
        }
    })

    return response



# ============= Save Incident Offcanvas Partial =============
def SaveIncidentOffcanvas(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now()
    incidents_target_id = request.POST.get('incidents_target_id', '')
    next_url = request.POST.get('next_url', '')

    # =============== CREATE INCIDENT ===============
    incident = IncidentModel.objects.create(
        project=project,
        incident_date=request.POST.get("incident_date"),
        incident_time=request.POST.get("incident_time"),
        title=request.POST.get("title"),
        work=request.POST.get("activity"),
        description=request.POST.get("description"),
        action_taken=request.POST.get("immediate_action"),
        severity=request.POST.get("severity"),
        incident_type=request.POST.get("incident_type"),
        weather_conditions=request.POST.get("weather_condition"),
        location=request.POST.get("location"),
        created_by=current_user,
    )

    # =============== INJURED PERSONS ===============
    first_names = request.POST.getlist("injured_first_name[]")
    last_names = request.POST.getlist("injured_last_name[]")
    injuries = request.POST.getlist("injured_injury[]")
    body_parts = request.POST.getlist("injured_body_part[]")
    treatments = request.POST.getlist("injured_treatment[]")

    for first_name, last_name, injury, body_part, treatment in zip(
        first_names,
        last_names,
        injuries,
        body_parts,
        treatments,
    ):
        InjuredPersonModel.objects.create(
            incident=incident,
            first_name=first_name,
            last_name=last_name,
            injury=injury,
            body_part=body_part,
            treatment=treatment,
        )

    # =============== WITNESS ===============
    witness_names = request.POST.getlist("witness_name[]")
    witness_contacts = request.POST.getlist("witness_contact[]")
    for name, contact in zip(
        witness_names,
        witness_contacts
    ):
        WitnessModel.objects.create(
            incident=incident,
            full_name=name,
            contract=contact,
        )


    # =============== FILES ===============
    attachments = request.FILES.getlist("project_incidents__attachments")
    for attachment in attachments:
        if attachment.content_type.startswith("image/"):
            ProjectUploadedFiles.objects.create(
                incident=incident,
                caption=incident.title,
                photo=attachment,
                project=project,
                uploaded_by_user=current_user,
            )
        else:
            ProjectUploadedFiles.objects.create(
                incident=incident,
                caption=incident.title,
                file=attachment,
                project=project,
                uploaded_by_user=current_user,
            )

    # =============== CREATE PROJECT TIMELINE ===============
    ActivityModel.objects.create(
        company=company,
        project=project,
        user=current_user,
        activity_type='Incident Created',
        description=f'{current_user.first_name} {current_user.last_name} logged incident "{incident.title}"',
        icon_type='incident',
    )


    

    if incidents_target_id == 'IncidentsSession':
        # GET UPDATED DATA 
        project_data = get_project_data(project=project, current_user=current_user)
        incidents = project_data['incidents']
        incidents_count = incidents.count()

        response = render(
            request,
            "partials/incident_target_partial.html",
            {
                "project": project,
                "project_data":project_data,
                "incidents": incidents,
                "incidents_count": incidents_count,
                "current_user": current_user,
                "next_url": next_url,
                "incidents_target_id": incidents_target_id,
                "today": today,
            },
        )
    else:
        incidents = IncidentModel.objects.filter(
            Q(project=project)).order_by('-created_at')
        todays_incidents_count = incidents.filter(
                created_at__date=today
            ).count()

        response = render(
            request,
            "partials/all_incidents_partial.html",
            {
                "project": project,
                "incidents": incidents,
                "todays_incidents_count": todays_incidents_count,
                "current_user": current_user,
                "next_url": next_url,
                "incidents_target_id": incidents_target_id,
                "today": today,
            },
        )

    response["HX-Trigger"] = json.dumps({
        "corevaToast": {
            "title": "Incident Created",
            "message": "incident successfully created."
        }
    })

    return response



# ============= Save Delivery Offcanvas Partial =============
def SaveDeliveryOffcanvas(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now()
    next_url = request.POST.get('next_url', '')
    delivery_target_id = request.POST.get('delivery_target_id', '')

    # Create Delivery Object
    delivery = DeliveryModel.objects.create(
        project=project,
        delivery_date=request.POST.get("delivery_date"),
        delivery_time=request.POST.get("delivery_time"),
        supplier=request.POST.get("supplier"),
        notes=request.POST.get("notes"),
        status=request.POST.get("status"),
        created_by=current_user,
    )


    # =============== DELIVERIES ITEMS ===============
    delivery_items = request.POST.getlist("delivery_item[]")
    delivery_quantities = request.POST.getlist("delivery_quantity[]")
    delivery_units = request.POST.getlist("delivery_unit[]")

    for item, quantity, unit in zip(
        delivery_items,
        delivery_quantities,
        delivery_units,
    ):
        DeliveredItemsModel.objects.create(
            delivery=delivery,
            item=item,
            quantity=quantity,
            unit=unit,
        )

    # =============== FILES ===============
    attachments = request.FILES.getlist("project_deliveries__attachments")
    for attachment in attachments:
        if attachment.content_type.startswith("image/"):
            ProjectUploadedFiles.objects.create(
                delivery=delivery,
                caption=delivery.reference,
                photo=attachment,
                project=project,
                uploaded_by_user=current_user,
            )
        else:
            ProjectUploadedFiles.objects.create(
                delivery=delivery,
                caption=delivery.reference,
                file=attachment,
                project=project,
                uploaded_by_user=current_user,
            )

   
    # =============== CREATE PROJECT TIMELINE ===============
    ActivityModel.objects.create(
        company=company,
        project=project,
        user=current_user,
        activity_type='Delivery Created',
        description=f'{current_user.first_name} {current_user.last_name} logged a delivery "{delivery.reference}" ',
        icon_type='delivery',
    )

     # CHECK WHICH PAGE ITS ON PROJECT DETAILS OR DELIVERIES LIST PAGE 
    if delivery_target_id == 'DeliveriesSession':
        # GET UPDATED DATA 
        project_data = get_project_data(project=project, current_user=current_user)
        deliveries = project_data['deliveries']
        deliveries_count = deliveries.count()


        response = render(
            request,
            "deliveries/delivery_target_partial.html",
            {
                "project": project,
                "project_data":project_data,
                "current_user": current_user,
                "deliveries": deliveries,
                "deliveries_count": deliveries_count,
                "next_url": next_url,
                "today": today,
                "delivery_target_id": delivery_target_id,
            },
        )
    else:
        # ==================================================
        # Deliveries
        # ==================================================
        deliveries = DeliveryModel.objects.filter(
            Q(project=project)).order_by('-created_at')
        todays_deliveries_count = deliveries.filter(
                    created_at__date=today
                ).count()
    
        delivery_target_id = "DeliveriesSessionList"

        response = render(
            request,
            "partials/all_deliveries_component_partial.html",
            {
                "project": project,
                "current_user": current_user,
                "deliveries": deliveries,
                "todays_deliveries_count": todays_deliveries_count,
                "next_url": next_url,
                "today": today,
                "delivery_target_id": delivery_target_id,
            },
        )


    response["HX-Trigger"] = json.dumps({
        "corevaToast": {
            "title": "Delivery Created",
            "message": "Delivery successfully logged."
        }
    })

    return response



# ============= Save Project Photos Offcanvas Partial =============
def SaveProjectPhotosOffcanvas(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.localdate()

    title=request.POST.get("title")

    # =============== FILES ===============
    attachments = request.FILES.getlist("project_photos__attachments")

    for attachment in attachments:
        if attachment.content_type.startswith("image/"):
            ProjectUploadedFiles.objects.create(
                reference='Site Activity',
                caption=title,
                photo=attachment,
                project=project,
                uploaded_by_user=current_user,
            )
        else:
            ProjectUploadedFiles.objects.create(
                reference='Site Activity',
                caption=title,
                file=attachment,
                project=project,
                uploaded_by_user=current_user,
            )

    # =============== CREATE PROJECT TIMELINE ===============
    ActivityModel.objects.create(
        company=company,
        project=project,
        user=current_user,
        activity_type='Site Attachment',
        description=f'{current_user.first_name} {current_user.last_name} added site attachment "{title}"',
        icon_type='photos',
    )

    site_attachments = ProjectUploadedFiles.objects.filter(Q(project=project) & Q(reference='Site Activity') & Q(created_at=today)).order_by("-created_at")


    response = render(
        request,
        "project_attachments/projects_attachments_partials.html",
        {
            "project": project,
            "current_user": current_user,
            "today": today,
            "site_attachments": site_attachments,
        },
    )


    response["HX-Trigger"] = json.dumps({
        "corevaToast": {
            "title": "Photos & Attachments",
            "message": "Photo or attachment added successfully."
        }
    })

    return response