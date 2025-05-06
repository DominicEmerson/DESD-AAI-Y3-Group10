from .forms import SignupForm, ForgotPasswordForm  # Import forms for signup and password reset
from authentication.models import CustomUser  # Import the custom user model
from django.contrib import messages  # Import messages framework for user feedback
from django.contrib.auth import get_user_model, login, logout  # Import authentication functions
from django.contrib.auth.decorators import login_required  # Import login required decorator
from django.http import JsonResponse  # Import JsonResponse for API responses
from django.shortcuts import render, redirect  # Import render and redirect functions
from django.utils.timezone import localtime  # Import localtime for timezone handling
import logging  # Import logging for logging events

User = get_user_model()  # Get the user model
logger = logging.getLogger(__name__)  # Set up logging for this module

@login_required
def role_redirect(request):
    """Redirect users to the correct page based on their role."""
    user = request.user  # Get the logged-in user
    if isinstance(user, CustomUser):  # Check if the user is an instance of CustomUser
        if user.role == 'admin':
            return redirect('sysadmin:admin_page')  # Redirect to the admin page
        elif user.role == 'engineer':
            return redirect('engineer:engineer_page')  # Redirect to the engineer page
        elif user.role == 'finance':
            return redirect('finance:finance_page')  # Redirect to the finance page
        elif user.role == 'enduser':
            return redirect('claims:claim_dashboard')  # Redirect to the claims dashboard
        else:
            return redirect('login')  # Redirect to login if the role is unknown
    return redirect('login')  # Redirect to login if the user is not a CustomUser

def signup(request):
    """Handles user signup."""
    if request.method == 'POST':  # Check if the request method is POST
        signup_form = SignupForm(request.POST)  # Get form data from the request
        if signup_form.is_valid():  # Check if the form is valid
            user = signup_form.save()  # Save the new user
            login(request, user)  # Log the user in
            messages.success(request, "Account successfully created! You're logged in.")  # Success message
            return redirect('role_redirect')  # Redirect to role redirect
    else:
        signup_form = SignupForm()  # Create a new form instance for GET requests

    return render(request, 'authentication/login.html', {'signup_form': signup_form})  # Render the signup form

def user_logout(request):
    """Handles user logout."""
    logout(request)  # Log the user out

    if request.GET.get('timeout') == '1':  # Check if the logout was due to timeout
        messages.info(request, "You have been logged out due to inactivity.")  # Message for timeout logout
        return redirect('/login/?timeout=1')  # Redirect to login with timeout parameter
    else:
        messages.success(request, "You have been logged out.")  # Success message for logout
        return redirect('/accounts/login/?logged_out=1')  # Redirect to login with logged out parameter

def forgot_password(request):
    """Handles password reset requests."""
    if request.method == 'POST':  # Check if the request method is POST
        form = ForgotPasswordForm(request.POST)  # Get form data from the request
        if form.is_valid():  # Check if the form is valid
            messages.success(
                request,
                "An email has been sent to the admin. You will receive an email with steps to reset password shortly."  # Success message
            )
            return redirect('forgot_password')  # Redirect to forgot password page
    else:
        form = ForgotPasswordForm()  # Create a new form instance for GET requests

    return render(request, 'authentication/forgot_password.html', {'form': form})  # Render the forgot password form

# ------------------------ 
# Session Management
# ------------------------
def session_info(request):
    """Returns session expiry information as JSON."""
    expiry = request.session.get_expiry_date()  # Get session expiry date
    return JsonResponse({'session_expiry': localtime(expiry).isoformat()})  # Return expiry date as JSON

def gdpr(request):
    """Renders the GDPR notice page."""
    return render(request, 'authentication/gdpr.html')  # Render the GDPR notice page