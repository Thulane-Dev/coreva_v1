from django.db import models
import uuid
from django.utils.timezone import now
from datetime import timedelta

# Create your models here.

def default_end_date():
    return now().date() + timedelta(days=14)


class AddressModel(models.Model):
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    province = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.street_address} - {self.city} {self.province}"


class CompanyProfileModel(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('de-active', 'De-Active'),
    ]
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    company_name = models.CharField(max_length=255, blank=True)
    address = models.ForeignKey(
        AddressModel, on_delete=models.CASCADE, null=True, blank=True)
    industry = models.CharField(max_length=200, default="Construction")
    contact_name = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    whatsapp = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(
        upload_to="media/company_logo/", null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active')
    added_by = models.ForeignKey(
                'authentication.UserModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="company_added_by")
    owner = models.ForeignKey(
           'authentication.UserModel', null=True, blank=True, on_delete=models.SET_NULL,related_name="company_owner")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company_name} - {self.industry}"


class SubscriptionPlanModel(models.Model):

    PLAN_CHOICES = [
        ('trial', 'Trial'),
        ('starter', 'Starter'),
        ('professional', 'Professional'),
        ('business', 'Business'),
    ]

    code = models.CharField(
        max_length=30,
        choices=PLAN_CHOICES,
        unique=True
    )

    name = models.CharField(
        max_length=50
    )

    monthly_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    max_projects = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    max_team_members = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    photo_storage_gb = models.PositiveIntegerField(
        default=1
    )

    subcontractor_portal = models.BooleanField(
        default=False
    )

    priority_support = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class CompanySubscriptionModel(models.Model):

    STATUS_CHOICES = [
        ("trial", "Trial"),
        ("active", "Active"),
        ("past_due", "Past Due"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
    ]

    company = models.OneToOneField(
        CompanyProfileModel,
        on_delete=models.CASCADE,
        related_name="subscription"
    )

    plan = models.ForeignKey(
        SubscriptionPlanModel,
        on_delete=models.PROTECT,
        related_name="subscriptions"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="trial"
    )

    trial_started_at = models.DateTimeField(
        null=True,
        blank=True
    )

    trial_ends_at = models.DateTimeField(
        null=True,
        blank=True
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True
    )

    current_period_start = models.DateTimeField(
        null=True,
        blank=True
    )

    current_period_end = models.DateTimeField(
        null=True,
        blank=True
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
            return f"{self.company.company_name} - {self.plan.name}"


class PaymentModel(models.Model):

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    subscription = models.ForeignKey(
        CompanySubscriptionModel,
        on_delete=models.PROTECT,
        related_name="payments"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )

    payment_date = models.DateTimeField(
        null=True,
        blank=True
    )

    due_date = models.DateTimeField(
        null=True,
        blank=True
    )

    reference = models.CharField(
        max_length=100,
        unique=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.subscription.company.company_name} - R{self.amount}"



class ConnectedContractorCompaniesModel(models.Model):
    company = models.ForeignKey(
            CompanyProfileModel, on_delete=models.CASCADE, null=True, blank=True,related_name='main_contractor_principle')
    connected_contractors = models.ManyToManyField(
                CompanyProfileModel, blank=True, default=None, related_name='connected_companies')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.company.company_name}"