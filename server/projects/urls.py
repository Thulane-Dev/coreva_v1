
from django.urls import path
from .import views

app_name = "projects"

urlpatterns = [
    path('projects/', views.ProjectsView, name='projects'),
    path('add-project/', views.AddProjectView, name='add-project'),
    path('save-new-project', views.save_new_project, name='save-new-project'),
    path('project-setting/<uuid:project_uuid>/',
             views.ProjectSettingsView, name='project-setting'),
    path('project-view/<uuid:project_uuid>/',
         views.ProjectDetailsPreviewDetails, name='project-view'),
     path('save-project-update/<uuid:project_uuid>/',
              views.save_projects_updates, name='save-project-update'),
    # Deliveries urls 
    path('log-delivery/<uuid:project_uuid>/',
         views.LogProjectDeliveryView, name='log-delivery'),
    path('save-new-delivery/<uuid:project_uuid>/',
         views.save_new_delivery, name='save-new-delivery'),
     path('project-deliveries/<uuid:project_uuid>/',
         views.ProjectDeliveriesPageView, name='project-deliveries'),
     path('delivery/<uuid:delivery_uuid>/',
              views.DeliveryDetailsView, name='delivery'),
    path('project-activity/<uuid:project_uuid>/',
         views.ProjectActivityDetailsPageView, name='project-activity'),



    # OFFCANVAS FORMS URLS 
     path('log-new-project-issue/<uuid:project_uuid>/',
          views.SaveIssueOffcanvasView, name='log-new-project-issue'),
     path('log-new-project-task/<uuid:project_uuid>/',
               views.SaveTaskOffcanvasView, name='log-new-project-task'),
     path('log-new-project-incident/<uuid:project_uuid>/',
                    views.SaveIncidentOffcanvas, name='log-new-project-incident'),
     path('save-new-project-delivery/<uuid:project_uuid>/',
                         views.SaveDeliveryOffcanvas, name='save-new-project-delivery'),
     path('save-new-project-attachments/<uuid:project_uuid>/',
                              views.SaveProjectPhotosOffcanvas, name='save-new-project-attachments'),
]
