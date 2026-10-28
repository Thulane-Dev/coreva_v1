from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q

# Models Import
from .models import *
from account.models import *
from authentication.models import *
from projects.models import *
from issues.models import *


from .services.contractors_views import (
    get_workspace_data,
    get_workspace_project_data,
)


# ============= Company Contractors =============
def CompanyContractorsView(request):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company

    context = {
        "company": company,
        "page": "contractors/company_contractors.html",
    }

    if request.htmx:
        return render(request, "contractors/company_contractors.html", context)
    return render(request, "client/base.html", context)



# ============= Project Contractors =============
def ProjectContractors(request,project_uuid):
    project = get_object_or_404(ProjectModel, uuid=project_uuid)

    contractors = (
        ProjectContractor.objects
        .filter(project=project)
        .select_related(
            "contractor",
            "contractor__address",
            "added_by",
        )
        .order_by("-created_at")
    )

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        contractors = contractors.filter(
            Q(contractor__company_name__icontains=search) |
            Q(contractor__industry__icontains=search) |
            Q(contractor__email__icontains=search) |
            Q(contractor__phone__icontains=search)
        )

    if status:
        contractors = contractors.filter(status=status)

    context = {
        "project" : project,
        "contractors": contractors,
        "search": search,
        "selected_status": status,

        "contractor_count": contractors.count(),
        "active_count": contractors.filter(status="active").count(),
        "pending_count": contractors.filter(status="pending").count(),
        "inactive_count": contractors.filter(status="inactive").count(),
        "page": "contractors/project_contractors.html",
    }

    if request.htmx:
        return render(request, "contractors/project_contractors.html", context)
    return render(request, "client/base.html", context)


# ============= Contractor Details Page =============
def ContractorDetailsPage(request, contractor_uuid):
    contractor = get_object_or_404(
        ProjectContractor.objects
        .select_related(
            "project",
            "contractor",
            "contractor__address",
            "added_by",
        ),
        uuid=contractor_uuid,
    )

    assigned_items = (
        IssueModel.objects
        .filter(assigned_contractor=contractor)
        .select_related(
            "project",
            "assigned_to",
            "created_by",
        )
        .order_by("-created_at")
    )

    assigned_issues = assigned_items.filter(type="issue")

    assigned_tasks = assigned_items.filter(type="task")

    open_issues = assigned_issues.filter(status="open")
    closed_issues = assigned_issues.filter(status="closed")

    open_tasks = assigned_tasks.filter(status="open")
    closed_tasks = assigned_tasks.filter(status="closed")

    back_url = request.GET.get("back_url") or reverse(
        "contractors:project-contractors",
        args=[contractor.project.uuid],
    )

    context = {
        "contractor": contractor,

        "assigned_issues": assigned_issues,
        "assigned_tasks": assigned_tasks,

        "total_items": assigned_items.count(),

        "issue_count": assigned_issues.count(),
        "task_count": assigned_tasks.count(),

        "open_issues_count": open_issues.count(),
        "closed_issues_count": closed_issues.count(),

        "open_tasks_count": open_tasks.count(),
        "closed_tasks_count": closed_tasks.count(),
        "back_url" : back_url,
        "page": "contractors/contractor_details.html",
    }

    if request.htmx:
        return render(request, "contractors/contractor_details.html", context)
    return render(request, "client/base.html", context)


# ============= Add Contractor View =============
def AddContractorView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    # contractors = SubcontractorRelation.objects.filter(main_contractor=company)

    contractors = SubcontractorRelation.objects.filter(
            main_contractor=company
        ).exclude(
            subcontractor__contractor_projects__project=project
        )

    project_contractors = ProjectContractor.objects.filter(project=project)

    context = {
        "project": project,
        "contractors" : contractors,
        "project_contractors" : project_contractors,
        "page": "contractors/add_contractor.html",
    }

    if request.htmx:
        return render(request, "contractors/add_contractor.html", context)
    return render(request, "client/base.html", context)


# ============= Save Select Existing Contractor =============
@require_POST
def save_select_existing_contractor(request, project_uuid):
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    contractor_uuid=request.POST.get("contractor_uuid")
    contractor = get_object_or_404(CompanyProfileModel, uuid=contractor_uuid)
   
    messages.success(
        request,
        f"✅ {contractor.company_name} successfully added."
    )

    # 🎯 Redirect To Projects
    url = reverse('projects:project-view', args=[project.uuid, ])
    return redirect(f"{url}#Contractors")



# ============= Save New Contractor =============
@require_POST
def save_new_contractor(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)


    # Create Company Profile Model Object
    save_contractor = CompanyProfileModel.objects.create(
        company_name=request.POST.get("company_name"),
        email=request.POST.get("email"),
        phone=request.POST.get("phone"),
        contact_name=request.POST.get("contact_name"),
        industry=request.POST.get("trade"),
    )

    # Create relationship
    SubcontractorRelation.objects.create(
        main_contractor=company,
        subcontractor=save_contractor,
        created_by=current_user,
    )

    # Add To Project
    ProjectContractor.objects.create(
        project=project,
        contractor=save_contractor,
        added_by=current_user,
    )

    messages.success(
        request,
        f"✅ {save_contractor.company_name} successfully added."
    )

    # 🎯 Redirect To Projects
    url = reverse('projects:project-view', args=[project.uuid, ])
    return redirect(f"{url}#Contractors")


