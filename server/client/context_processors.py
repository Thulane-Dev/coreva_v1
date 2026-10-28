from authentication.models import UserModel
from django.db.models import Prefetch


from account.models import(
    CompanySubscriptionModel,
    PaymentModel,
)


def company_context_old_function(request):
    if request.user.is_authenticated:
        try:
            current_user = UserModel.objects.get(user=request.user)

            return {
                "company": current_user.company
            }

        except UserModel.DoesNotExist:
            pass

    return {
        "company": None
    }


def company_context_older(request):
    if request.user.is_authenticated:
        try:
            current_user = UserModel.objects.select_related(
                "company",
                "company__subscription",
                "company__subscription__plan",
            ).get(user=request.user)

            company = current_user.company

            return {
                "company": company,
                "subscription": getattr(company, "subscription", None),
                "plan": (
                    company.subscription.plan
                    if hasattr(company, "subscription")
                    else None
                ),
            }

        except UserModel.DoesNotExist:
            pass

    return {
        "company": None,
        "subscription": None,
        "plan": None,
    }


def company_context(request):

    # next_url = request.GET.get("next")

    next_url = request.GET.get("next", "")
    section = request.GET.get("section", "")
    if section:
        next_url = f"{next_url}#{section}"

    if not request.user.is_authenticated:
        return {
            "company": None,
            "subscription": None,
            "plan": None,
            "payments": [],
            "latest_payment": None,
        }

    try:

        current_user = (
            UserModel.objects
            .select_related(
                "company",
                "company__subscription",
                "company__subscription__plan",
            )
            .prefetch_related(
                Prefetch(
                    "company__subscription__payments",
                    queryset=PaymentModel.objects.order_by("-created_at"),
                    to_attr="all_payments",
                )
            )
            .get(
                user=request.user
            )
        )

        company = current_user.company

        subscription = getattr(
            company,
            "subscription",
            None
        )

        plan = (
            subscription.plan
            if subscription
            else None
        )

        payments = (
            subscription.all_payments
            if subscription
            else []
        )

        latest_payment = (
            payments[0]
            if payments
            else None
        )

        return {
            "company": company,
            "subscription": subscription,
            "plan": plan,
            "payments": payments,
            "latest_payment": latest_payment,
            "next_url": next_url,
        }

    except UserModel.DoesNotExist:

        return {
            "company": None,
            "subscription": None,
            "plan": None,
            "payments": [],
            "latest_payment": None,
            "next_url": next_url,
        }