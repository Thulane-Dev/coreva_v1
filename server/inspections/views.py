from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q,Prefetch
from django.utils import timezone
from django.http import HttpResponse
import json
from datetime import datetime

from django.db.models import Case, When, Value, IntegerField



# Models Import
from .models import *
from authentication.models import UserModel
from issues.models import *
from projects.models import *

# Services Import
from .services.inspections_view import (
    get_project_daily_inspection_new,
    get_missed_inspection_days
)

# ============= Todays Dashboard New PLACEHOLDER =============
def DailyInspectionView(request):

    context = {
        "page": "inspections/inspections.html",
        }

    if request.htmx:
        return render(request, "inspections/inspections.html", context)
    return render(request, "client/base.html", context)


# ============= PROJECT DAILY INSPECTIONS =============
def ProjectDailyInspectionsView(request, project_uuid, inspection_uuid=None):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    inspection = InspectionModel.objects.filter(uuid=inspection_uuid).first()

    if inspection:
        inspection_data_new = get_project_daily_inspection_new(
                project=project, current_user=current_user,inspection=inspection)
        inspection = inspection_data_new['inspection']
    else:
        inspection_data_new = get_project_daily_inspection_new(
            project=project, current_user=current_user)
        inspection  = inspection_data_new['inspection']

        
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')
    today = timezone.now()

    context = {
        "inspection": inspection,
        "inspection_data_new": inspection_data_new,
        "team_members": team_members,
        "today": today,
        "current_user" : current_user,
        "project" : project,
        "inspection_uuid": inspection_uuid,
        "page": "inspections/project_daily_inspections.html",
    }

    if request.htmx:
        return render(request, "inspections/project_daily_inspections.html", context)
    return render(request, "client/base.html", context)

# ============= Admin Sign-Off =============
@require_POST
def admin_sign_off(request, project_uuid, inspection_uuid=None):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    inspection = InspectionModel.objects.filter(uuid=inspection_uuid).first()
    if inspection:
        inspection_data_new = get_project_daily_inspection_new(
                project=project, current_user=current_user,inspection=inspection)
        update_inspection = inspection
    else:
        inspection_data_new = get_project_daily_inspection_new(
            project=project, current_user=current_user)
        update_inspection = inspection_data_new['inspection']
    
    today = timezone.now()

    # Update Inspection
    update_inspection.admin_sign_off = current_user
    update_inspection.signed_off_at = today
    update_inspection.save()

    messages.success(
        request,
        f"✅ Inspection successfully updated."
    )

    # 🎯 Redirect To Projects Inspections
    url = reverse('inspections:project-inspections', args=[project.uuid, ])
    return redirect(f"{url}#inspection-list-{update_inspection.id}")


# INSPECTION RESPONSE UPDATE
def update_inspection_response(request, response_id):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')
    today = timezone.now()

    response = get_object_or_404(
        InspectionResponseModel.objects.select_related(
            "question",
            "question__category",
            "inspection",
        ).prefetch_related(
            "inspection_response",
        ),
        id=response_id,
    )

    answer = request.POST.get("answer")

    response.answer = answer
    response.save()

    category = response.question.category
    inspection = response.inspection

    # Get all responses for this category
    category_responses = InspectionResponseModel.objects.filter(
        question__category=category,
        inspection=inspection,
    ).prefetch_related(
        "inspection_response",
    )

    total_questions = category_responses.count()

    total_answered = category_responses.filter(
        answer__isnull=False
    ).exclude(
        answer=""
    ).count()

    failed_items = category_responses.filter(answer="fail").count()

    # =============== CREATE PROJECT TIMELINE  ===============
    if answer == 'fail':
        ActivityModel.objects.create(
            company=company,
            project=response.inspection.project,
            user=current_user,
            activity_type='Inspection Failed',
            description=f'{current_user.first_name} {current_user.last_name} flagged inspection item - {response.question.question} - failed',
            icon_type='inspection',
        )

    return render(
        request,
        "partials/inspection_response_update.html",
        {
            "response": response,
            "total_questions": total_questions,
            "total_answered": total_answered,
            "team_members": team_members,
            "today": today,
            "failed_items": failed_items,
        },
    )

