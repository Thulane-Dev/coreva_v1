from django.apps import apps
from django.db.models import Q
from datetime import date
from django.utils import timezone
from collections import defaultdict
from datetime import timedelta
from datetime import datetime, date


from inspections.services.inspections_view import (
    get_project_details_inspection_data,
    get_project_daily_inspection_new,
    get_pdf_inspections_data
)


# Models Import
IssueModel = apps.get_model(
    "issues", "IssueModel")

DailyReportModel = apps.get_model(
    "report", "DailyReportModel")

DeliveryModel = apps.get_model(
    "projects", "DeliveryModel")

IncidentModel = apps.get_model(
    "incidents", "IncidentModel")

ProjectUploadedFiles = apps.get_model(
    "projects", "ProjectUploadedFiles")

ActivityModel = apps.get_model(
    "projects", "ActivityModel")


# Models Import
InspectionCategoryModel = apps.get_model(
    "inspections", "InspectionCategoryModel")
InspectionModel = apps.get_model(
    "inspections", "InspectionModel")
InspectionQuestionModel = apps.get_model(
    "inspections", "InspectionQuestionModel")
InspectionResponseModel = apps.get_model(
    "inspections", "InspectionResponseModel")


# GENERATE DAILY REPORT REFERENCE
def generate_daily_report_reference(project, report_date):

    if isinstance(report_date, str):
        report_date = datetime.strptime(
            report_date,
            "%Y-%m-%d"
        ).date()

    count = DailyReportModel.objects.filter(
        project=project,
        report_date=report_date
    ).count()

    sequence = count + 1

    return f"DR-{report_date.strftime('%Y%m%d')}-{sequence:03d}"


