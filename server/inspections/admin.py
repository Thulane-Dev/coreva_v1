from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(InspectionCategoryModel)
admin.site.register(InspectionQuestionModel)
admin.site.register(InspectionModel)
admin.site.register(InspectionResponseModel)
