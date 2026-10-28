from django.apps import apps
from django.db.models import Q
from datetime import date
from django.utils import timezone
from collections import defaultdict
from datetime import timedelta
from datetime import datetime, date

# Models Import
InspectionCategoryModel = apps.get_model(
    "inspections", "InspectionCategoryModel")
InspectionModel = apps.get_model(
    "inspections", "InspectionModel")
InspectionQuestionModel = apps.get_model(
    "inspections", "InspectionQuestionModel")
InspectionResponseModel = apps.get_model(
    "inspections", "InspectionResponseModel")
ActivityModel = apps.get_model(
    "projects", "ActivityModel")


# PROJECT MISSED INSPECTIONS FUNCTION
def get_missed_inspection_days(project):
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    current_date = max(
        project.start_date,
        project.created_at.date()
    )

    missed_days = []

    while current_date <= yesterday:

        # Only check configured project working days
        if current_date.weekday() in project.working_days:

            inspection_exists = InspectionModel.objects.filter(
                project=project,
                inspection_date=current_date,
            ).exists()

            if not inspection_exists:
                missed_days.append(current_date)

        current_date += timedelta(days=1)

    return missed_days


# GENERATE DAILY INSPECTION REFERENCE
def generate_inspection_reference(inspection_id, inspection_date):

    if isinstance(inspection_date, str):
        inspection_date = datetime.strptime(
            inspection_date,
            "%Y-%m-%d"
        ).date()

    return f"IN-{inspection_date.strftime('%Y%m%d')}-{inspection_id:04d}"


# ======================================================================================================================= 


# PROJECT DETAILS FUNCTION DATA ********* USE
def get_project_details_inspection_data(
        inspection,
):

    unanswered_count = 0
    answered_count = 0
    failed_count = 0
    total_passed_count = 0
    total_na_count = 0
    items_count = 0
    

    checklist = (
        InspectionResponseModel.objects
        .filter(
            inspection=inspection
        )
        .select_related(
            "question",
            "question__category",
        )
        .order_by(
            "question__category__order",
            "question__order",
        )
    )

    # Group responses by category
    grouped_checklist = defaultdict(list)

    

    for response in checklist:
        category = response.question.category
        grouped_checklist[category].append(response)

    # Convert into template-friendly structure
    grouped_checklist = [
        {
            "category": category,
            "name": category.name,
            "responses": responses,

            # Statistics
            "tot_question": len(responses),

            "an_questions": sum(
                1 for response in responses
                if response.answer is not None
            ),

            "failed_questions": sum(
                1
                for response in responses
                if response.answer == "fail"
            ),

            # Status
            "status": (
                "Pending"
                if sum(1 for response in responses if response.answer is not None) == 0
                else "Complete"
                if sum(1 for response in responses if response.answer is not None) == len(responses)
                else "Incomplete"
            ),
        }
        for category, responses in grouped_checklist.items()
    ]

    # CHECK COUNTS
    for item in checklist:
        items_count += 1
        if item.answer == None:
            unanswered_count += 1
        elif item.answer == 'fail':
            failed_count += 1
            answered_count += 1

        elif item.answer == 'pass':
            total_passed_count += 1
            answered_count += 1

        elif item.answer == 'na':
            total_na_count += 1
            answered_count += 1

    # DAILY INSPECTIONS INSIGHTS
    if unanswered_count > 0:
        inspection_icon = '🟡'
        inspection_insight = f'Daily inspection is incomplete'
        inspection_action = 'Continue inspection'
        inspection_btn = 'Continue inspection'
        inspection_status = 'Incomplete'
        failed_inspections = ''
    elif answered_count == items_count and inspection.status == "in_progress":
        inspection_icon = "🟠"
        inspection_insight = "Daily inspection is ready to save."
        inspection_action = "Save inspection"
        inspection_btn = 'Save inspection'
        inspection_status = 'Ready to Save'
        failed_inspections = ''
    elif inspection.status == "draft":
        inspection_icon = "🟠"
        inspection_insight = "Daily inspection is still in draft"
        inspection_action = "Continue inspection"
        inspection_btn = 'Continue inspection'
        inspection_status = 'Draft'
        failed_inspections = f'({failed_count} failed checks)'
    else:
        inspection_icon = "🟢"
        inspection_action = "View inspection"
        inspection_btn = 'View inspection'
        inspection_status = 'Complete'
        failed_inspections = f'({failed_count} failed checks)'
        if inspection.admin_sign_off:
            inspection_insight = "Daily inspection complete ✅"
        else:
            inspection_insight = "Inspection complete — awaiting admin sign-off."

    inspection_percentage = int(
        (answered_count / items_count) * 100)
    
    return {
        "grouped_checklist": grouped_checklist,
        "inspection_status": inspection_status,
        "inspection_btn": inspection_btn,
        "inspection_insight": inspection_insight,
        "inspection_icon": inspection_icon,
        "inspection_action": inspection_action,
        "failed_inspections": failed_inspections,
        "failed_inspections_count": failed_count,
        "total_passed_count": total_passed_count,
        "total_na_count": total_na_count,
        "unanswered_count": unanswered_count,
        "answered_count": answered_count,
        "total_checklists": items_count,
        "questions_count": 0,
        "inspection_percentage": inspection_percentage,
    }


