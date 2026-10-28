from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q


# Models Import 
from projects.models import *
from issues.models import *



# ============= Project Team Members =============
def ProjectTeamMembersView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)


    team_members = UserModel.objects.filter(
        company=current_user.company
    ).filter(
        Q(role="admin") |
        Q(
            project_user__project=project,
            project_user__status="active"
        )
    ).distinct()


    company_users = UserModel.objects.filter(
        company=company,
        is_active=True,
    ).exclude(
        uuid__in=team_members.values_list(
            "uuid",
            flat=True
        )
    )


    # search = request.GET.get("search", "").strip()
    # role = request.GET.get("role", "").strip()

    # if search:
    #     team_members = team_members.filter(
    #         project_user__first_name__icontains=search
    #     ) | team_members.filter(
    #         project_user__last_name__icontains=search
    #     ) | team_members.filter(
    #         project_user__email__icontains=search
    #     ) | team_members.filter(
    #         project_user__job_title__icontains=search
    #     )

    # if role:
    #     team_members = team_members.filter(
    #         project_user__role=role
    #     )

    context = {
        "project": project,
        "team_members": team_members,

        "total_members": team_members.count(),

        "admin_count": team_members.filter(
            role="admin").count(),

        "user_count": ProjectUserModel.objects.filter(
            project=project,
            project_user__role="user",
            project_user__isnull=False
        ).count(),

        "company_users" : company_users,
        "page": "team/project_team_members.html",
    }

    if request.htmx:
        return render(request, "team/project_team_members.html", context)
    return render(request, "client/base.html", context)


# ============= Save New Contractor =============
@require_POST
def add_team_member(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)

    member_uuid=request.POST.get("project_user_uuid")
    member = get_object_or_404(UserModel, uuid=member_uuid)


    project_user_check = ProjectUserModel.objects.filter(
        project=project,
        project_user=member
    ).first()

    # check if user has active account 
    if project_user_check:
        if project_user_check.status == "inactive":
            project_user_check.status = "active"
            project_user_check.added_by = current_user
            project_user_check.save()
    else:
        # Add To Project
        ProjectUserModel.objects.create(
            project=project,
            project_user=member,
            added_by=current_user,
        )


    messages.success(
        request,
        f"✅ {member.first_name} {member.last_name} successfully added."
    )

    # 🎯 Redirect To Projects
    url = reverse('team:project-team', args=[project.uuid, ])
    return redirect(f"{url}#member-{member.uuid }")

# ============= Member Details Page =============
def MemberDetailsPage(request,project_uuid, member_uuid):
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    user = get_object_or_404(UserModel, uuid=member_uuid)

    if user.role == "admin":
        member = {}
        assigned_items = (
            IssueModel.objects
            .filter(
                assigned_to=user,
                project=project,
            )
            .select_related(
                "project",
                "inspection",
                "daily_report",
                "created_by",
                "closed_by",
            )
            .order_by("-created_at")
        )
    else:
        member = get_object_or_404(ProjectUserModel,
            project=project,
            project_user=user
        )
    
        assigned_items = (
            IssueModel.objects
            .filter(
                assigned_to=user,
                project=member.project,
            )
            .select_related(
                "project",
                "inspection",
                "daily_report",
                "created_by",
                "closed_by",
            )
            .order_by("-created_at")
        )

    assigned_issues = assigned_items.filter(type="issue")
    assigned_tasks = assigned_items.filter(type="task")

    open_issues = assigned_issues.filter(status="open")
    closed_issues = assigned_issues.filter(status="closed")

    open_tasks = assigned_tasks.filter(status="open")
    closed_tasks = assigned_tasks.filter(status="closed")


     # member = get_object_or_404(
    #     ProjectUserModel.objects.select_related(
    #         "project",
    #         "project_user",
    #         "added_by",
    #     ),
    #     project_user=user,
    # )

    context = {
        "member": member,
        "project": project,
        "user": user,

        "assigned_issues": assigned_issues,
        "assigned_tasks": assigned_tasks,

        "total_items": assigned_items.count(),

        "issue_count": assigned_issues.count(),
        "task_count": assigned_tasks.count(),

        "open_issues_count": open_issues.count(),
        "closed_issues_count": closed_issues.count(),

        "open_tasks_count": open_tasks.count(),
        "closed_tasks_count": closed_tasks.count(),
        "page": "team/member_details.html",
    }


    if request.htmx:
        return render(request, "team/member_details.html", context)
    return render(request, "client/base.html", context)



# ============= Save New Contractor =============
@require_POST
def remove_member_project(request, project_uuid,member_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    user = get_object_or_404(UserModel, uuid=member_uuid)

    project_user = get_object_or_404(ProjectUserModel,
        project=project,
        project_user=user
    )

    project_user.status = "inactive"
    project_user.removed_by = current_user
    project_user.save()

    messages.success(
        request,
        f"✅ Team member successfully removed."
    )

    # 🎯 Redirect To Projects
    url = reverse('team:project-team', args=[project.uuid, ])
    return redirect(f"{url}")




# ============= Company Team =============
def CompanyTeamView(request):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    team_members = UserModel.objects.filter( company=company).order_by('-date_created')
    pending_invitations = UserInvite.objects.filter(
        company=company,
        is_used=False
    ).select_related('user')


    pending_invitations = UserInvite.objects.filter(
        company=company,
        is_used=False
    ).select_related('user')


    context = {
        "company": company,
        "team_members" : team_members,
        "total_members": team_members.count(),
        
        "admin_count": team_members.filter(
            role="admin").count(),

        "user_count": team_members.filter(
            role="user").count(),
        "pending_invitations": pending_invitations,

        "page": "team/company_team.html",
    }

    if request.htmx:
        return render(request, "team/company_team.html", context)
    return render(request, "client/base.html", context)



# ============= Company Team =============
# ============= Company Team =============
def TeamMemberDetailsView(request, member_uuid):
    user = request.user

    current_user = get_object_or_404(
        UserModel,
        user=user
    )

    company = current_user.company

    member = get_object_or_404(
        UserModel,
        uuid=member_uuid
    )

    if member.role == "admin":

        # Admins can see all projects belonging to the company
        projects = (
            ProjectModel.objects
            .filter(company=company)
            .select_related("location")
            .order_by("-created_at")
        )

    else:
        # Normal users can only see projects assigned to them
        projects = (
            ProjectModel.objects
            .filter(
                project__project_user=member,
                company=company,
                project__status='active',
            )
            .select_related("location")
            .distinct()
            .order_by("-created_at")
        )

    project_count = projects.count()

    context = {
        "company": company,
        "member": member,
        "projects": projects,
        "project_count": project_count,

        "page": "team/team_member_details.html",
    }

    if request.htmx:
        return render(
            request,
            "team/team_member_details.html",
            context
        )

    return render(
        request,
        "client/base.html",
        context
    )