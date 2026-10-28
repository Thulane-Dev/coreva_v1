
from django.urls import path
from .import views

app_name = "report"

urlpatterns = [
    path('report-placeholder/<uuid:report_uuid>/',
         views.ReportPlaceHolder, name='report-placeholder'),
    path('create-report/<uuid:project_uuid>/',
         views.CreateReportView, name='create-report'),
     path('create-report/<uuid:project_uuid>/<uuid:report_uuid>/',
              views.CreateReportView, name='create-report'),
     path('create-missed-report/<uuid:project_uuid>/',
              views.create_missed_report, name='create-missed-report'),

    # Partial Report Urls 
    path('issue-save-daily/<uuid:project_uuid>/',
         views.create_report_issue, name='issue-save-daily'),
    path('save-report-task/<uuid:project_uuid>/',
         views.create_report_task, name='save-report-task'),
    path('save-report-incident/<uuid:project_uuid>/',
         views.log_incident, name='save-report-incident'),
    path('save-delivery-item/<uuid:project_uuid>/',
         views.add_report_delivery, name='save-delivery-item'),
    path('save-report-planned-work/<uuid:project_uuid>/',
         views.create_report_planned_work, name='save-report-planned-work'),

    # Save Full Report Url 
    path('save-report/<uuid:report_uuid>/',
         views.save_full_report, name='save-report'),
     path('missed-daily-reports/<uuid:project_uuid>/',
         views.MissedDailyReports, name='missed-daily-reports'),
     path('project-reports/<uuid:project_uuid>/',
          views.ProjectReportsPageView, name='project-reports'),


     # Create PDF REPORT 
     path(
        "daily-reports/<uuid:report_uuid>/download/",views.daily_report_pdf,name="daily-report-pdf",),


    # HTMX PLACEHOLDER FORM SUBMIT 
    path('test-form-submit/',
         views.test_form_view, name='test-form-submit'),
]
