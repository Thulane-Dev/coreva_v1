from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q


# Models Import
from authentication.models import UserModel
from account.models import *
from projects.models import *
from inspections.models import *


# Services Import
from .services.dashboard_view import (
    get_all_projects_data
)



# ============= Todays Dashboard New =============
def TodaysDashboardViewNew(request):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    today = timezone.now()

    if current_user.role == 'admin':
            user_projects = ProjectModel.objects.filter(
                company=company
            ).order_by('created_at')
    
    elif current_user.role == 'user':
        user_projects = ProjectModel.objects.filter(Q(project__project_user=current_user) & Q(project__status="active")).order_by('created_at')

    projects_data = get_all_projects_data(
        company=company, current_user=current_user)
    total_projects = projects_data['total_projects']
    projects = projects_data['projects_list']

    current_hour = timezone.localtime().hour

    if current_hour < 12:
        greeting = "Good morning"
    elif current_hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    project_count = len(user_projects)

    context = {
        "current_user": current_user,
        "today": today,
        "user_projects": user_projects,
        "projects_data": projects_data,
        "projects": projects,
        "total_projects": total_projects,
        "greeting" : greeting,
        "project_count": project_count,
        "page": "dashboard/todays_page.html",
    }


    if request.htmx:
        return render(request, "dashboard/todays_page.html", context)
    return render(request, "client/base.html", context)



def FilterProjectsView(request):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company

    projects_data = get_all_projects_data(
        company=company, current_user=current_user)
    projects = projects_data['projects_list']

    # SEARCH FILTER
    query = request.POST.get("query", "").strip()
    if query:
        projects = [
            item for item in projects
            if query.lower() in item['project'].project_name.lower()
        ]


    # OVERALL STATUS FILTER
    overall_status = request.POST.get("overall_status", "").strip()
    if overall_status:
        projects = [
            item for item in projects
            if item['overall_status'] == overall_status
        ]

    # PROJECT STATUS 
    project_status = request.POST.get("project_status", "").strip()
    if project_status:
        projects = [
            item for item in projects
            if item['project_status'] == project_status
        ]


    return render(
        request,
        "partials/todays_projects_partial.html",
        {
            "current_user": current_user,
            "projects" : projects,
        },
    )