# IF INSPECTION IS NOT CREATED OR IF CREATED GET INSPECTION DATA
def get_project_details_daily_inspection(
        project,
        current_user=None,
):
    today = timezone.now()
    inspection = InspectionModel.objects.filter(
        Q(created_at__date=today) & Q(project=project) & Q(is_missed_inspection=False)
    ).first()


    # ==================================================
    # NO DAILY INSPECTION CREATED DATA
    # ==================================================

    # Get All Project Questions
    inspection_questions = InspectionQuestionModel.objects.filter((
        Q(is_default=True) &
        Q(project_question__isnull=True)
    ) |
        (
        Q(is_default=False) &
        Q(project_question=project)
    )).exclude(not_applicable=project).order_by(
        "category__order",
        "order",
    )

    # inspection_questions = InspectionQuestionModel.objects.filter(Q(is_default=True) &
    #         Q(project_question__isnull=True)).exclude(not_applicable=project)

    # print(project)

    # inspection_questions = InspectionQuestionModel.objects.all()
    # inspection_questions = inspection_questions.exclude(not_applicable=project)


    # for item in inspection_questions:
    #     print(item)

    if inspection == None:
        inspection_status = 'Not Started'
        inspection_btn = 'Start Inspection'
        inspection_icon = '🔴'
        inspection_insight = 'Daily inspection not started'
        inspection_action = 'Start inspection'
        failed_inspections = ''
        questions_count = inspection_questions.count()
        checklist_items = None
        unanswered_count = 1
        inspection_percentage = 0
        answered_count = 0
        total_checklists = 0

    # ==================================================
    # GET CREATED INSPECTION DATA
    # ==================================================
    else:
        todays_inspection_data = get_project_details_inspection_data(
            inspection=inspection)
        inspection_icon = todays_inspection_data['inspection_icon']
        inspection_status = todays_inspection_data['inspection_status']
        inspection_btn = todays_inspection_data['inspection_btn']
        inspection_insight = todays_inspection_data['inspection_insight']
        failed_inspections = todays_inspection_data['failed_inspections']
        inspection_action = todays_inspection_data['inspection_action']
        questions_count = todays_inspection_data['questions_count']
        checklist_items = todays_inspection_data['grouped_checklist']
        unanswered_count = todays_inspection_data['unanswered_count']
        inspection_percentage = todays_inspection_data['inspection_percentage']
        answered_count = todays_inspection_data['answered_count']
        total_checklists = todays_inspection_data['total_checklists']

    # ==================================================
    # CHECK MISSED INSPECTIONS
    # ==================================================
    missed_inspection_days = get_missed_inspection_days(project)
    missed_inspection_count = len(missed_inspection_days)
    if missed_inspection_count > 0:
        missed_inspection_icon = '🔴'
        if missed_inspection_count > 1:
            missed_inspections_text = f'{missed_inspection_count} daily inspections were missed'
        else:
            missed_inspections_text = f'{missed_inspection_count} daily inspection missed'
    else:
        missed_inspection_icon = ''
        missed_inspections_text = ''

    return {
        # INSPECTIONS
        "inspection" : inspection,
        "missed_inspection_days": missed_inspection_days,
        "missed_inspections_text": missed_inspections_text,
        "missed_inspection_count": missed_inspection_count,
        "missed_inspection_icon": missed_inspection_icon,
        "inspection_status": inspection_status,
        "inspection_btn": inspection_btn,
        "inspection_icon": inspection_icon,
        "inspection_insight": inspection_insight,
        "failed_inspections": failed_inspections,
        "inspection_action": inspection_action,
        "questions_count": questions_count,
        "checklist_items": checklist_items,
        "unanswered_count": unanswered_count,
        "inspection_percentage": inspection_percentage,
        "answered_count": answered_count,
        "total_checklists": total_checklists,
    }


