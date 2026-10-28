from django.db import models
from account.models import *

# Create your models here.


class SubcontractorRelation(models.Model):
    main_contractor = models.ForeignKey(
        CompanyProfileModel,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="principal_contractor"
    )
    subcontractor = models.ForeignKey(
        CompanyProfileModel,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="sub_contractor"
    )
    created_by = models.ForeignKey(
        'authentication.UserModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="created_by_contractor")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.main_contractor.company_name} - {self.subcontractor.company_name}"
