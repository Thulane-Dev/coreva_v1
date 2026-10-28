from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from django.db.models import Prefetch
from datetime import date
from urllib.parse import urlencode

# htmx
from django.http import HttpResponse
import json

# Models Import
from .models import *
from projects.models import *
from authentication.models import *


from .services.issues_view import (
    get_all_project_issues_data,
    get_all_project_tasks_data,
)



# ============= ISSUES PLACEHOLDER =============
def IssuesPlaceHolder(request):

    context = {
        "page": "issues/issues_placeholder.html",
    }

    if request.htmx:
        return render(request, "issues/issues_placeholder.html", context)
    return render(request, "client/base.html", context)

# ============= ADD PROJECT ISSUE =============
def AddIssueView(request, project_uuid):
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
    ).distinct().order_by('date_created')
    contractors = ProjectContractor.objects.filter(project=project).order_by('created_at')
    today = timezone.now()

    current_url = request.resolver_match.url_name
    if current_url == 'add-task':
        page_title = 'Add Task'
        save_btn = 'Save Task'
        section_text = 'Task'
        description_text = 'Task Description'
        icon = 'bi bi-check2-square'
        sub_title = 'Add a task that needs be completed.'
    else:
        page_title = 'Add Issue'
        save_btn = 'Save Issue'
        section_text = 'Issue'
        description_text = 'Description'
        icon = 'bi bi-exclamation-triangle-fill'
        sub_title = 'Record an issue that needs attention, tracking or resolution.'

    back_url = request.GET.get("back_url") or reverse(
        "issues:project-issues",
        args=[project.uuid],
    )

    context = {
        "project": project,
        "team_members": team_members,
        "contractors": contractors,
        "today": today,
        "page_title": page_title,
        "save_btn": save_btn,
        "sub_title": sub_title,
        "section_text": section_text,
        "description_text": description_text,
        "icon": icon,
        "back_url" : back_url,
        "page": "issues/add_issue.html",
    }

    if request.htmx:
        return render(request, "issues/add_issue.html", context)
    return render(request, "client/base.html", context)


