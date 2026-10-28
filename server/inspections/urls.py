
from django.urls import path
from .import views

app_name = "inspections"

urlpatterns = [
    # Placeholder 
    path('inspections/',
         views.DailyInspectionView, name='inspections'),

    # Inspection Urls 
    path('checklist/<uuid:project_uuid>/',
             views.ProjectDailyInspectionsView, name='checklist'),
     path('checklist/<uuid:project_uuid>/<uuid:inspection_uuid>/',
                  views.ProjectDailyInspectionsView, name='checklist'),


     # Admin SIgn Off 
     path('admin-sign-off/<uuid:project_uuid>/',
                  views.admin_sign_off, name='admin-sign-off'),
     path('admin-sign-off/<uuid:project_uuid>/<uuid:inspection_uuid>/',
                    views.admin_sign_off, name='admin-sign-off'),

    path('update-inspection-response/<int:response_id>/',
         views.update_inspection_response, name='update-inspection-response'),
    path('add-issue/<int:response_id>/',
         views.create_new_issue, name='add-issue'),
    path('save-inspection/<uuid:inspection_uuid>/',
         views.save_inspection, name='save-inspection'),

     # MISSED INSPECTIONS 
     path('missed-inspections/<uuid:project_uuid>/',
         views.MissedDailyInspections, name='missed-inspections'),
     path('create-missed-inspection/<uuid:project_uuid>/',
              views.create_missed_inspection, name='create-missed-inspection'),

    path('project-inspections/<uuid:project_uuid>/',
         views.ProjectInspectionsPageView, name='project-inspections'),

     # EDIT INSPECTIONS ITEMS 
     path('inspection-items/<uuid:project_uuid>/',
                  views.ProjectInspectionItems, name='inspection-items'),
     path('save-category/<uuid:project_uuid>/',
                            views.save_new_category_view, name='save-category'),

                            
     path('remove-category/<uuid:project_uuid>/<uuid:category_uuid>/',
                                 views.remove_category_view, name='remove-category'),


     path('save-question/<uuid:category_uuid>/<uuid:project_uuid>/',
                       views.save_question_view, name='save-question'),
     path('remove-question/<uuid:question_uuid>/<uuid:project_uuid>/',
                            views.remove_question_view, name='remove-question'),

]