def get_daily_report(
        project,
        current_user=None,
        created_daily_report=None,
        missed_date=None,
):
    today = timezone.now()

    if missed_date:
        current_report = None 
    else:
        if created_daily_report:
            current_report = created_daily_report
        else:
            current_report = DailyReportModel.objects.filter(
                Q(project=project) & Q(report_date=today) & Q(is_missed_report=False)).first()
        
    # =========================
    # GET REPORT OR CREATE ONE
    # =========================
    if current_report == None:

        if missed_date:
            report_date = missed_date
            reference = generate_daily_report_reference(project,report_date)
            current_report = DailyReportModel.objects.create(
                reference=reference,
                project=project,
                report_date=missed_date,
                status='draft',
                is_missed_report= True,
                created_by=current_user,
            )
        else:
            report_date = timezone.now().date()
            reference = generate_daily_report_reference(project,report_date)

            current_report = DailyReportModel.objects.create(
                reference=reference,
                project=project,
                report_date=today,
                status='draft',
                created_by=current_user,
            )

        # =============== CREATE PROJECT TIMELINE ===============
        company = current_user.company
        ActivityModel.objects.create(
            company=company,
            project=project,
            user=current_user,
            activity_type='Daily Report Created',
            description=f'{current_user.first_name} {current_user.last_name} created a daily report',
            icon_type='report',
        )
    else:
        current_report = current_report

    # REPORT DATE
    report_date = current_report.report_date

    # =========================
    # TASKS
    # =========================
    # tasks = IssueModel.objects.filter(
    #     Q(project=project) &
    #     Q(type='task') &
    #     (
    #         Q(status='open') |
    #         Q(created_at__date=today)
    #     )
    # ).order_by('-created_at')

    # TASKS: Due today, overdue, or created today with no future due date
    tasks = IssueModel.objects.filter(
        Q(project=project) &
        Q(type='task') &
        Q(status='open') &
        (
            Q(due_date__lte=today) |
            Q(created_at__date=today, due_date__isnull=True)
        )
    ).order_by('-created_at')

    # FUTURE TASKS: Due after today
    future_tasks = IssueModel.objects.filter(
        Q(project=project) &
        Q(type='task') &
        Q(status='open') &
        Q(due_date__gt=today)
    ).order_by('due_date', '-created_at')


    # =========================
    # ISSUES
    # =========================
    issues = IssueModel.objects.filter(
        Q(project=project) & Q(type='issue') &
        (
            Q(status='open') |
            Q(created_at__date=today)
        )).order_by('-created_at')

    # =========================
    # DELIVERIES
    # =========================
    deliveries = DeliveryModel.objects.filter(
        Q(project=project) & Q(delivery_date=today)).order_by('-created_at')

    # =========================
    # INCIDENTS
    # =========================
    incidents = IncidentModel.objects.filter(
        Q(project=project) & Q(incident_date=today)).order_by('-created_at')

    # =========================
    # FILES
    # =========================
    files = ProjectUploadedFiles.objects.filter(
        Q(report=current_report))



    # =========================
    # CREATE OR GET MISSED DAILY REPORT
    # =========================
    if created_daily_report:
        inspection_model = InspectionModel.objects.filter(inspection_date=created_daily_report.report_date).first()
        # if there is an inspection created 
        if inspection_model:
            inspection_data_new = get_project_daily_inspection_new(
                            project=project, current_user=current_user,inspection=inspection_model)
            inspection = inspection_data_new['inspection']
        else:
            # create new inspection cos it was missed 
            inspection_data_new = get_project_daily_inspection_new(
                            project=project, current_user=current_user,missed_date=created_daily_report.report_date)
            inspection = inspection_data_new['inspection']
    else:
        # =========================
        # New Daily Inspections
        # =========================
        inspection = InspectionModel.objects.filter(
            Q(created_at__date=today) & Q(project=project)
        ).first()


    if inspection:
        daily_inspection_data = get_project_details_inspection_data(
            inspection=inspection)
        categories = daily_inspection_data['grouped_checklist']
        inspection_status = daily_inspection_data['inspection_status']
        inspection_btn = daily_inspection_data['inspection_btn']
        total_checklists = daily_inspection_data['total_checklists']
        failed_inspections_count = daily_inspection_data['failed_inspections_count']
        total_passed_count = daily_inspection_data['total_passed_count']
        total_na_count = daily_inspection_data['total_na_count']
    else:
        categories = {}
        inspection_status = 'Not Started'
        inspection_btn = 'Start Inspection'

    return {
        "report": current_report,
        "tasks": tasks,
        "future_tasks": future_tasks,
        "issues": issues,
        "deliveries": deliveries,
        "incidents": incidents,
        "files": files,

        # DAILY INSPECTION
        "inspection": inspection,
        "categories": categories,
        "inspection_status": inspection_status,
        "inspection_btn": inspection_btn,
        "total_checklists" : total_checklists,
        "failed_inspections_count" : failed_inspections_count,
        "total_passed_count" : total_passed_count,
        "total_na_count" : total_na_count,
    }



# GET MISSED REPORT DATES DETAILS PAGE  NOT PROJECT WORKING DAYS
def get_missed_report_days_old_no(project):
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    print(project.working_days)

    current_date = max(
        project.start_date,
        project.created_at.date()
    )

    missed_days = []

    while current_date <= yesterday:

        # Monday-Friday only
        if current_date.weekday() < 5:

            report_exists = DailyReportModel.objects.filter(
                project=project,
                report_date=current_date,
            ).exists()

            if not report_exists:
                missed_days.append(current_date)

        current_date += timedelta(days=1)

    return missed_days


def get_missed_report_days(project):

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

            report_exists = DailyReportModel.objects.filter(
                project=project,
                report_date=current_date,
            ).exists()

            if not report_exists:
                missed_days.append(current_date)

        current_date += timedelta(days=1)

    return missed_days