# 1st DAILY INSPECTION CHECKLIST ITEMS PAGE 
def get_project_daily_inspection_new_old(
    current_user=None,
    project=None,
    inspection=None,
    missed_date=None,
):  
    today = timezone.now()
    inspections_data = []
    total_answered_count = 0
    total_questions_count = 0
    total_unanswered_count = 0


    if missed_date:
        inspection = None 
    else:
        if inspection is None:
            inspection = InspectionModel.objects.filter(
                Q(created_at__date=today) & Q(project=project)
            ).first()
        else:
            inspection = inspection
          

    # ==================================================
    # CHECK IF INSPECTION CREATED IF NOT CREATE ONE
    # ==================================================
    if inspection == None:

        # Create Inspection For missed days
        if missed_date:
            inspection = InspectionModel.objects.create(
                project=project,
                status="in_progress",
                started_at=today,
                inspection_date = missed_date,
                started_by=current_user,
            )

            # inspection reference 
            # inspection_date = missed_date
            inspection_id = inspection.id
            reference = generate_inspection_reference(
                inspection_id, missed_date)
            inspection.reference = reference
            inspection.save()

        # Create Inspection for today 
        else:
            inspection = InspectionModel.objects.create(
                project=project,
                status="in_progress",
                inspection_date=today,
                started_at=today,
                started_by=current_user,
            )

            # inspection reference
            inspection_date = timezone.now().date()
            inspection_id = inspection.id
            reference = generate_inspection_reference(
                inspection_id, inspection_date)
            inspection.reference = reference
            inspection.save()
            

        # Get All Project Questions
        inspection_questions = InspectionQuestionModel.objects.filter((
            Q(is_default=True) &
            Q(project_question__isnull=True)
        ) |
            (
            Q(is_default=False) &
            Q(project_question=project)
        )).exclude(not_applicable=project).order_by(
            "category__order",
            "order",
        )

        # Create All Responses for All Questions
        InspectionResponseModel.objects.bulk_create([
            InspectionResponseModel(
                inspection=inspection,
                question=question,
            )
            for question in inspection_questions
        ])

        # =============== CREATE PROJECT TIMELINE ===============
        company = current_user.company
        ActivityModel.objects.create(
            company=company,
            project=project,
            user=current_user,
            activity_type='Inspection Started',
            description=f'{current_user.first_name} {current_user.last_name} started daily inspection',
            icon_type='inspection',
        )

    # ==================================================
    # GET INSPECTION CHECKLIST ITEMS
    # ==================================================
    inspection_questions = InspectionQuestionModel.objects.filter((
        Q(is_default=True) &
        Q(project_question__isnull=True)
    ) |
        (
        Q(is_default=False) &
        Q(project_question=project)
    )).exclude(not_applicable=project).order_by(
        "category__order",
        "order",
    )

    inspection_categories = InspectionCategoryModel.objects.filter(
        (
            Q(is_default=True) &
            Q(project__isnull=True)
        ) |
        (
            Q(is_default=False) &
            Q(project=project)
        )
    ).exclude(not_applicable=project)

    for category in inspection_categories:
        responses = InspectionResponseModel.objects.filter(
            question__category=category,
            inspection=inspection,
        ).prefetch_related(
            "inspection_response",
        )

        total_questions = responses.count()
        total_answered = responses.filter(
            answer__isnull=False
        ).exclude(
            answer=""
        ).count()

        total_unanswered = responses.filter(answer=None)
        total_unanswered_count += total_unanswered.count()

        failed_items = responses.filter(answer="fail").count()

        total_answered_count += total_answered
        total_questions_count += total_questions

        inspections_data.append({
            "category": category,
            "responses": responses,
            "total_questions": total_questions,
            "total_answered": total_answered,
            "failed_items": failed_items,
        })

    inspection_percentage = int(
        (total_answered_count / total_questions_count) * 100)

    # DAILY INSPECTIONS STATUS
    if total_unanswered_count > 0:
        inspection_icon = '🟡'
        inspection_status = 'Incomplete'
    elif total_answered_count == total_questions_count and inspection.status == "in_progress":
        inspection_icon = "🟠"
        inspection_status = 'Ready to Save'
    elif inspection.status == "draft":
        inspection_icon = "🟠"
        inspection_status = 'Draft'
    else:
        inspection_icon = "🟢"
        inspection_status = 'Complete'
        

    return {
        "inspection": inspection,
        "categories": inspections_data,
        "total_questions_count": total_questions_count,
        "total_answered_count": total_answered_count,
        "inspection_percentage": inspection_percentage,
        "inspection_status": inspection_status,
    }



