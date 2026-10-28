
from django.urls import path
from .import views

app_name = "team"

urlpatterns = [
    path('project-team/<uuid:project_uuid>/', views.ProjectTeamMembersView, name='project-team'),
    path('member/<uuid:project_uuid>/<uuid:member_uuid>/', views.MemberDetailsPage, name='member'),
    path('add-team-member/<uuid:project_uuid>/', views.add_team_member, name='add-team-member'),
    path('remove-member-project/<uuid:project_uuid>/<uuid:member_uuid>/', views.remove_member_project, name='remove-member-project'),
    # Company Team 
    path('team', views.CompanyTeamView, name='team'),
    path('team-member-details/<uuid:member_uuid>/', views.TeamMemberDetailsView, name='team-member-details'),
]