# ============= Create Inspection Issue =============
def create_new_issue(request, response_id):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')

    response = get_object_or_404(
        InspectionResponseModel.objects.select_related(
            "question",
            "question__category",
            "inspection",
        ).prefetch_related(
            "inspection_response",
        ),
        id=response_id,
    )

    # Add Issue ==============
    assigned_to_id = request.POST.get("assigned_to_id")
    if assigned_to_id != 'None':
        assigned_to = UserModel.objects.filter(id=assigned_to_id).first()
    else:
        assigned_to = None

    issue, created = IssueModel.objects.update_or_create(
        # Lookup fields - used to find existing record
        inspection=response.inspection,
        inspection_response=response,

        # Default fields - used when creating or updating
        defaults={
            'type': 'issue',
            'project': response.inspection.project,
            'title': response.question.question,
            'description': request.POST.get("description"),
            'priority': request.POST.get("priority"),
            'due_date': request.POST.get("due_date"),
            'assigned_to': assigned_to,
        }
    )

    response = get_object_or_404(
        InspectionResponseModel.objects.select_related(
            "question",
            "question__category",
            "inspection",
        ).prefetch_related(
            "inspection_response",
        ),
        id=response_id,
    )

    category = response.question.category
    inspection = response.inspection

    # Get all responses for this category
    category_responses = InspectionResponseModel.objects.filter(
        question__category=category,
        inspection=inspection,
    ).prefetch_related(
        "inspection_response",
    )

    total_questions = category_responses.count()

    total_answered = category_responses.filter(
        answer__isnull=False
    ).exclude(
        answer=""
    ).count()

    failed_items = category_responses.filter(answer="fail").count()

    # =============== CREATE PROJECT TIMELINE  ===============
    ActivityModel.objects.create(
        company=company,
        project=issue.inspection.project,
        user=current_user,
        activity_type='Issue Created',
        description=f'{current_user.first_name} {current_user.last_name} created an inspection issue - {issue.title}',
        icon_type='issue',
    )

    if assigned_to:
        ActivityModel.objects.create(
            company=company,
            project=issue.inspection.project,
            user=current_user,
            activity_type='Issue Assigned',
            description=f'{current_user.first_name} {current_user.last_name} assigned inspection issue - {issue.title} - to {assigned_to.first_name} {assigned_to.last_name}',
            icon_type='issue',
        )

    return render(
        request,
        "partials/inspection_response_update.html",
        {
            "response": response,
            "total_questions": total_questions,
            "total_answered": total_answered,
            "team_members": team_members,
            "failed_items": failed_items,
        },
    )

