from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('authentication.urls')),
    path('', include('client.urls')),
    path('', include('dashboard.urls')),
    path('', include('account.urls')),
    path('', include('projects.urls')),
    path('', include('inspections.urls')),
    path('', include('issues.urls')),
    path('', include('incidents.urls')),
    path('', include('report.urls')),
    path('', include('contractors.urls')),
    path('', include('team.urls')),

]
    

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)