# 1st DAILY INSPECTION CHECKLIST ITEMS PAGE 
def get_project_daily_inspection_new(
    current_user=None,
    project=None,
    inspection=None,
    missed_date=None,
):  

    today = timezone.now()
    inspections_data = []
    total_answered_count = 0
    total_questions_count = 0
    total_unanswered_count = 0

    if missed_date:
        inspection = None 
    else:
        if inspection is None:
            inspection = InspectionModel.objects.filter(
                Q(created_at__date=today) & Q(project=project) & Q(is_missed_inspection=False)
            ).first()
        else:
            inspection = inspection

    # ==================================================
    # CHECK IF INSPECTION CREATED IF NOT CREATE ONE
    # ==================================================
    if inspection == None:

        # Create Inspection For missed days
        if missed_date:
            inspection = InspectionModel.objects.create(
                project=project,
                status="in_progress",
                started_at=today,
                inspection_date = missed_date,
                is_missed_inspection =True,
                started_by=current_user,
            )

            # inspection reference 
            # inspection_date = missed_date
            inspection_id = inspection.id
            reference = generate_inspection_reference(
                inspection_id, missed_date)
            inspection.reference = reference
            inspection.save()

        # Create Inspection for today 
        else:
            inspection = InspectionModel.objects.create(
                project=project,
                status="in_progress",
                inspection_date=today,
                started_at=today,
                is_missed_inspection =False,
                started_by=current_user,
            )

            # inspection reference
            inspection_date = timezone.now().date()
            inspection_id = inspection.id
            reference = generate_inspection_reference(
                inspection_id, inspection_date)
            inspection.reference = reference
            inspection.save()
            

        # Get All Project Questions
        inspection_questions = InspectionQuestionModel.objects.filter((
            Q(is_default=True) &
            Q(project_question__isnull=True)
        ) |
            (
            Q(is_default=False) &
            Q(project_question=project)
        )).exclude(not_applicable=project).order_by(
            "category__order",
            "order",
        )

        # Create All Responses for All Questions
        InspectionResponseModel.objects.bulk_create([
            InspectionResponseModel(
                inspection=inspection,
                question=question,
            )
            for question in inspection_questions
        ])

        # =============== CREATE PROJECT TIMELINE ===============
        company = current_user.company
        ActivityModel.objects.create(
            company=company,
            project=project,
            user=current_user,
            activity_type='Inspection Started',
            description=f'{current_user.first_name} {current_user.last_name} started daily inspection',
            icon_type='inspection',
        )

    # ==================================================
    # GET INSPECTION CHECKLIST ITEMS
    # ==================================================
    inspection_questions = InspectionQuestionModel.objects.filter((
        Q(is_default=True) &
        Q(project_question__isnull=True)
    ) |
        (
        Q(is_default=False) &
        Q(project_question=project)
    )).exclude(not_applicable=project).order_by(
        "category__order",
        "order",
    )

    inspection_categories = InspectionCategoryModel.objects.filter(
        (
            Q(is_default=True) &
            Q(project__isnull=True)
        ) |
        (
            Q(is_default=False) &
            Q(project=project)
        )
    ).exclude(not_applicable=project)

    for category in inspection_categories:
        responses = InspectionResponseModel.objects.filter(
            question__category=category,
            inspection=inspection,
        ).prefetch_related(
            "inspection_response",
        )

        total_questions = responses.count()
        total_answered = responses.filter(
            answer__isnull=False
        ).exclude(
            answer=""
        ).count()

        total_unanswered = responses.filter(answer=None)
        total_unanswered_count += total_unanswered.count()

        failed_items = responses.filter(answer="fail").count()

        total_answered_count += total_answered
        total_questions_count += total_questions
        inspections_data.append({
            "category": category,
            "jamal": 'jamal',
            "responses": responses,
            "total_questions": total_questions,
            "total_answered": total_answered,
            "failed_items": failed_items,
        })

    inspection_percentage = int(
        (total_answered_count / total_questions_count) * 100)

    # DAILY INSPECTIONS STATUS
    if total_unanswered_count > 0:
        inspection_icon = '🟡'
        inspection_status = 'Incomplete'
    elif total_answered_count == total_questions_count and inspection.status == "in_progress":
        inspection_icon = "🟠"
        inspection_status = 'Ready to Save'
    elif inspection.status == "draft":
        inspection_icon = "🟠"
        inspection_status = 'Draft'
    else:
        inspection_icon = "🟢"
        inspection_status = 'Complete'

    return {
        "inspection": inspection,
        "categories": inspections_data,
        "total_questions_count": total_questions_count,
        "total_answered_count": total_answered_count,
        "inspection_percentage": inspection_percentage,
        "inspection_status": inspection_status,
    }



