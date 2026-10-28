
from django.urls import path
from .import views

app_name = "contractors"

urlpatterns = [
    path('company-contractors/',
             views.CompanyContractorsView, name='company-contractors'),

    path('project-contractors/<uuid:project_uuid>/',
         views.ProjectContractors, name='project-contractors'),

     # ADD CONTRACTOR OPTIONS URLS 
    path('add-contractor/<uuid:project_uuid>/',
         views.AddContractorView, name='add-contractor'),
    path('save-select-existing-contractor/<uuid:project_uuid>/',
              views.save_select_existing_contractor, name='save-select-existing-contractor'),
    path('save-new-contractor/<uuid:project_uuid>/',
                  views.save_new_contractor, name='save-new-contractor'),
    path('search-coreva-contractor/<uuid:project_uuid>/',
                      views.search_coreva_contractor, name='search-coreva-contractor'),
    path('add-found-contractor/<uuid:project_uuid>/<uuid:contractor_uuid>/',
                                 views.add_found_contractor_function, name='add-found-contractor'),

    
     path('edit-contractor/<uuid:contractor_uuid>/',
              views.EditContractorDetailsView, name='edit-contractor'),
     path('link-contractor-account/<uuid:contractor_uuid>/',
                   views.LinkContractorAccountView, name='link-contractor-account'),
     path('search-contractor-profile/<uuid:project_contractor_uuid>/',
                        views.Search_contractor_profile, name='search-contractor-profile'),
     path('connect-contractor/<uuid:project_contractor_uuid>/<uuid:contractor_uuid>/',
                             views.Connect_found_contractor, name='connect-contractor'),
     path('contractor/<uuid:contractor_uuid>/',
              views.ContractorDetailsPage, name='contractor'),

     # Contractor Portal 
     path('workspace/<uuid:contractor_uuid>/',
               views.ContractorPortalView, name='workspace'),
     path('workspace-project/<uuid:project_uuid>/<uuid:portal_uuid>/',
               views.ContractorPortalProjectView, name='workspace-project'),
     path('work/<uuid:issue_uuid>/<uuid:portal_uuid>/',
               views.ViewWorkDetailsPage, name='work'),
     path('save-contractor-comment/<uuid:issue_uuid>/<uuid:contractor_uuid>/',
              views.save_contractor_comment, name='save-contractor-comment'),
     path('mark-contractor-issue-read/<uuid:issue_uuid>/<uuid:contractor_uuid>/',
              views.mark_contractor_issue_read, name='mark-contractor-issue-read'),
     path('save-contractor-work-stage/<uuid:issue_uuid>/<uuid:contractor_uuid>/',
                   views.save_contractor_work_stage, name='save-contractor-work-stage'),
]
