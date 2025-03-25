from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from claims.models import CustomUser, Accident, Claim, Vehicle, Driver, Injury
from .forms import SignupForm, CreateUserForm
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.contrib.auth import login, logout
from django.http import JsonResponse
from claims.models import CustomUser, Accident, Claim, Vehicle, Driver, Injury
from .forms import SignupForm, ClaimSubmissionForm


from django import forms
from django.contrib.auth.forms import UserCreationForm
from .forms import ForgotPasswordForm
from .models import CustomUser

User = get_user_model()


# Role-Based Pages
@never_cache 
@login_required
def engineer_page(request):
    # Querying the database for all accidents, claims, vehicles, drivers, and injuries
    accidents = Accident.objects.all()  # Fetch all accidents
    claims = Claim.objects.all()  # Fetch all claims
    vehicles = Vehicle.objects.all()  # Fetch all vehicles
    drivers = Driver.objects.all()  # Fetch all drivers
    injuries = Injury.objects.all()  # Fetch all injuries

    # Pass the data to the template
    context = {
        'accidents': accidents,
        'claims': claims,
        'vehicles': vehicles,
        'drivers': drivers,
        'injuries': injuries,
    }

    return render(request, 'role_pages/engineer.html', context)

@never_cache 
@login_required
def finance_page(request):
    return render(request, 'role_pages/finance.html')

@never_cache
@login_required
def enduser_page(request):
    return render(request, 'role_pages/enduser.html')


@login_required
def role_redirect(request):
    """ Redirect users to the correct page based on their role. """
    user = request.user
    if user.is_authenticated:
        if isinstance(user, CustomUser):
            if user.role == 'admin':
                return redirect('admin_page')  # Redirect admins to the admin page
            elif user.role == 'engineer':
                return redirect('engineer_page')
            elif user.role == 'finance':
                return redirect('finance_page')
            else:
                return redirect('enduser_page')
    return redirect('login')  # Redirect to login if not authenticated




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
    response = redirect('login')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


# Check if user is an admin
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


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


def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # Check if the email exists in the user table
            if User.objects.filter(email=email).exists():
                # Instead of sending an email, just show a success message
                messages.success(request, "An email has been sent to the admin. You will receive an email with steps to reset password shortly.")
            else:
                messages.error(request, "No user with that email exists.")

            return redirect('forgot_password')

    else:
        form = ForgotPasswordForm()

    return render(request, 'registration/forgot_password.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def admin_page(request):
    return render(request, 'admin_page.html')

# Author: Ahmed Mohamed
class ClaimDashboardView(LoginRequiredMixin, ListView):
    """Dashboard view for displaying user's claims."""
    model = Claim
    template_name = 'claims/dashboard.html'
    context_object_name = 'claims'

    def get_queryset(self):
        if self.request.user.role == 'enduser':
            return Claim.objects.filter(accident__reported_by=self.request.user).select_related('accident')
        elif self.request.user.role in ['admin', 'finance']:
            return Claim.objects.all().select_related('accident')
        elif self.request.user.role == 'engineer':
            return Claim.objects.all().select_related('accident', 'accident__vehicle', 'accident__driver', 'accident__injury')
        return Claim.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = self.request.user.role
        qs = self.get_queryset()
        total_claims = qs.count()
        pending_claims = qs.filter(settlement_value=0).count()
        approved_claims = total_claims - pending_claims
        context['total_claims'] = total_claims
        context['pending_claims'] = pending_claims
        context['approved_claims'] = approved_claims
        return context

# Author: Ahmed Mohamed
class ClaimSubmissionView(LoginRequiredMixin, CreateView):
    """View for submitting new claims."""
    form_class = ClaimSubmissionForm
    template_name = 'claims/claim_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = kwargs.get('form') or self.get_form()
        context['accident_form'] = form.accident_form
        context['vehicle_form'] = form.vehicle_form
        context['driver_form'] = form.driver_form
        context['injury_form'] = form.injury_form
        return context

    def form_valid(self, form):
        try:
            # Clear any previous claim_id from the session
            if 'claim_id' in self.request.session:
                del self.request.session['claim_id']

            self.object = form.save(commit=False)
            if self.object.accident:
                self.object.accident.reported_by = self.request.user
                self.object.accident.save()
            self.object.save()
            messages.success(self.request, 'Claim submitted successfully!')
            self.request_prediction(self.object)

            # Store the claim in the session for the success page
            self.request.session['claim_id'] = self.object.id
            # Make sure session is saved
            self.request.session.modified = True

            # Redirect to success page instead of dashboard
            return redirect('claim_submission_success')
        except Exception as e:
            messages.error(self.request, f'Error submitting claim: {str(e)}')
            return self.form_invalid(form)

    def request_prediction(self, claim):
        # Placeholder for future MLaaS integration.
        pass

# Author: Ahmed Mohamed
class ClaimPredictionView(LoginRequiredMixin, DetailView):
    """View for handling MLaaS prediction requests."""
    model = Claim

    def get(self, request, *args, **kwargs):
        claim = self.get_object()
        prediction_data = {
            'status': 'pending',
            'message': 'Prediction service not yet available'
        }
        return JsonResponse(prediction_data)

class ClaimSuccessView(LoginRequiredMixin, DetailView):
    """Display claim submission success page."""
    model = Claim
    template_name = 'claims/claim_success.html'
    context_object_name = 'claim'

    def get_object(self):
        claim_id = self.request.session.get('claim_id')
        if not claim_id:
            # Don't redirect here - get_object must return an object or None
            # Return None will trigger Http404 (which is what we want)
            return None
        return Claim.objects.select_related('accident').get(id=claim_id)

    def dispatch(self, request, *args, **kwargs):
        # Check for claim_id before any processing
        if not request.session.get('claim_id'):
            return redirect('claim_dashboard')
        return super().dispatch(request, *args, **kwargs)
## new commit just cos view was being dodgy!!
    return render(request, 'admin/admin_page.html')