# ============= Search Coreva Contractor Function =============
def search_coreva_contractor(request, project_uuid):
    project = get_object_or_404(ProjectModel, uuid=project_uuid)

    contractor_uuid = request.POST.get("contractor_uuid", "").strip()
    
    found_company = None
    company_not_found = False
    invalid_uuid = False
    

    # Validate UUID before querying the database
    try:
        contractor_uuid = uuid.UUID(contractor_uuid)

    except (ValueError, AttributeError, TypeError):
        invalid_uuid = True

    else:
        found_company = CompanyProfileModel.objects.filter(
            uuid=contractor_uuid
        ).first()

        if found_company:
            company_not_found = True


    return render(
            request,
            "partials/add_contractor_search_result_partial.html",
            {
                "project": project,
                "found_company": found_company,
                "company_not_found": company_not_found,
                "invalid_uuid": invalid_uuid,
            },
        )


# ============= Save New Contractor =============
@require_POST
def add_found_contractor_function(request, project_uuid,contractor_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)

    contractor = get_object_or_404(CompanyProfileModel, uuid=contractor_uuid)

    # Create relationship
    SubcontractorRelation.objects.create(
        main_contractor=company,
        subcontractor=contractor,
        created_by=current_user,
    )

    # Add To Project
    ProjectContractor.objects.create(
        project=project,
        contractor=contractor,
        added_by=current_user,
    )

    messages.success(
        request,
        f"✅ {contractor.company_name} successfully added."
    )

    # 🎯 Redirect To Projects
    url = reverse('projects:project-view', args=[project.uuid, ])
    return redirect(f"{url}#Contractors")



# ============= EDIT CONTRACTOR DETAILS =============
def EditContractorDetailsView(request, contractor_uuid):
    project_contractor = get_object_or_404(ProjectContractor,uuid=contractor_uuid)
    contractor = project_contractor.contractor
    project = project_contractor.project
    linked_contractor = CompanyProfileModel.objects.filter(
            connected_companies__connected_contractors=contractor
        ).first()


    context = {
        "project": project,
        "contractor" : contractor,
        "project_contractor" : project_contractor,
        "linked_contractor" : linked_contractor,
        "page": "contractors/edit_contractor.html",
    }

    if request.htmx:
        return render(request, "contractors/edit_contractor.html", context)
    return render(request, "client/base.html", context)


# ============= Link Contractor Account =============
def LinkContractorAccountView(request, contractor_uuid):
    project_contractor = get_object_or_404(ProjectContractor,uuid=contractor_uuid)
    contractor = project_contractor.contractor
    project = project_contractor.project



    context = {
        "project": project,
        "contractor" : contractor,
        "project_contractor" : project_contractor,
        "page": "contractors/link_contractor_account.html",
    }

    if request.htmx:
        return render(request, "contractors/link_contractor_account.html", context)
    return render(request, "client/base.html", context)


# ============= Search Function =============
def Search_contractor_profile(request, project_contractor_uuid):

    project_contractor = get_object_or_404(
        ProjectContractor,
        uuid=project_contractor_uuid
    )

    contractor_uuid = request.POST.get("contractor_uuid", "").strip()

    found_company = None
    company_not_found = False
    invalid_uuid = False
    

    # Validate UUID before querying the database
    try:
        contractor_uuid = uuid.UUID(contractor_uuid)

    except (ValueError, AttributeError, TypeError):
        invalid_uuid = True

    else:
        found_company = CompanyProfileModel.objects.filter(
            uuid=contractor_uuid
        ).first()

        if found_company:
            company_not_found = True

    return render(
        request,
        "partials/link_contractor_search_partial.html",
        {
            "project_contractor": project_contractor,
            "found_company": found_company,
            "company_not_found": company_not_found,
            "invalid_uuid": invalid_uuid,
        },
    )


