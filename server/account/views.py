from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
from django.utils import timezone
from urllib.parse import urlencode


# Models Import
from .models import *
from authentication.models import *




# ============= Account Setup View =============
def AccountSetupView(request):
    work_days = [
        ("monday", "Monday"),
        ("tuesday", "Tuesday"),
        ("wednesday", "Wednesday"),
        ("thursday", "Thursday"),
        ("friday", "Friday"),
        ("saturday", "Saturday"),
        ("sunday", "Sunday"),
    ]

    context = {
        "work_days": work_days,
    }
    return render(request, 'account/account_setup.html', context)


# ============= Save Account Setup =============
@require_POST
def save_account_setup(request):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)

    # Create Address Model Object
    save_address = AddressModel.objects.create(
        street_address=request.POST.get("street"),
        city=request.POST.get("city"),
        province=request.POST.get("province"),
        country=request.POST.get("country"),
    )

    # Check if company logo uploaded
    logo = request.FILES.get("logo")
    if logo:
        uploaded_logo = logo
    else:
        uploaded_logo = None

    # Create Company Profile Model Object
    save_company = CompanyProfileModel.objects.create(
        company_name=request.POST.get("company_name"),
        email=request.POST.get("email"),
        phone=request.POST.get("phone"),
        address=save_address,
        logo=uploaded_logo,
        added_by=current_user,
        owner=current_user,
    )

    # Update User Account Details
    current_user.company = save_company
    current_user.account_complete = True
    current_user.save()


    CompanySubscriptionModel.objects.create(
        company=save_company,
        plan=SubscriptionPlanModel.objects.get(code="starter"),
        trial_started_at=timezone.now(),
        trial_ends_at=timezone.now() + timedelta(days=14),
    )

    messages.success(
        request,
        f"🎉 Account successfully setup."
    )

    # 🎯 Redirect To Dashboard
    url = reverse('dashboard:today')
    return redirect(f"{url}")


# ============= Account View =============
def AccountView(request):

    user = get_object_or_404(
        UserModel.objects.select_related(
            "company",
            "address",
        ),
        user=request.user,
    )

    company = user.company

    context = {
        "account_user": user,
        "company" : company,
        "page": "account/account.html",
    }

    if request.htmx:
        return render(request, "account/account.html", context)
    return render(request, "client/base.html", context)


def post(self, request):
        user = get_object_or_404(
            UserModel.objects.select_related(
                "company",
                "address",
            ),
            user=request.user,
        )

        user.first_name = request.POST.get("first_name", "").strip()
        user.last_name = request.POST.get("last_name", "").strip()
        user.job_title = request.POST.get("job_title", "").strip()
        user.phone = request.POST.get("phone", "").strip()
        user.whatsappNumber = request.POST.get(
            "whatsapp",
            ""
        ).strip()

        user.save()

        messages.success(
            request,
            "Your account details have been updated."
        )

        return redirect("authentication:account")


# ============= Save Account Setup =============
@require_POST
def update_account_details(request):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)

    current_user.first_name = request.POST.get("first_name", "").strip()
    current_user.last_name = request.POST.get("last_name", "").strip()
    current_user.job_title = request.POST.get("job_title", "").strip()
    current_user.phone = request.POST.get("phone", "").strip()
    current_user.whatsappNumber = request.POST.get(
        "whatsapp",
        ""
    ).strip()

    current_user.save()

    messages.success(
        request,
        "Your account details have been updated."
    )

    # 🎯 Redirect To Account
    url = reverse('account:account')
    return redirect(f"{url}")





# ============= Invite Team Member View =============
def InviteTeamMemberView(request):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company

    back_url = request.GET.get("back_url") or reverse("team:team")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("name", "").strip()
        role = request.POST.get("role", "").strip()

        # Redirect back to the invite form while preserving back_url.
        invite_form_url = reverse("account:invite-team-member")
        redirect_url = (
            f"{invite_form_url}?{urlencode({'back_url': back_url})}"
        )

        # Basic validation
        if not email or not first_name or role not in ["admin", "user"]:
            messages.error(
                request,
                "Please provide a name, valid email address and access level."
            )
            return redirect(redirect_url)

        # Check whether this email already exists.
        existing_user = User.objects.filter(
            email__iexact=email
        ).first()

        if existing_user:
            # Is there already a pending invitation for this company?
            pending_invite = UserInvite.objects.filter(
                user=existing_user,
                company=company,
                is_used=False,
            ).first()

            if pending_invite:
                messages.error(
                    request,
                    f"An invitation has already been created for "
                    f"{email}. You can find it under Pending Team Invites."
                )
            else:
                messages.error(
                    request,
                    f"The email address {email} is already associated "
                    f"with a Coreva account or another invitation."
                )

            return redirect(redirect_url)

        # Create a unique username instead of using the first name.
        new_user = User(
            username=f"invite_{uuid.uuid4().hex}",
            email=email,
            first_name=first_name,
        )

        new_user.set_unusable_password()
        new_user.save()

        # Create the invitation.
        invite = UserInvite.objects.create(
            user=new_user,
            company=company,
            role=role,
        )

        messages.success(
            request,
            "Invitation successfully created."
        )

        # Redirect to the pending invitation details.
        url = reverse(
            "account:pending-invite",
            args=[invite.token]
        )

        return redirect(
            f"{url}?{urlencode({'back_url': back_url})}"
        )

    context = {
        "page": "account/invite_team.html",
        "back_url": back_url,
    }

    if request.htmx:
        return render(request, "account/invite_team.html", context)

    return render(request, "client/base.html", context)





