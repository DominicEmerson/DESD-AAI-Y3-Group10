from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from claims.models import CustomUser, Accident, Claim, Vehicle, Driver, Injury
from django import forms
from .forms import SignupForm, CreateUserForm, ForgotPasswordForm, ClaimSubmissionForm
from .models import CustomUser, Accident, Claim, Vehicle, Driver, Injury
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView
from reportlab.pdfgen import canvas
from django.contrib.auth import get_user_model, login, logout
from django.shortcuts import get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils.timezone import localtime
import docker
import requests
import logging
from django.conf import settings

from .models import CustomUser, Accident, Claim, Vehicle, Driver, Injury
from .forms import SignupForm, CreateUserForm, ClaimSubmissionForm, ForgotPasswordForm


User = get_user_model()
logger = logging.getLogger(__name__)

# ------------------------
# Role-Based Pages
# ------------------------
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'
def is_engineer(user):
    return user.is_authenticated and user.role == 'engineer'

def is_finance(user):
    return user.is_authenticated and user.role == 'finance'

def is_enduser(user):
    return user.is_authenticated and user.role == 'enduser'

@never_cache
@login_required
@user_passes_test(is_engineer, login_url='role_redirect')
def engineer_page(request):
    context = {
        'accidents': Accident.objects.all(),
        'claims': Claim.objects.all(),
        'vehicles': Vehicle.objects.all(),
        'drivers': Driver.objects.all(),
        'injuries': Injury.objects.all(),
    }
    return render(request, 'role_pages/engineer.html', context)


# Finance page
@never_cache 
@login_required
@user_passes_test(is_finance, login_url='role_redirect')
def finance_page(request):
    return render(request, 'finance/finance.html')

@login_required
def generate_report(request):
    # Create a PDF in memory
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, "This is a placeholder for the report.")
    p.showPage()
    p.save()
    buffer.seek(0)

    # Return the PDF response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="report.pdf"'
    return response

@login_required
def generate_invoice(request):
    # Create a PDF in memory
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    # Add content to the PDF
    p.drawString(100, 750, "Invoice")
    p.drawString(100, 730, "Item: Insurance")
    p.drawString(100, 710, "Description: Testing Invoice")
    p.drawString(100, 690, "Price: £1000.00")
    # Finalise the PDF
    p.showPage()
    p.save()
    buffer.seek(0)

    # Return the PDF response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="invoice.pdf"'
    return response


@never_cache
@login_required
@user_passes_test(is_enduser, login_url='role_redirect')
def enduser_page(request):
    return render(request, 'role_pages/enduser.html')


@login_required
def role_redirect(request):
    """ Redirect users to the correct page based on their role. """
    user = request.user
    if isinstance(user, CustomUser):
        if user.role == 'admin':
            return redirect('admin_page')
        elif user.role == 'engineer':
            return redirect('engineer_page')
        elif user.role == 'finance':
            return redirect('finance_page')
        else:
            return redirect('claim_dashboard')
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

    return render(request, 'registration/login.html', {'signup_form': signup_form})

def user_logout(request):
    logout(request)

    if request.GET.get('timeout') == '1':
        messages.info(request, "You have been logged out due to inactivity.")
        return redirect('/login/?timeout=1')
    else:
        messages.success(request, "You have been logged out.")
        return redirect('/accounts/login/?logged_out=1')




# ------------------------
# Admin User Management
# ------------------------