# ============= Save Inspection =============
@require_POST
def save_inspection(request, inspection_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    inspection = get_object_or_404(InspectionModel, uuid=inspection_uuid)
    project = inspection.project

    inspection_data = get_project_daily_inspection_new(
                    project=project, current_user=current_user,inspection=inspection)
    inspection_status = inspection_data['inspection_status']

    if request.method == 'POST' and 'save_draft' in request.POST:
        status = 'draft'
        messages.success(
            request,
            f"✅ Inspection successfully saved as draft."
        )

    if request.method == 'POST' and 'save_inspection' in request.POST:
        status = 'completed'
        messages.success(
            request,
            f"✅ Inspection successfully complete."
        )

    if inspection_status == 'Incomplete':
        status = 'in_progress'

    # Update Inspection
    inspection.completed_at = timezone.now()
    inspection.completed_by = current_user
    inspection.status = status
    inspection.save()

    

    # 🎯 Redirect To Projects
    url = reverse('inspections:checklist', args=[project.uuid, inspection_uuid])
    return redirect(f"{url}")

# ============= Missed Daily Inspections =============
def MissedDailyInspections(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    missed_inspection_days = get_missed_inspection_days(project=project)

    context = {
        "missed_inspection_days": missed_inspection_days,
        "project": project,
        "page": "inspections/missed_inspections.html",
    }

    if request.htmx:
        return render(request, "inspections/missed_inspections.html", context)
    return render(request, "client/base.html", context)


# ============= Create Missed Daily Inspection =============
@require_POST
def create_missed_inspection(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)

    missed_date = request.POST.get("missed_date")

    if missed_date:
        missed_date = datetime.strptime(missed_date,"%Y-%m-%d").date()

    inspection_data_new = get_project_daily_inspection_new(
        project=project, current_user=current_user,missed_date=missed_date)
    inspection = inspection_data_new['inspection']
       
    # 🎯 Redirect To Projects Inspections
    url = reverse('inspections:checklist', args=[project.uuid, inspection.uuid ])
    return redirect(f"{url}")

# ============= All Project Inspections =============
def ProjectInspectionsPageView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now()
    todays_card_highlight = timezone.localdate()
    next_url = request.GET.get("next")
    
    # inspections = (
    #         InspectionModel.objects
    #         .filter(project=project)
    #         .annotate(
    #             is_today=Case(
    #                 When(inspection_date=today, then=Value(0)),
    #                 default=Value(1),
    #                 output_field=IntegerField(),
    #             )
    #         )
    #         .order_by("is_today", "-created_at")
    #     )

    today_inspection = (
    InspectionModel.objects
        .filter(
            project=project,
            inspection_date=today
        )
        .first()
    )


    inspections = list(
        InspectionModel.objects
        .filter(project=project)
        .exclude(inspection_date=today)
        .order_by("-created_at")
    )


    if today_inspection:
        # Today's inspection exists.
        # Put the real inspection at the top.
        inspections.insert(0, today_inspection)

    else:
        # Today's inspection does not exist.
        # Show the virtual "Not started" card.
        inspections.insert(0, {
            "is_not_started": True,
            "inspection_date": today,
            "reference": "Today's Inspection",
        })
    context = {
        "inspections": inspections,
        "project": project,
        "today": today,
        "todays_card_highlight": todays_card_highlight,
        "next_url": next_url,
        "page": "inspections/project_inspections.html",
    }

    if request.htmx:
        return render(request, "inspections/project_inspections.html", context)
    return render(request, "client/base.html", context)


# ============= GET PROJECT INSPECTIONS  =============
def get_inspection_categories(project):

    return InspectionCategoryModel.objects.filter(

        (
            Q(is_default=True) &
            Q(project__isnull=True)
        )

        |

        (
            Q(is_default=False) &
            Q(project=project)
        )

    ).exclude(

        not_applicable=project

    ).prefetch_related(

        Prefetch(
            "category",

            queryset=InspectionQuestionModel.objects.filter(

                (
                    Q(is_default=True) &
                    Q(project_question__isnull=True)
                )

                |

                (
                    Q(is_default=False) &
                    Q(project_question=project)
                )

            ).exclude(

                not_applicable=project

            ).order_by("order"),

            to_attr="inspection_questions"
        )

    ).order_by("order")


# ============= EDIT INSPECTIONS ITEMS VIEW=============
def ProjectInspectionItems(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    inspection_categories = get_inspection_categories(project)

    context = {
        "project": project,
        "inspection_categories" : inspection_categories,
        "page": "edit_inspections/inspection_items.html",
    }

    if request.htmx:
        return render(request, "edit_inspections/inspection_items.html", context)
    return render(request, "client/base.html", context)



# ============= ADD CATEGORY =============
def save_new_category_view(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)

    categories = InspectionCategoryModel.objects.filter(
                (
                    Q(is_default=True) &
                    Q(project__isnull=True)
                )

                |

                (
                    Q(is_default=False) &
                    Q(project=project)
                )

            ).exclude(

                not_applicable=project

            ).order_by("-order").first()

    next_order = (
        categories.order + 1
        if categories
        else 1
    )


    # -----------------------------------------------
    # SAVE CATEGORY
    # -----------------------------------------------
    category = request.POST.get("category", "").strip()
    if category:
        InspectionCategoryModel.objects.create(
            name=category,
            is_default=False,
            project=project,
            order=next_order,
        )


    inspection_categories = get_inspection_categories(project)

    response = render(
        request,
        "edit_inspections/inspections_categories_partial.html",
        {
            "current_user": current_user,
            "inspection_categories": inspection_categories,
            "project": project,
        },
    )

    response["HX-Trigger"] = json.dumps({
        "corevaToast": {
            "title": "Category added",
            "message": "The checklist category was added successfully."
        }
    })

    return response



# ============= REMOVE CATEGORY =============
def remove_category_view(request, project_uuid, category_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)

    category = get_object_or_404(InspectionCategoryModel,uuid=category_uuid)
    questions = InspectionQuestionModel.objects.filter(
        Q(category=category)
        ).filter(
            (
                Q(is_default=True) &
                Q(project_question__isnull=True)
            )
            |
            (
                Q(is_default=False) &
                Q(project_question=project)
            )
        ).exclude(
            not_applicable=project
        ).order_by("order")

    # -----------------------------------------------
    # UPDATE QUESTION OBJECT
    # -----------------------------------------------
    for question in questions:
        if question.is_default == True:
            question.not_applicable.add(project)
        else:
            question.delete()


    # -----------------------------------------------
    # UPDATE CATEGORY
    # -----------------------------------------------
    if category.is_default == True:
        category.not_applicable.add(project)
    else:
        category.delete()


    inspection_categories = get_inspection_categories(project)

    response = render(
        request,
        "edit_inspections/inspections_categories_partial.html",
        {
            "current_user": current_user,
            "inspection_categories": inspection_categories,
            "project": project,
        },
    )

    response["HX-Trigger"] = json.dumps({
        "corevaToast": {
            "title": "Category removed",
            "message": "The inspection category was removed successfully."
        }
    })

    return response



# ============= ADD QUESTION =============
def save_question_view(request, category_uuid, project_uuid):
    user = request.user
    current_user = get_object_or_404(
        UserModel,
        user=user
    )
    today = timezone.now()

    project = get_object_or_404(
        ProjectModel,
        uuid=project_uuid
    )

    category_object = get_object_or_404(
        InspectionCategoryModel,
        uuid=category_uuid
    )

    # -----------------------------------------------
    # GET CURRENT QUESTIONS FOR THIS CATEGORY
    # -----------------------------------------------

    last_question = InspectionQuestionModel.objects.filter(
        category=category_object
    ).order_by("-order").first()

    next_order = (
        last_question.order + 1
        if last_question
        else 1
    )


    # -----------------------------------------------
    # SAVE QUESTION
    # -----------------------------------------------

    question = request.POST.get("question", "").strip()

    if question:
        save_question = InspectionQuestionModel.objects.create(
            category=category_object,
            question=question,
            is_default=False,
            project_question=project,
            order=next_order,
        )

    # Create if todays inspection exists for this project
    inspection = InspectionModel.objects.filter(
                Q(created_at__date=today) & Q(project=project) 
            ).first()
    
    if inspection:
        if inspection.status != 'completed':
            InspectionResponseModel.objects.create(
                inspection=inspection,
                question=save_question,
            )


    # -----------------------------------------------
    # GET UPDATED CATEGORY
    # -----------------------------------------------

    inspection_categories = get_inspection_categories(project)

    category = next(
        (
            item
            for item in inspection_categories
            if str(item.uuid) == str(category_uuid)
        ),
        None
    )


    return render(
        request,
        "edit_inspections/inspection_category_question_partial.html",
        {
            "current_user": current_user,
            "category": category,
            "project" : project,
        },
    )


# ============= ADD CATEGORY QUESTION =============
def remove_question_view(request, question_uuid, project_uuid):

    user = request.user

    current_user = get_object_or_404(
        UserModel,
        user=user
    )

    today = timezone.now()

    project = get_object_or_404(
        ProjectModel,
        uuid=project_uuid
    )

    question_object = get_object_or_404(InspectionQuestionModel,uuid=question_uuid)

    # Check if todays inspection exists for this project
    inspection = InspectionModel.objects.filter(
                Q(created_at__date=today) & Q(project=project) 
            ).first()
    
    if inspection:
        if inspection.status != 'completed':
            remove_question = InspectionResponseModel.objects.filter(
                inspection=inspection,
                question=question_object,
            ).first()
            if remove_question:
                remove_question.delete()

    # -----------------------------------------------
    # UPDATE QUESTION OBJECT
    # -----------------------------------------------
    if question_object.is_default == True:
        question_object.not_applicable.add(project)
    else:
        question_object.delete()

    # -----------------------------------------------
    # GET UPDATED CATEGORY
    # -----------------------------------------------
    category = question_object.category

    inspection_categories = get_inspection_categories(project)

    category = next(
        (
            item
            for item in inspection_categories
            if str(item.uuid) == str(category.uuid)
        ),
        None
    )

    return render(
        request,
        "edit_inspections/inspection_category_question_partial.html",
        {
            "current_user": current_user,
            "category": category,
            "project" : project,
        },
    )