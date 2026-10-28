from django.urls import path
from .import views

app_name = "dashboard"

urlpatterns = [
    path('today', views.TodaysDashboardViewNew, name='today'),
    path('filter-projects', views.FilterProjectsView, name='filter-projects'),
]