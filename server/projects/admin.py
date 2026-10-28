from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(ProjectModel)
admin.site.register(ProjectUserModel)
admin.site.register(ProjectContractor)
admin.site.register(DeliveryModel)
admin.site.register(DeliveredItemsModel)
admin.site.register(ProjectUploadedFiles)
admin.site.register(ActivityModel)