def get_daily_report_pdf_data(
        report=None,
        project=None
):
    today = timezone.now()

    # =========================
    # TODAYS REPORT DATA
    # =========================
    if report.is_missed_report == False:

        # ********** Tasks **********
        tasks = IssueModel.objects.filter(
            Q(project=project) &
            Q(type='task') &
            (
                Q(status='open') |
                Q(created_at__date=today) |
                Q(status='closed', created_at__date=today)
            )
        ).order_by('-created_at')

        # ********** Future Tasks **********
        future_tasks = IssueModel.objects.filter(
            Q(project=project) &
            Q(type='task') &
            Q(status='open') &
            Q(due_date__gt=today)
        ).order_by('due_date', '-created_at')

        # ********** Issues **********
        issues = IssueModel.objects.filter(
            Q(project=project) &
            Q(type='issue') &
            (
                Q(status='open') |
                Q(created_at__date=today) |
                Q(status='closed', created_at__date=today)
            )
        ).order_by('-created_at')

        # ********** Deliveries **********
        deliveries = (
            DeliveryModel.objects
            .filter(Q(project=project) & Q(delivery_date=today))
            .prefetch_related("delivered_item")
            .order_by("-delivery_date")
        )

        # ********** Incidents **********
        incidents = (
            IncidentModel.objects
            .filter(
                project=project,
                incident_date=today,
            )
            .prefetch_related("injured_person")
            .order_by("-incident_time", "-created_at")
        )

        # ********** Files **********
        files = ProjectUploadedFiles.objects.filter(
                Q(report=report))

        # ********** Daily Inspection **********
        inspection = InspectionModel.objects.filter(
            Q(inspection_date=today) & Q(project=project)
        ).first()   

        inspection_data = get_pdf_inspections_data(inspection=inspection)
        inspections = inspection_data['grouped_checklist']
        inspection_status = inspection_data['inspection_status']
        total_checklist_questions = inspection_data['total_checklist_questions']
        total_failed_questions = inspection_data['total_failed_questions']
        total_pass_questions = inspection_data['total_pass_questions']
        total_na_questions = inspection_data['total_na_questions']


    # =========================
    # MISSED REPORT DATA
    # =========================
    else:
        report_date = report.report_date

        # ********** Tasks **********
        tasks = IssueModel.objects.filter(
            Q(project=project) &
            Q(type='task') &
            Q(created_at__date=report_date)
        ).order_by('-created_at')

        # ********** Future Tasks **********
        future_tasks = {}

        # ********** Issues **********
        issues = IssueModel.objects.filter(
            Q(project=project) &
            Q(type='issue') &
            Q(created_at__date=report_date)
        ).order_by('-created_at')

        # ********** Deliveries **********
        deliveries = (
            DeliveryModel.objects
            .filter(Q(project=project) & Q(delivery_date=report_date))
            .prefetch_related("delivered_item")
            .order_by("-delivery_date")
        )

        # ********** Incidents **********
        incidents = (
            IncidentModel.objects
            .filter(
                project=project,
                incident_date=report_date,
            )
            .prefetch_related("injured_person")
            .order_by("-incident_time", "-created_at")
        )

        # ********** Files **********
        files = ProjectUploadedFiles.objects.filter(
                Q(report=report))

        # ********** Daily Inspection **********
        inspection = InspectionModel.objects.filter(
            Q(inspection_date=report_date) & Q(project=project)
        ).first()   

        inspection_data = get_pdf_inspections_data(inspection=inspection)
        inspections = inspection_data['grouped_checklist']
        inspection_status = inspection_data['inspection_status']
        total_checklist_questions = inspection_data['total_checklist_questions']
        total_failed_questions = inspection_data['total_failed_questions']
        total_pass_questions = inspection_data['total_pass_questions']
        total_na_questions = inspection_data['total_na_questions']
    
    # Total Completed Inspection Checks 
    total_checks = total_failed_questions + total_pass_questions + total_na_questions


    return {
        "report": report,
        "tasks": tasks,
        "future_tasks": future_tasks,
        "issues": issues,
        "deliveries": deliveries,
        "incidents": incidents,
        "files": files,

        # DAILY INSPECTION
        "inspection": inspection,
        "inspections": inspections,
        "inspection_status": inspection_status,
        "total_checklist_questions": total_checklist_questions,
        "total_checks": total_checks,
        "total_failed_questions": total_failed_questions,
        "total_pass_questions": total_pass_questions,
        "total_na_questions": total_na_questions,
    }


    