# ==========================================================================================     


# PDF INSPECTIONS DATA
def get_pdf_inspections_data(
        inspection=None
):
    total_checklist_questions = 0
    total_unanswered = 0
    total_failed_questions = 0 
    total_pass_questions = 0 
    total_na_questions = 0 


    # GET ALL THE CHECKLIST RESPONSES 
    checklist = (
        InspectionResponseModel.objects
        .filter(
            inspection=inspection
        )
        .select_related(
            "question",
            "question__category",
        )
        .order_by(
            "question__category__order",
            "question__order",
        )
    )

    # GROUP RESPONSES BY CATEGORY
    grouped_checklist = defaultdict(list)

    for response in checklist:
        category = response.question.category
        grouped_checklist[category].append(response)


    # CONVERT INTO TEMPLATE-FRIENDLY STRUCTURE
    grouped_checklist = [
        {
            "category": category,
            "name": category.name,
            "responses": responses,

            # Statistics
            "tot_question": len(responses),

            "an_questions": sum(
                1 for response in responses
                if response.answer is not None
            ),

            "failed_questions": sum(
                1
                for response in responses
                if response.answer == "fail"
            ),

            # Status
            "status": (
                "Pending"
                if sum(1 for response in responses if response.answer is not None) == 0
                else "Complete"
                if sum(1 for response in responses if response.answer is not None) == len(responses)
                else "Incomplete"
            ),
        }
        for category, responses in grouped_checklist.items()
    ]


    # CHECK TOTAL QUESTIONS,FAILED,PASS AND NA QUESTIONS COUNTS

    for item in checklist:
        total_checklist_questions += 1

        # Not answered count 
        if item.answer == None:
            total_unanswered += 1

        # Failed checklist 
        elif item.answer == 'fail':

            total_failed_questions += 1

        # Pass checklist 
        elif item.answer == 'pass':
            total_pass_questions += 1

        # NA checklist 
        elif item.answer == 'na':
            total_na_questions += 1


    # CERATE DAILY INSPECTION STATUS
    if total_unanswered > 0:
        inspection_status = 'Incomplete'
    else:
        inspection_status = 'Complete'

    return{
        "grouped_checklist": grouped_checklist,
        "inspection_status": inspection_status,
        "total_checklist_questions": total_checklist_questions,
        "total_failed_questions": total_failed_questions,
        "total_pass_questions": total_pass_questions,
        "total_na_questions": total_na_questions
    }