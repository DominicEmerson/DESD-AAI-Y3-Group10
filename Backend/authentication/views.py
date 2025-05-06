from .forms import SignupForm, ForgotPasswordForm
from authentication.models import CustomUser
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.timezone import localtime
import logging
from django.conf import settings
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV3
import requests


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


def validate_recaptcha(token):
    """ Validates the reCAPTCHA token with Google's API. """
    secret_key = settings.RECAPTCHA_PRIVATE_KEY
    response = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={'secret': secret_key, 'response': token}
    )
    result = response.json()
    return result.get('success', False)

def signup(request):
    """ Handles user signup, including reCAPTCHA validation. """
    if request.method == 'POST':
        signup_form = SignupForm(request.POST)
        captcha_response = request.POST.get('g-recaptcha-response')
        
        # Check if the reCAPTCHA token is received
        if not captcha_response:
            messages.error(request, "Please complete the reCAPTCHA verification.")
            return render(request, 'authentication/login.html', {
                'signup_form': signup_form,
                'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
            })
        
        # Validate the reCAPTCHA token
        if not validate_recaptcha(captcha_response):
            messages.error(request, "reCAPTCHA validation failed. Please try again.")
            return render(request, 'authentication/login.html', {
                'signup_form': signup_form,
                'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
            })
        
        # Continue with signup processing if validation is successful
        if signup_form.is_valid():
            user = signup_form.save()
            login(request, user)
            messages.success(request, "Account successfully created! You're logged in.")
            return redirect('role_redirect')
        else:
            messages.error(request, "There were errors in the signup form.")
            return render(request, 'authentication/login.html', {
                'signup_form': signup_form,
                'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
            })
    else:
        # Clear any previous error messages on GET request
        signup_form = SignupForm()

    return render(request, 'authentication/login.html', {
        'signup_form': signup_form,
        'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
    })


def user_logout(request):
    logout(request)

    if request.GET.get('timeout') == '1':
        messages.info(request, "You have been logged out due to inactivity.")
        return redirect('/login/?timeout=1')
    else:
        messages.success(request, "You have been logged out.")
        return redirect('/accounts/login/?logged_out=1')

def forgot_password(request):
    """ Handles forgot password requests, including reCAPTCHA validation. """
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        captcha_response = request.POST.get('g-recaptcha-response')
        
        # Check if the reCAPTCHA token is received
        if not captcha_response:
            messages.error(request, "Please complete the reCAPTCHA verification.")
            return render(request, 'authentication/forgot_password.html', {
                'form': form,
                'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
            })
        
        # Validate the reCAPTCHA token
        if not validate_recaptcha(captcha_response):
            messages.error(request, "reCAPTCHA validation failed. Please try again.")
            return render(request, 'authentication/forgot_password.html', {
                'form': form,
                'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
            })
        
        # Continue with forgot password processing if validation is successful
        if form.is_valid():
            # Logic to send reset password email
            messages.success(request, "An email has been sent to reset your password.")
            return redirect('forgot_password')
        else:
            messages.error(request, "There were errors in the forgot password form.")
            return render(request, 'authentication/forgot_password.html', {
                'form': form,
                'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
            })
    else:
        # Clear any previous error messages on GET request
        form = ForgotPasswordForm()

    return render(request, 'authentication/forgot_password.html', {
        'form': form,
        'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
    })

# ------------------------ 
# Session Management
# ------------------------
def session_info(request):
    expiry = request.session.get_expiry_date()
    return JsonResponse({'session_expiry': localtime(expiry).isoformat()})


def gdpr(request):
    return render(request, 'authentication/gdpr.html')

def custom_login(request):
    """ Custom login view that handles reCAPTCHA validation. """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        captcha_response = request.POST.get('g-recaptcha-response')
        
        if not captcha_response:
            messages.error(request, "Please complete the reCAPTCHA verification.")
            return render(request, 'authentication/login.html', {
                'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
            })
        
        # Verify reCAPTCHA
        recaptcha_field = ReCaptchaField(
            widget=ReCaptchaV3(
                attrs={
                    'required_score': 0.5,
                    'action': 'login'
                }
            )
        )
        
        try:
            recaptcha_field.clean(captcha_response)
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('role_redirect')
            else:
                messages.error(request, "Invalid username or password.")
        except Exception as e:
            logger.error(f"reCAPTCHA validation failed: {str(e)}")
            messages.error(request, "reCAPTCHA validation failed. Please try again.")
    
    return render(request, 'authentication/login.html', {
        'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
    })