# ============= Connect Found Contractor =============
def Connect_found_contractor(request, project_contractor_uuid,contractor_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company

    
    found_company = CompanyProfileModel.objects.filter(uuid=contractor_uuid).first()
    project_contractor = get_object_or_404(
            ProjectContractor,
            uuid=project_contractor_uuid
        )


    # Update Sub Contraction Relation 
    subContractorRelation = get_object_or_404(SubcontractorRelation,subcontractor = project_contractor.contractor)
    subContractorRelation.subcontractor=found_company 
    subContractorRelation.save()


    # Update All Contractor Projects
    contractor_projects = ProjectContractor.objects.filter(uuid=project_contractor_uuid)
    for project in contractor_projects:
        project.contractor = found_company
        project.save()


    return render(
            request,
            "partials/link_contractor_search_partial.html",
            {   
                "connected_company": found_company,
                "project_contractor_uuid" : project_contractor_uuid,
            },
        )


# ============= SAVE CONTRACTOR UPDATES =============
@require_POST
def save_contractor_updates(request,project_contractor_uuid):
    project_contractor = get_object_or_404(
            ProjectContractor,
            uuid=project_contractor_uuid
        )

    contractor = project_contractor.contractor

    # 🎯 Redirect To Contractor Profile
    url = reverse('contractors:contractor', args=[project_contractor.uuid, ])
    return redirect(url)

# ============= Contractor Portal =============
def ContractorPortalView(request,contractor_uuid):
    contractor = get_object_or_404(CompanyProfileModel,uuid=contractor_uuid)
    contractor_data = get_workspace_data(contractor=contractor)
    projects = contractor_data['projects_list']


    context = {
        "contractor_data": contractor_data,
        "projects" : projects,
        "contractor" : contractor,
    }
    return render(request, 'contractor_portal/contractor_workspace.html', context)


# ============= Contractor Project Details Page =============
def ContractorPortalProjectView(request,project_uuid, portal_uuid):
    project_contractor = get_object_or_404(ProjectContractor,uuid=portal_uuid)
    contractor = project_contractor.contractor
    project_data = get_workspace_project_data(project=project_contractor.project,   contractor=project_contractor,  show_project_details=True)
    open_issues = project_data['open_issues']
    project = project_contractor.project 

    context = {
        "project" : project,
        "portal_uuid" : portal_uuid,
        "project_data" : project_data,
    }

    return render(request, 'contractor_portal/workspace_project_details.html',context)



# ============= View Work Details Page =============
def ViewWorkDetailsPage(request,issue_uuid, portal_uuid):
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

    contractor = issue.assigned_contractor.contractor

    attachments = ProjectUploadedFiles.objects.filter(issue_task=issue).order_by('-created_at')

    comments = (
        IssueCommentModel.objects
        .filter(issue=issue)
        .select_related("comment_by")
        .prefetch_related("comment_attachments")
        .order_by("-created_at")
    )

    work_stages = (
        WorkStageModel.objects
        .filter(Q(issue=issue) & Q(created_by_contractor=contractor))
        .select_related("created_by_contractor")
        .prefetch_related("work_stage_attachments")
        .order_by("-created_at")
    )

    context = {
        "issue": issue,
        "comments": comments,
        "attachments" : attachments,
        "contractor" : contractor,
        "work_stages" : work_stages,
    }

    return render(request, 'contractor_portal/view_work_details.html',context)


# ============= Save Issue Comment =============
def save_contractor_comment(request, issue_uuid,contractor_uuid):
    contractor = get_object_or_404(CompanyProfileModel,uuid=contractor_uuid)
    issue = IssueModel.objects.filter(uuid=issue_uuid).first()
    project = issue.project

    comment = IssueCommentModel.objects.create(
        issue=issue,
        comment=request.POST.get("comment"),
        contractor_comment=contractor,
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
                uploaded_by_contractor=contractor,
            )
        else:
            ProjectUploadedFiles.objects.create(
                project=project,
                comment=comment,
                caption=issue.title,
                file=attachment,
                uploaded_by_contractor=contractor,
            )

    # Comments for this issue
    comments = (
        IssueCommentModel.objects
        .filter(issue=issue)
        .select_related("comment_by")
        .prefetch_related("comment_attachments")
        .order_by("-created_at")
    )


    return render(
        request,
        "partials/contractor_comments_partial.html",
        {
            "issue": issue,
            "comments": comments,
            "contractor" : contractor,
        },
    )




# ============= Mark Comment as read =============
def mark_contractor_issue_read(request, issue_uuid,contractor_uuid):
    issue = IssueModel.objects.filter(uuid=issue_uuid).first()
    contractor = get_object_or_404(CompanyProfileModel,uuid=contractor_uuid) 
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

    return render(
        request,
        "partials/contractor_comments_partial.html",
        {
            "issue": issue,
            "comments": comments,
            "contractor" : contractor,
        },
    )



# ============= SAVE CONTRACTOR WORK STAGE =============
def save_contractor_work_stage(request, issue_uuid,contractor_uuid):
    contractor = get_object_or_404(CompanyProfileModel,uuid=contractor_uuid)
    issue = IssueModel.objects.filter(uuid=issue_uuid).first()
    project = issue.project

    work_stage = WorkStageModel.objects.create(
        issue=issue,
        status=request.POST.get("work_status"),
        update=request.POST.get("comment"),
        created_by_contractor=contractor,
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
                uploaded_by_contractor=contractor,
            )
        else:
            ProjectUploadedFiles.objects.create(
                project=project,
                work_stage=work_stage,
                caption=issue.title,
                file=attachment,
                uploaded_by_contractor=contractor,
            )

    # Comments for this issue
    work_stages = (
        WorkStageModel.objects
        .filter(Q(issue=issue) & Q(created_by_contractor=contractor))
        .select_related("created_by_contractor")
        .prefetch_related("work_stage_attachments")
        .order_by("-created_at")
    )


    return render(
        request,
        "partials/contractor_work_progress_partial.html",
        {   
            "contractor" : contractor,
            "issue": issue,
            "work_stages": work_stages,
        },
    )



