from .forms import SignupForm, ForgotPasswordForm
from authentication.models import CustomUser
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.timezone import localtime
import logging


User = get_user_model()
logger = logging.getLogger(__name__)

@login_required
def role_redirect(request):
    """ Redirect users to the correct page based on their role. """
    user = request.user
    if isinstance(user, CustomUser):
        if user.role == 'admin':
            #return redirect('admin_page')
            return redirect('sysadmin:admin_page')
        elif user.role == 'engineer':
            #return redirect('engineer_page')
            return redirect('engineer:engineer_page')
        elif user.role == 'finance':
            #return redirect('finance_page')
            return redirect('finance:finance_page')
        elif user.role == 'enduser':
            # return redirect('claim_dashboard')
            return redirect('claims:claim_dashboard')
        else:
            return redirect('login') ## should add error page here to handle unknown roles
    return redirect('login')


def signup(request):
    if request.method == 'POST':
        signup_form = SignupForm(request.POST)
        if signup_form.is_valid():
            user = signup_form.save()
            login(request, user)
            messages.success(request, "Account successfully created! You're logged in.")
            return redirect('role_redirect')
    else:
        signup_form = SignupForm()

    return render(request, 'authentication/login.html', {'signup_form': signup_form})


def user_logout(request):
    logout(request)

    if request.GET.get('timeout') == '1':
        messages.info(request, "You have been logged out due to inactivity.")
        return redirect('/login/?timeout=1')
    else:
        messages.success(request, "You have been logged out.")
        return redirect('/accounts/login/?logged_out=1')

def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            messages.success(
                request,
                "An email has been sent to the admin. You will receive an email with steps to reset password shortly."
            )
            return redirect('forgot_password')
    else:
        form = ForgotPasswordForm()

    return render(request, 'authentication/forgot_password.html', {'form': form})

# ------------------------ 
# Session Management
# ------------------------
def session_info(request):
    expiry = request.session.get_expiry_date()
    return JsonResponse({'session_expiry': localtime(expiry).isoformat()})