# ============= SAVE PROJECT ISSUE FUNCTION =============
@require_POST
def save_issue_post(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    current_url = request.resolver_match.url_name
    # Get just the date
    today = timezone.now().date()

    if request.method == "POST":
        # Assigned Team Member
        assigned_to_id = request.POST.get("team_id")

        if assigned_to_id != 'None':
            assigned_to = UserModel.objects.filter(id=assigned_to_id).first()
        else:
            assigned_to = None

        title = request.POST.get("title")


        # check if contractor selected 
        contractor_id = request.POST.get("contractor_id")
        if contractor_id != 'None':
            assigned_contractor = ProjectContractor.objects.filter(id=contractor_id).first()
        else:
            assigned_contractor = None
        

        save_type = request.POST.get("save_type")
        if save_type == 'Issue':
            return_url = 'issue'
            activity_type = 'Issue Created'
            description_text = 'issue'
            document_type = 'issue'
            caption = title
            messages.success(
                request,
                f"✅ Issue successfully added."
            )
        else:
            return_url = 'task'
            activity_type = 'Task Created'
            description_text = 'task'
            document_type = 'task'
            caption = title
            messages.success(
                request,
                f"✅ Task successfully created."
            )

        # =============== Save New Issue ===============
        issue = IssueModel.objects.create(
            project=project,
            type=document_type,
            title=caption,
            description=request.POST.get("description"),
            priority=request.POST.get("priority"),
            assigned_to=assigned_to,
            due_date=request.POST.get("due_date"),
            created_by=current_user,
            assigned_contractor = assigned_contractor,
        )

        # =============== Save Photos Evidence ===============
        files = request.FILES.getlist("files")
        for i in files:
            ProjectUploadedFiles.objects.create(
                issue_task=issue,
                caption=caption,
                photo=i,
                project=project,
                uploaded_by_user=current_user,
            )


        # =============== FILES ===============
        attachments = request.FILES.getlist("project_issues__attachments")
        for attachment in attachments:
            if attachment.content_type.startswith("image/"):
                ProjectUploadedFiles.objects.create(
                    issue_task=issue,
                    caption=caption,
                    photo=attachment,
                    project=project,
                    uploaded_by_user=current_user,
                )
            else:
                ProjectUploadedFiles.objects.create(
                    issue_task=issue,
                    caption=caption,
                    file=attachment,
                    project=project,
                    uploaded_by_user=current_user,
                )

        # =============== CREATE PROJECT TIMELINE ===============
        # ISSUE TIMELINE
        if save_type == 'Issue':
            ActivityModel.objects.create(
                company=company,
                project=project,
                user=current_user,
                activity_type='Issue Created',
                description=f'{current_user.first_name} {current_user.last_name} created an issue - {caption}',
                icon_type='issue',
            )

            if assigned_to:
                ActivityModel.objects.create(
                    company=company,
                    project=project,
                    user=current_user,
                    activity_type='Issue Assigned',
                    description=f'{current_user.first_name} {current_user.last_name} assigned - {caption} - issue to {assigned_to.first_name} {assigned_to.last_name}',
                    icon_type='issue',
                )
        # TASK TIMELINE
        else:
            ActivityModel.objects.create(
                company=company,
                project=project,
                user=current_user,
                activity_type='Task Created',
                description=f'{current_user.first_name} {current_user.last_name} created a task - {caption}',
                icon_type='tasks',
            )

            if assigned_to:
                ActivityModel.objects.create(
                    company=company,
                    project=project,
                    user=current_user,
                    activity_type='Task Assigned',
                    description=f'{current_user.first_name} {current_user.last_name} assigned - {caption} - task to {assigned_to.first_name} {assigned_to.last_name}',
                    icon_type='tasks',
                )

        # Back destination: this project's issues list
        if issue.type == 'issue':
            back_url = reverse(
                "issues:project-issues",
                args=[issue.project.uuid],
            )
            # Redirect to issue details, preserving back_url
            url = reverse("issues:issue", args=[issue.uuid])
        else:
            back_url = reverse(
                "issues:project-tasks",
                args=[issue.project.uuid],
            )
            # Redirect to tasks details, preserving back_url
            url = reverse("issues:task", args=[issue.uuid])
        
        return redirect(f"{url}?{urlencode({'back_url': back_url})}")


# ============= Project Issues =============
def ProjectIssuesPageView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now().date()

    project_issues = get_all_project_issues_data(project=project,current_user=current_user)
    issues = project_issues['issues_list']
    issues.sort(
        key=lambda item: item['issue'].status != 'open'
    )

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
    issues_target_id = "ProjectIssuesSection"

    context = {
        "today": today,
        "current_user": current_user,
        "project": project,
        "project_issues": project_issues,
        "issues": issues,
        "next_url": next_url,
        "issues_target_id": issues_target_id,
        "team_members": team_members,
        "project_contractors": project_contractors,
        "page": "issues/project_issues.html",
    }

    if request.htmx:
        return render(request, "issues/project_issues.html", context)
    return render(request, "client/base.html", context)


# ============= Project Tasks =============
def ProjectTasksPageView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now().date()

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

    project_tasks = get_all_project_tasks_data(project=project,current_user=current_user)
    tasks = project_tasks['tasks_list']
    tasks.sort(
        key=lambda item: item['task'].status != 'open'
    )



    # next_url = request.GET.get("next")
    next_url = request.get_full_path()
    tasks_target_id = "ProjectTasksSection"

    context = {
        "today": today,
        "current_user": current_user,
        "project": project,
        "team_members": team_members,
        "project_contractors": project_contractors,

        # NEW DATA 
        "project_tasks": project_tasks,
        "tasks": tasks,
        "next_url": next_url,
        "tasks_target_id": tasks_target_id,
        "page": "issues/project_tasks.html",
    }

    if request.htmx:
        return render(request, "issues/project_tasks.html", context)
    return render(request, "client/base.html", context)


# ============= VIEW ISSUE PAGE =============
def IssuePreview(request, issue_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company

    # Get the issue and its related objects
    issue = get_object_or_404(
        IssueModel.objects.select_related(
            "project",
            "inspection",
            "inspection_response",
            "daily_report",
            "assigned_to",
            "created_by",
        ),
        uuid=issue_uuid,
    )

    attachments = ProjectUploadedFiles.objects.filter(issue_task=issue).order_by('-created_at')

    comments = (
        IssueCommentModel.objects
        .filter(issue=issue)
        .select_related("comment_by")
        .prefetch_related("comment_attachments")
        .order_by("-created_at")
    )

    # Team Members
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')

    # Contractors 
    contractors = ProjectContractor.objects.filter(project=issue.project).order_by('created_at')

    # User work progress
    # work_stages = (
    #     WorkStageModel.objects
    #     .filter(Q(issue=issue) & Q(created_by_team=current_user))
    #     .select_related("created_by_team")
    #     .prefetch_related("work_stage_attachments")
    #     .order_by("-created_at")
    # )


    work_stages = (
        WorkStageModel.objects
        .filter(
            Q(issue=issue) &
            (
                Q(created_by_team=current_user) |
                Q(created_by_contractor__isnull=False)
            )
        )
        .select_related(
            "created_by_team",
            "created_by_contractor"
        )
        .prefetch_related("work_stage_attachments")
        .order_by("-created_at")
    )

    back_url = request.GET.get("back_url") or reverse(
        "issues:project-issues",
        args=[issue.project.uuid],
    )

    IssueActivityView.objects.update_or_create(
        issue=issue,
        user=current_user,
        defaults={
            "last_viewed_at": timezone.now()
        }
    )

    context = {
        "issue": issue,
        "comments": comments,
        "team_members": team_members,
        "today": timezone.localdate(),
        "work_stages": work_stages,
        "contractors" : contractors,
        "attachments" : attachments,
        "back_url" :back_url,
        "page": "issues/issue_preview.html",
    }

    if request.htmx:
        return render(request, "issues/issue_preview.html", context)
    return render(request, "client/base.html", context)


# ============= DELETE THIS UPDATE ISSUE POST METHOD =============
def save_issue_update(request):

    if request.method == "POST":
        name = request.POST.get("name")

        url = reverse(
            "issues:issues",
        )

        response = HttpResponse(status=200)

        # response["HX-Location"] = json.dumps({
        #     "path": url,
        #     "target": "#content",
        #     "swap": "innerHTML",
        # })

        response["HX-Location"] = json.dumps({
            "path": f"{url}#issueTargetPlaceID",
            "target": "#content",
            "swap": "innerHTML",
        })

        return response


# ============= Save Issue Comment =============
def save_issue_comment(request, issue_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    issue = IssueModel.objects.filter(uuid=issue_uuid).first()
    project = issue.project

    comment = IssueCommentModel.objects.create(
        issue=issue,
        comment=request.POST.get("comment"),
        comment_by=current_user,
    )

    # =============== FILES ===============
    attachments = request.FILES.getlist("comment_attachments")
    for attachment in attachments:
        if attachment.content_type.startswith("image/"):
            ProjectUploadedFiles.objects.create(
                project=project,
                comment=comment,
                caption=issue.title,
                photo=attachment,
                uploaded_by_user=current_user,
            )
        else:
            ProjectUploadedFiles.objects.create(
                project=project,
                comment=comment,
                caption=issue.title,
                file=attachment,
                uploaded_by_user=current_user,
            )

    # Comments for this issue
    comments = (
        IssueCommentModel.objects
        .filter(issue=issue)
        .select_related("comment_by")
        .prefetch_related("comment_attachments")
        .order_by("created_at")
    )

    message = "Comment added successfully."

    return render(
        request,
        "partials/issue_comments_partial.html",
        {
            "issue": issue,
            "comments": comments,
            "message": message,
        },
    )


# ============= Mark Comment as read =============
def mark_issue_read(request, issue_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    issue = IssueModel.objects.filter(uuid=issue_uuid).first()

    comment_uuid = request.POST.get("comment_uuid")
    comment = IssueCommentModel.objects.filter(uuid=comment_uuid).first()
    comment.is_read = True
    comment.save()

    # Comments for this issue
    comments = (
        IssueCommentModel.objects
        .filter(issue=issue)
        .select_related("comment_by")
        .order_by("created_at")
    )

    message = "Comment updated successfully."

    return render(
        request,
        "partials/issue_comments_partial.html",
        {
            "issue": issue,
            "comments": comments,
            "message": message,
        },
    )


# ============= Update Issue Status =============
@require_POST
def update_issue_status(request, issue_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    today = timezone.now()
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company

    # Assigned Team Member
    assigned_to_id = request.POST.get("assigned_to_id")

    if assigned_to_id != 'None':
        assigned_to = UserModel.objects.filter(id=assigned_to_id).first()
    else:
        assigned_to = None

    issue = IssueModel.objects.filter(uuid=issue_uuid).first()
    issue.status = request.POST.get("status")
    issue.priority = request.POST.get("priority")
    issue.due_date = request.POST.get("due_date")
    issue.assigned_to = assigned_to
    issue.closed_at = today
    issue.assigned_to = assigned_to
    issue.closed_by = current_user
    issue.save()

    messages.success(
        request,
        f"Successfully updated."
    )

    ActivityModel.objects.create(
        company=company,
        project=issue.project,
        user=current_user,
        activity_type=f'Issue {issue.status}',
        description=f'{current_user.first_name} {current_user.last_name} {issue.status} issue - {issue.title}',
        icon_type='issue',
    )

    if issue.status == 'closed':
        comments = IssueCommentModel.objects.filter(
            Q(issue=issue) & Q(is_read=False))
        for issue_comment in comments:
            issue_comment.is_read = True
            issue_comment.save()

    

    # Back destination: this project's issues list
    if issue.type == 'issue':
        back_url = reverse(
            "issues:project-issues",
            args=[issue.project.uuid],
        )
        # Redirect to issue details, preserving back_url
        url = reverse("issues:issue", args=[issue.uuid])
    else:
        back_url = reverse(
            "issues:project-tasks",
            args=[issue.project.uuid],
        )

        # Redirect to tasks details, preserving back_url
        url = reverse("issues:task", args=[issue.uuid])
    
    return redirect(f"{url}?{urlencode({'back_url': back_url})}")


# ============= VIEW ISSUE PAGE =============
def TasksPreview(request, issue_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    view_type = 'Task'

    # Get the issue and its related objects
    issue = get_object_or_404(
        IssueModel.objects.select_related(
            "project",
            "inspection",
            "inspection_response",
            "daily_report",
            "assigned_to",
            "created_by",
        ),
        uuid=issue_uuid,
    )

    attachments = ProjectUploadedFiles.objects.filter(issue_task=issue).order_by('-created_at')

    comments = (
        IssueCommentModel.objects
        .filter(issue=issue)
        .select_related("comment_by")
        .prefetch_related("comment_attachments")
        .order_by("-created_at")
    )

    # Team Members
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')

    # Contractors 
    contractors = ProjectContractor.objects.filter(project=issue.project).order_by('created_at')

    # User work progress
    work_stages = (
        WorkStageModel.objects
        .filter(
            Q(issue=issue) &
            (
                Q(created_by_team=current_user) |
                Q(created_by_contractor__isnull=False)
            )
        )
        .select_related(
            "created_by_team",
            "created_by_contractor"
        )
        .prefetch_related("work_stage_attachments")
        .order_by("-created_at")
    )

    back_url = request.GET.get("back_url") or reverse(
        "issues:project-issues",
        args=[issue.project.uuid],
    )

    IssueActivityView.objects.update_or_create(
        issue=issue,
        user=current_user,
        defaults={
            "last_viewed_at": timezone.now()
        }
    )

    context = {
        "issue": issue,
        "comments": comments,
        "team_members": team_members,
        "today": timezone.localdate(),
        "work_stages" : work_stages,
        "contractors": contractors,
        "attachments":attachments,
        "back_url" : back_url,
        "page": "issues/task_preview.html",
    }

    if request.htmx:
        return render(request, "issues/task_preview.html", context)
    return render(request, "client/base.html", context)


# ============= Save Item Comment =============
def save_item_comment(request, issue_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    issue = IssueModel.objects.filter(uuid=issue_uuid).first()
    project = issue.project

    comment = IssueCommentModel.objects.create(
        issue=issue,
        comment=request.POST.get("comment"),
        comment_by=current_user,
    )

    # =============== FILES ===============
    attachments = request.FILES.getlist("comment_attachments")
    for attachment in attachments:
        if attachment.content_type.startswith("image/"):
            ProjectUploadedFiles.objects.create(
                project=project,
                comment=comment,
                caption=issue.title,
                photo=attachment,
                uploaded_by_user=current_user,
            )
        else:
            ProjectUploadedFiles.objects.create(
                project=project,
                comment=comment,
                caption=issue.title,
                file=attachment,
                uploaded_by_user=current_user,
            )

    # Comments for this issue
    comments = (
        IssueCommentModel.objects
        .filter(issue=issue)
        .select_related("comment_by")
        .prefetch_related("comment_attachments")
        .order_by("-created_at")
    )

    if issue.type == 'issue':
        return render(
            request,
            "partials/item_comments_partial.html",
            {
                "issue": issue,
                "comments": comments,
                "current_user" : current_user,
            },
        )
    else:
        return render(
            request,
            "partials/task_item_comments_partial.html",
            {
                "issue": issue,
                "comments": comments,
                "current_user" : current_user,
            },
        )


# ============= Mark Comment as read =============
def mark_item_as_read(request, issue_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    issue = IssueModel.objects.filter(uuid=issue_uuid).first()
    comment_uuid = request.POST.get("comment_uuid")
    comment = IssueCommentModel.objects.filter(uuid=comment_uuid).first()
    comment.is_read = True
    comment.save()

    # Comments for this issue
    comments = (
        IssueCommentModel.objects
        .filter(issue=issue)
        .select_related("comment_by")
        .order_by("-created_at")
    )

    if issue.type == 'issue':
        return render(
            request,
            "partials/item_comments_partial.html",
            {
                "issue": issue,
                "comments": comments,
                "current_user" : current_user,
            },
        )
    else:
        return render(
            request,
            "partials/task_item_comments_partial.html",
            {
                "issue": issue,
                "comments": comments,
                "current_user" : current_user,
            },
        )


# ============= SAVE CONTRACTOR WORK STAGE =============
def save_user_work_stage(request, issue_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    issue = IssueModel.objects.filter(uuid=issue_uuid).first()
    project = issue.project

    work_stage = WorkStageModel.objects.create(
        issue=issue,
        status=request.POST.get("work_status"),
        update=request.POST.get("comment"),
        created_by_team=current_user,
    )

    # =============== FILES ===============
    attachments = request.FILES.getlist("stage_attachments")
    for attachment in attachments:
        if attachment.content_type.startswith("image/"):
            ProjectUploadedFiles.objects.create(
                project=project,
                work_stage=work_stage,
                caption=issue.title,
                photo=attachment,
                uploaded_by_user=current_user,
            )
        else:
            ProjectUploadedFiles.objects.create(
                project=project,
                work_stage=work_stage,
                caption=issue.title,
                file=attachment,
                uploaded_by_user=current_user,
            )

    # User work progress
    work_stages = (
        WorkStageModel.objects
        .filter(
            Q(issue=issue) &
            (
                Q(created_by_team=current_user) |
                Q(created_by_contractor__isnull=False)
            )
        )
        .select_related(
            "created_by_team",
            "created_by_contractor"
        )
        .prefetch_related("work_stage_attachments")
        .order_by("-created_at")
    )

    if issue.type == 'issue':
        return render(
            request,
            "partials/work_progress.html",
            {   
                "current_user" : current_user,
                "issue": issue,
                "work_stages": work_stages,
            },
        )
    else:
        return render(
            request,
            "partials/task_work_progress.html",
            {   
                "current_user" : current_user,
                "issue": issue,
                "work_stages": work_stages,
            },
        )



# ============= UPDATE ISSUE ACTIVITY =============
def update_issue_activity(request, issue_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    issue = IssueModel.objects.filter(uuid=issue_uuid).first()
    project = issue.project

    work_stage = WorkStageModel.objects.create(
        issue=issue,
        status=request.POST.get("status"),
        update=request.POST.get("update"),
        created_by_team=current_user,
    )

    # =============== FILES ===============
    attachments = request.FILES.getlist("attachments")
    for attachment in attachments:
        if attachment.content_type.startswith("image/"):
            ProjectUploadedFiles.objects.create(
                project=project,
                work_stage=work_stage,
                caption=issue.title,
                photo=attachment,
                uploaded_by_user=current_user,
            )
        else:
            ProjectUploadedFiles.objects.create(
                project=project,
                work_stage=work_stage,
                caption=issue.title,
                file=attachment,
                uploaded_by_user=current_user,
            )

    # User work progress
    work_stages = (
        WorkStageModel.objects
        .filter(
            Q(issue=issue) &
            (
                Q(created_by_team=current_user) |
                Q(created_by_contractor__isnull=False)
            )
        )
        .select_related(
            "created_by_team",
            "created_by_contractor"
        )
        .prefetch_related("work_stage_attachments")
        .order_by("-created_at")
    )

    return render(
        request,
        "issues_templates/issue_activity_partial.html",
        {   
            "current_user" : current_user,
            "issue": issue,
            "work_stages": work_stages,
        },
    )


# ============= UPDATE TASK ACTIVITY =============
def update_task_activity(request, issue_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    issue = IssueModel.objects.filter(uuid=issue_uuid).first()
    project = issue.project

    work_stage = WorkStageModel.objects.create(
        issue=issue,
        status=request.POST.get("status"),
        update=request.POST.get("update"),
        created_by_team=current_user,
    )

    # =============== FILES ===============
    attachments = request.FILES.getlist("attachments")
    for attachment in attachments:
        if attachment.content_type.startswith("image/"):
            ProjectUploadedFiles.objects.create(
                project=project,
                work_stage=work_stage,
                caption=issue.title,
                photo=attachment,
                uploaded_by_user=current_user,
            )
        else:
            ProjectUploadedFiles.objects.create(
                project=project,
                work_stage=work_stage,
                caption=issue.title,
                file=attachment,
                uploaded_by_user=current_user,
            )

    # User work progress
    work_stages = (
        WorkStageModel.objects
        .filter(
            Q(issue=issue) &
            (
                Q(created_by_team=current_user) |
                Q(created_by_contractor__isnull=False)
            )
        )
        .select_related(
            "created_by_team",
            "created_by_contractor"
        )
        .prefetch_related("work_stage_attachments")
        .order_by("-created_at")
    )

    return render(
        request,
        "issues_templates/task_activity_partial..html",
        {   
            "current_user" : current_user,
            "issue": issue,
            "work_stages": work_stages,
        },
    )


# ============= Project Issues Partial =============
def filter_project_issues_view(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now().date()

    project_issues = get_all_project_issues_data(project=project,current_user=current_user)
    issues = project_issues['issues_list']

    # SEARCH FILTER
    query = request.POST.get("query", "").strip()
    if query:
        issues = [
            item for item in issues
            if query.lower() in item['issue'].title.lower()
        ]


    # STATUS FILTER
    status = request.POST.get("status", "").strip()
    if status:
        issues = [
            item for item in issues
            if item['issue'].status == status
        ]


    # STATUS FILTER
    priority = request.POST.get("priority", "").strip()
    if priority:
        issues = [
            item for item in issues
            if item['status'] == priority
        ]

    # ASSIGNEE
    assignee = request.POST.get("assignee", "").strip()
    if assignee:
        if assignee == "unassigned":
            issues = [
                item for item in issues
                if item["issue"].assigned_to == None
            ]
        elif assignee == "me":
            issues = [
                item for item in issues
                if item["issue"].assigned_to == current_user
            ]

    # CREATED DATE
    created_date = request.POST.get("created_date", "").strip()
    if created_date:
        if created_date == "today":

            today_date = timezone.localdate()

            issues = [
                item for item in issues
                if item["issue"].created_at.date() == today_date
            ]
        elif created_date == "week":
            today_date = timezone.localdate()
            start_of_week = today_date - timedelta(days=today_date.weekday())

            issues = [
                item for item in issues
                if start_of_week <= item["issue"].created_at.date() <= today_date
            ]


    # SPECIFIC DATE
    specific_date = request.POST.get("specific_date", "").strip()

    if specific_date:
        selected_date = date.fromisoformat(specific_date)

        issues = [
            item for item in issues
            if item["issue"].created_at.date() == selected_date
        ]

    # UNREAD COMMENTS
    comments = request.POST.get("comments", "").strip()
    if comments:
        issues = [
            item for item in issues
            if item['comment_count'] != 0
        ]



    return render(
        request,
        "partials/all_issues_partial.html",
        {
            "project": project,
            "current_user": current_user,
            "today": today,
            "issues" : issues,
        },
    )



# ============= Project Tasks Partial =============
def filter_project_tasks_view(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now().date()

    project_tasks = get_all_project_tasks_data(project=project,current_user=current_user)
    tasks = project_tasks['tasks_list']

    # SEARCH FILTER
    query = request.POST.get("query", "").strip()
    if query:
        tasks = [
            item for item in tasks
            if query.lower() in item['task'].title.lower()
        ]


    # STATUS FILTER
    status = request.POST.get("status", "").strip()
    if status:
        tasks = [
            item for item in tasks
            if item['task'].status == status
        ]


    # STATUS FILTER
    priority = request.POST.get("priority", "").strip()
    if priority:
        tasks = [
            item for item in tasks
            if item['status'] == priority
        ]

    # ASSIGNEE
    assignee = request.POST.get("assignee", "").strip()
    if assignee:
        if assignee == "unassigned":
            tasks = [
                item for item in tasks
                if item["task"].assigned_to == None
            ]
        elif assignee == "me":
            tasks = [
                item for item in tasks
                if item["task"].assigned_to == current_user
            ]

    # CREATED DATE
    created_date = request.POST.get("created_date", "").strip()
    if created_date:
        if created_date == "today":

            today_date = timezone.localdate()

            tasks = [
                item for item in tasks
                if item["task"].created_at.date() == today_date
            ]
        elif created_date == "week":
            today_date = timezone.localdate()
            start_of_week = today_date - timedelta(days=today_date.weekday())

            tasks = [
                item for item in tasks
                if start_of_week <= item["task"].created_at.date() <= today_date
            ]


    # SPECIFIC DATE
    specific_date = request.POST.get("specific_date", "").strip()

    if specific_date:
        selected_date = date.fromisoformat(specific_date)

        tasks = [
            item for item in tasks
            if item["task"].created_at.date() == selected_date
        ]

    # UNREAD COMMENTS
    comments = request.POST.get("comments", "").strip()
    if comments:
        tasks = [
            item for item in tasks
            if item['comment_count'] != 0
        ]



    return render(
        request,
        "partials/all_tasks_partial.html",
        {
            "project": project,
            "current_user": current_user,
            "today": today,
            "tasks" : tasks,
        },
    )