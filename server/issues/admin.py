from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(IssueModel)
admin.site.register(IssueCommentModel)
admin.site.register(WorkStageModel)
admin.site.register(IssueActivityView)




