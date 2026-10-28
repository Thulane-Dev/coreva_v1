from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(AddressModel)
admin.site.register(CompanyProfileModel)
admin.site.register(ConnectedContractorCompaniesModel)
admin.site.register(SubscriptionPlanModel)
admin.site.register(CompanySubscriptionModel)
admin.site.register(PaymentModel)