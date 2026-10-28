
from django.urls import path
from .import views

app_name = "issues"

urlpatterns = [
    path('issues-placeholder/',
         views.IssuesPlaceHolder, name='issues-placeholder'),

    # Issues URLS 
    path('log-issue/<uuid:project_uuid>/',
         views.AddIssueView, name='log-issue'),
    path('save-issue/<uuid:project_uuid>/',
         views.save_issue_post, name='save-issue'),

    # Tasks URLS 
    path('add-task/<uuid:project_uuid>/',
         views.AddIssueView, name='add-task'),

     path('project-issues/<uuid:project_uuid>/',
         views.ProjectIssuesPageView, name='project-issues'),



    path('project-tasks/<uuid:project_uuid>/',
         views.ProjectTasksPageView, name='project-tasks'),
    # UPDATE ISSUE URLS
    path('issue/<uuid:issue_uuid>/',
         views.IssuePreview, name='issue'),
    path('update-issue-status/<uuid:issue_uuid>/',
         views.update_issue_status, name='update-issue-status'),
    path('update-issue/',
         views.save_issue_update, name='update-issue'),
    path('save-issue-comment/<uuid:issue_uuid>/',
         views.save_issue_comment, name='save-issue-comment'),
    path('mark-issue-read/<uuid:issue_uuid>/',
         views.mark_issue_read, name='mark-issue-read'),
    # Tasks Urls
    path('task/<uuid:issue_uuid>/',
         views.TasksPreview, name='task'),

     # COMMENTS URLS 
     path('save-item-comment/<uuid:issue_uuid>/',
          views.save_item_comment, name='save-item-comment'),
     path('mark-item-read/<uuid:issue_uuid>/',
                   views.mark_item_as_read, name='mark-item-read'),
     path('save-work-progress/<uuid:issue_uuid>/',
                        views.save_user_work_stage, name='save-work-progress'),

     # FILTER ISSUE ITEMS 
     path('filter-issues/<uuid:project_uuid>/',
              views.filter_project_issues_view, name='filter-issues'),
     # FILTER TASKS ITEMS 
     path('filter-tasks/<uuid:project_uuid>/',
               views.filter_project_tasks_view, name='filter-tasks'),

     # ISSUE ACTIVITY STATUS 
     path('update-issue-activity/<uuid:issue_uuid>/',
               views.update_issue_activity, name='update-issue-activity'),
     path('update-task-activity/<uuid:issue_uuid>/',
                    views.update_task_activity, name='update-task-activity'),
]
