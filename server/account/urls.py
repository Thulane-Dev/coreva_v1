
from django.urls import path
from .import views

app_name = "account"

urlpatterns = [
    path('account', views.AccountView, name='account'),
    path('update-account-details', views.update_account_details, name='update-account-details'),
    path('company-details', views.CompanyDetailsView, name='company-details'),
    path('update-company-details', views.UpdateCompanyDetails, name='update-company-details'),
    path('deactivate-company', views.DeactivateCompanyView, name='deactivate-company'),
    path('account-setup', views.AccountSetupView, name='account-setup'),
    path('save-account-setup', views.save_account_setup, name='save-account-setup'),
    path('invite-team-member', views.InviteTeamMemberView, name='invite-team-member'),
    path('pending-invite/<uuid:invite_uuid>/',
             views.PendingUserInviteView, name='pending-invite'),
    
]