@login_required
@user_passes_test(is_admin)
def create_user(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" created successfully!')
            form = CreateUserForm()
        else:
            messages.error(request, "There was an error creating the user.")
    else:
        form = CreateUserForm()

    return render(request, 'admin/create_user.html', {'form': form})

def custom_login(request):
    if request.GET.get('timeout') == '1':
        messages.info(request, "You have been logged out due to inactivity.")
    elif request.GET.get('logged_out') == '1':
        messages.success(request, "You have been logged out.")

    return render(request, 'login.html')


@login_required
@user_passes_test(is_admin)
def create_user(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" created successfully!')
            form = CreateUserForm()  
        else:
            messages.error(request, "There was an error creating the user.")
    else:
        form = CreateUserForm()

    return render(request, 'admin/create_user.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def user_management(request):
    query = request.GET.get('query', '')
    users = User.objects.all()

    if query:
        users = users.filter(email__icontains=query)

    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)

        # Update user role
        if action == 'update_role':
            new_role = request.POST.get('role')
            user.role = new_role
            if new_role == 'admin':
                user.is_staff = True
                user.is_superuser = True
            elif new_role in ['engineer', 'finance']:
                user.is_staff = True
                user.is_superuser = False
            else:
                user.is_staff = False
                user.is_superuser = False

            user.save()
            messages.success(request, f'Role for "{user.username}" updated to "{new_role}".')

        # Reset password
        elif action == 'reset_password':
            new_password = request.POST.get('new_password')
            if new_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, f'Password for "{user.username}" has been reset.')

        # Delete user
        elif action == 'delete_user':
            user.delete()
            messages.success(request, f'User "{user.username}" deleted successfully.')

        return redirect('user_management')

    return render(request, 'admin/user_management.html', {'users': users, 'query': query})



@login_required
@user_passes_test(is_admin)
def container_status_api(request):
    try:
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        containers = client.containers.list(all=True)
        data = []
        for c in containers:
            info   = c.attrs
            state  = info['State']['Status']
            health = info['State'].get('Health', {}).get('Status')
            data.append({
                'name':   c.name,
                'state':  state,
                'health': health
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse(
            {'error': 'Cannot connect to Docker', 'detail': str(e)},
            status=500
        )
@login_required
@user_passes_test(is_admin)
def container_status_page(request):
    # this must match the path under your templates/ directory:
    return render(request, 'admin/system_health.html')


@login_required
@user_passes_test(is_admin)
def container_status_page(request):
    return render(request, 'admin/system_health.html')

@login_required
@user_passes_test(is_admin)
def user_management(request):
    query = request.GET.get('query', '')
    users = User.objects.all()

    if query:
        users = users.filter(email__icontains=query)

    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)

        if action == 'update_role':
            new_role = request.POST.get('role')
            user.role = new_role
            user.is_staff = new_role in ['admin', 'engineer', 'finance']
            user.is_superuser = (new_role == 'admin')
            user.save()
            messages.success(request, f'Role for "{user.username}" updated to "{new_role}".')

        elif action == 'reset_password':
            new_password = request.POST.get('new_password')
            if new_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, f'Password for "{user.username}" has been reset.')

        elif action == 'delete_user':
            user.delete()
            messages.success(request, f'User "{user.username}" deleted successfully.')

        return redirect('user_management')

    return render(request, 'admin/user_management.html', {'users': users, 'query': query})


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

    return render(request, 'registration/forgot_password.html', {'form': form})



@login_required
@user_passes_test(is_admin)
def admin_page(request):
    return render(request, 'admin/admin_page.html')


# ------------------------
# Claims Views (Author: Ahmed Mohamed)
# ------------------------

class ClaimDashboardView(LoginRequiredMixin, ListView):
    model = Claim
    template_name = 'claims/dashboard.html'
    context_object_name = 'claims'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'enduser':
            return Claim.objects.filter(accident__reported_by=user).select_related('accident')
        elif user.role in ['admin', 'finance']:
            return Claim.objects.all().select_related('accident')
        elif user.role == 'engineer':
            return Claim.objects.all().select_related(
                'accident', 'accident__vehicle', 'accident__driver', 'accident__injury'
            )
        return Claim.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context.update({
            'user_role': self.request.user.role,
            'total_claims': qs.count(),
            'pending_claims': qs.filter(settlement_value=0).count(),
            'approved_claims': qs.exclude(settlement_value=0).count(),
        })
        return context


class ClaimSubmissionView(LoginRequiredMixin, CreateView):
    form_class = ClaimSubmissionForm
    template_name = 'claims/claim_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = kwargs.get('form') or self.get_form()
        context.update({
            'accident_form': form.accident_form,
            'vehicle_form': form.vehicle_form,
            'driver_form': form.driver_form,
            'injury_form': form.injury_form,
        })
        return context

    def form_valid(self, form):
        try:
            self.request.session.pop('claim_id', None)
            self.object = form.save(commit=False)
            if self.object.accident:
                self.object.accident.reported_by = self.request.user
                self.object.accident.save()
            self.object.save()
            self.request.session['claim_id'] = self.object.id
            self.request.session.modified = True
            messages.success(self.request, 'Claim submitted successfully!')

            #  call the ML service
            self.request_prediction(self.object)

            return redirect('claim_submission_success')
        except Exception as e:
            messages.error(self.request, f'Error submitting claim: {str(e)}')
            return self.form_invalid(form)

    # Implement a minimal MLaaS API call
    def request_prediction(self, claim):
        """
        Sends claim data to the MLaaS API to get a prediction.
        Updates the claim object's 'prediction_result' field with the response.
        """
        # Check if MLaaS URL is configured
        if not getattr(settings, 'MLAAS_SERVICE_URL', None):
            logger.warning("MLAAS_SERVICE_URL not configured. Skipping prediction.")
            claim.prediction_result = {'error': 'MLaaS not configured'}
            claim.save(update_fields=['prediction_result'])
            return

        # For a simple 3-feature regressor, let's pick any 3 fields from the claim:
        try:
            # fetch related data (accident, vehicle, etc.) if needed
            accident = claim.accident
            driver = Driver.objects.filter(accident=accident).first()

            # If your model expects exactly 3 numeric inputs, just pick 3:
            input_features = [
                float(claim.special_health_expenses or 0),
                float(claim.special_earnings_loss or 0),
                float(driver.driver_age if driver else 0)
            ]

            # The MLaaS expects a JSON payload like this:
            payload = {
                "input_data": [input_features],  # a list of lists
                "algorithm_name": "3feature_regression_model"  # or whatever your ML service expects
            }

            # Construct endpoint URL 
            algorithm_id = getattr(settings, 'DEFAULT_ML_ALGORITHM_ID', 1)
            predict_url = f"{settings.MLAAS_SERVICE_URL.rstrip('/')}/algorithms/{algorithm_id}/predict/"

            logger.info(f"Sending ML prediction request for Claim {claim.id} to {predict_url}")

            response = requests.post(predict_url, json=payload, timeout=10)
            response.raise_for_status()  # Raise an HTTPError if status >= 400

            result_json = response.json()
            claim.prediction_result = result_json
            claim.save(update_fields=['prediction_result'])

            logger.info(f"Claim {claim.id} prediction stored: {result_json}")

        except requests.exceptions.RequestException as ex:
            logger.error(f"ML prediction request failed for Claim {claim.id}: {ex}")
            claim.prediction_result = {'error': str(ex)}
            claim.save(update_fields=['prediction_result'])

        except Exception as ex:
            logger.exception(f"Unexpected error during ML prediction for Claim {claim.id}: {ex}")
            claim.prediction_result = {'error': f'Unexpected: {ex}'}
            claim.save(update_fields=['prediction_result'])


class ClaimPredictionView(LoginRequiredMixin, DetailView):
    model = Claim

    def get(self, request, *args, **kwargs):
        claim = self.get_object()
        return JsonResponse({
            'status': 'pending',
            'message': 'Prediction service not yet available'
        })


class ClaimSuccessView(LoginRequiredMixin, DetailView):
    model = Claim
    template_name = 'claims/claim_success.html'
    context_object_name = 'claim'

    def get_object(self):
        claim_id = self.request.session.get('claim_id')
        if not claim_id:
            return None
        return Claim.objects.select_related('accident').get(id=claim_id)

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('claim_id'):
            return redirect('claim_dashboard')
        return super().dispatch(request, *args, **kwargs)
    


# ------------------------ 
# Session Management
# ------------------------
def session_info(request):
    expiry = request.session.get_expiry_date()
    return JsonResponse({'session_expiry': localtime(expiry).isoformat()})