# ============= Invite Team Member View=============
def InviteTeamMemberView_old(request):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company

    if request.method == "POST":
        email = request.POST.get("email")
        first_name = request.POST.get("name")
        role = request.POST.get("role")

        # # Create user without password
        user = User.objects.create(
            username=first_name,
            email=email,
        )

        user.set_unusable_password()
        user.save()

        # # create user invite
        invite = UserInvite.objects.create(
            user=user,
            company=company,
            role=role,
        )

        message = "Invite successfully added."

        back_url = reverse(
            "team:team",
        )
        # Redirect to tasks details, preserving back_url
        url = reverse("account:pending-invite", args=[invite.token])
        return redirect(f"{url}?{urlencode({'back_url': back_url})}")

    back_url = request.GET.get("back_url") or reverse(
        "team:team",
    )

    context = {
        "page": "account/invite_team.html",
        "back_url" : back_url,
    }

    if request.htmx:
        return render(request, "account/invite_team.html", context)
    return render(request, "client/base.html", context)


# ============= Pending Team Invite View =============
def PendingUserInviteView(request, invite_uuid):
    pending_invite = get_object_or_404(
        UserInvite.objects.select_related(
            "user",
            "company",
            "contractor",
        ),
        token=invite_uuid,
    )

    invite_url = request.build_absolute_uri(
        reverse(
            "accept_invite",
            kwargs={"token": pending_invite.token},
        )
    )

    invited_user = pending_invite.user

    back_url = request.GET.get("back_url") or reverse(
        "team:team",
    )

    context = {
        "pending_invite": pending_invite,
        "invite_url": invite_url,
        "invited_user": invited_user,
        "back_url" : back_url,
        "page": "invites/pending_user_invite.html",
    }

    if request.htmx:
        return render(request, "invites/pending_user_invite.html", context)
    return render(request, "client/base.html", context)


# ============= Company Details View =============
def CompanyDetailsView(request):

    user = get_object_or_404(
        UserModel.objects.select_related(
            "company",
            "address",
        ),
        user=request.user,
    )

    company = user.company

    context = {
        "account_user": user,
        "company" : company,
        "page": "account/company_details.html",
    }

    if request.htmx:
        return render(request, "account/company_details.html", context)
    return render(request, "client/base.html", context)


@require_POST
def UpdateCompanyDetails(request):

    current_user = get_object_or_404(
        UserModel,
        user=request.user
    )

    company = current_user.company

    # Check if company logo uploaded
    logo = request.FILES.get("logo")
    if logo:
        company.logo = logo

    company.company_name=request.POST.get("company_name")
    company.industry=request.POST.get("industry")
    company.contact_name=request.POST.get("contact_name")
    company.email=request.POST.get("email")
    company.phone=request.POST.get("phone")
    company.whatsapp=request.POST.get("whatsapp")

    # Address Details 
    address = company.address
    address.street_address=request.POST.get("street_address")
    address.city=request.POST.get("city")
    address.province=request.POST.get("province")
    address.postal_code=request.POST.get("postal_code")
    address.country=request.POST.get("country") 
    address.save()

    # Save company details 
    company.save()
    
    

    messages.success(
        request,
        "Company details have been updated."
    )

    return redirect("account:company-details")



@require_POST
def DeactivateCompanyView(request):

    current_user = get_object_or_404(
        UserModel,
        user=request.user
    )

    company = current_user.company

    company.status = "de-active"
    company.save(update_fields=["status"])

    messages.success(
        request,
        "Your company has been deactivated."
    )

    logout(request)

    return redirect("login")