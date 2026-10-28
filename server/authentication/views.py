from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import now
from datetime import date
from django.db.models import Q
from django.urls import reverse

from .models import *

# Extended Models
from client.models import *

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
# email imports start
from django.core.mail import send_mail
from django.conf import settings
# email imports end

# Authentication Imports start
from .forms import CreateUserForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .decorators import unauthenticated_user, allowed_user
from django.contrib.auth.models import Group
# Authentication Imports end


# Invite user password
from django.contrib.auth.forms import SetPasswordForm

# Create your views here.



@unauthenticated_user
def LoginPage(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # Find the user by email, ignoring letter casing.
        matching_users = User.objects.filter(email__iexact=email)

        user = None

        # Only authenticate if exactly one account matches.
        if matching_users.count() == 1:
            user_record = matching_users.first()

            user = authenticate(
                request,
                username=user_record.username,
                password=password,
            )

        if user is not None:
            login(request, user)

            current_user = UserModel.objects.get(user=user)

            if not current_user.account_complete:
                return redirect('account:account-setup')

            return redirect('dashboard:today')

        else:
            messages.error(
                request,
                'Email address or password is incorrect.'
            )

    return render(request, "authentication/login.html")



@unauthenticated_user
def LoginPage01(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            user = request.user
            current_user = UserModel.objects.get(user=user)
            if current_user.account_complete == False:
                return redirect('account:account-setup')
            else:
                return redirect('dashboard:today')
        else:
            messages.success(request, '❌ Username or Password is incorrect')

    return render(request, "authentication/login.html")



@unauthenticated_user
def RegisterUser(request):
    form = CreateUserForm()

    if request.method == 'POST' and 'create-account' in request.POST:
        form = CreateUserForm(request.POST)

        if form.is_valid():
            user = form.save()

            first_name = form.cleaned_data['first_name']
            user_email = form.cleaned_data['email']

            UserModel.objects.create(
                user=user,
                first_name=first_name,
                email=user_email,
                agreeTerms=True,
            )

            messages.success(
                request,
                f"Account successfully created for {first_name}."
            )

            return redirect("login")

    context = {
        'form': form,
    }

    return render(
        request,
        "authentication/register.html",
        context
    )


@unauthenticated_user
def RegisterUser01(request):
    form = CreateUserForm()
    if request.method == 'POST' and 'create-account' in request.POST:
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            user_email = form.cleaned_data.get('email')

            UserModel.objects.create(
                user=user,
                first_name=username,
                email=user_email,
                agreeTerms=True,
            )

            messages.success(request, 'Account was created for ' + username)
            return redirect("login")

    context = {
        'form': form
    }
    return render(request, "authentication/register.html", context)


# logout user
def LogoutUser(request):
    logout(request)
    return redirect('login')



def accept_invite(request, token):
    # 1. Find invite safely
    invite = get_object_or_404(UserInvite, token=token)
    user = invite.user

    # 4. Handle form submission
    if request.method == "POST":

        # Create password form with POST data
        form = SetPasswordForm(user, request.POST)

        # Validate passwords
        if form.is_valid():

            # Save password securely
            form.save()

            # Mark invite as used
            invite.is_used = True
            invite.save()

            # create user model
            UserModel.objects.create(
                user=user,
                first_name=invite.user.username,
                email=invite.user.email,
                company=invite.company,
                role=invite.role,
                account_complete=True,
            )

            # Log user in immediately
            login(request, user)

            # Redirect to dashboard
            return redirect('dashboard:today')

        else:
            # Form errors will show in template
            return render(request, "set_password.html", {
                "form": form,
                "invite": invite
            })

    # 5. First-time page load (GET request)
    else:
        form = SetPasswordForm(user)

    context = {
        "form": form,
        "invite": invite
    }

    return render(request, "authentication/set_password.html", context)