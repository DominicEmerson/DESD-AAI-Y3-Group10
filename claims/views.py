# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth import login, logout
from django.http import JsonResponse
from claims.models import CustomUser, Accident, Claim, Vehicle, Driver, Injury
from .forms import SignupForm, ClaimSubmissionForm

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
    return redirect('claim_dashboard')

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
@user_passes_test(is_admin)  # <-- Only admins can access this page
def admin_page(request):
    return render(request, 'admin_page.html')


# Author: Ahmed Mohamed
class ClaimDashboardView(LoginRequiredMixin, ListView):
    """Dashboard view for displaying user's claims."""
    model = Claim
    template_name = 'claims/dashboard.html'
    context_object_name = 'claims'

    def get_queryset(self):
        """Filter claims based on user role."""
        if self.request.user.role == 'enduser':
            # End users only see claims related to accidents they reported
            return Claim.objects.filter(accident__customuser=self.request.user)
        elif self.request.user.role in ['admin', 'finance']:
            # Admin and finance see all claims
            return Claim.objects.all()
        elif self.request.user.role == 'engineer':
            # Engineers see all claims for analysis
            return Claim.objects.all().select_related('accident', 'accident__vehicle', 'accident__driver', 'accident__injury')
        return Claim.objects.none()

    def get_context_data(self, **kwargs):
        """Add additional context for the dashboard."""
        context = super().get_context_data(**kwargs)
        context['user_role'] = self.request.user.role
        if self.request.user.role == 'engineer':
            # Add extra context for engineers
            context['total_claims'] = self.get_queryset().count()
            context['pending_claims'] = self.get_queryset().filter(settlement_value=0).count()
        return context

# Author: Ahmed Mohamed 
class ClaimSubmissionView(LoginRequiredMixin, CreateView):
    """View for submitting new claims."""
    form_class = ClaimSubmissionForm
    template_name = 'claims/claim_form.html'
    success_url = reverse_lazy('claim_dashboard')

    def get_context_data(self, **kwargs):
        """Add nested forms to the context."""
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['accident_form'] = self.object.accident_form
            context['vehicle_form'] = self.object.vehicle_form
            context['driver_form'] = self.object.driver_form
            context['injury_form'] = self.object.injury_form
        else:
            context['accident_form'] = self.form_class().accident_form
            context['vehicle_form'] = self.form_class().vehicle_form
            context['driver_form'] = self.form_class().driver_form
            context['injury_form'] = self.form_class().injury_form
        return context

    def form_valid(self, form):
        """Process the form submission."""
        try:
            claim = form.save(commit=True)
            messages.success(self.request, 'Claim submitted successfully!')
            
            # Request prediction from MLaaS (will be implemented when service is ready)
            self.request_prediction(claim)
            
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Error submitting claim: {str(e)}')
            return self.form_invalid(form)

    def request_prediction(self, claim):
        """
        Placeholder method for requesting prediction from MLaaS.
        Will be implemented when MLaaS service is ready.
        """
        pass

# Author: Ahmed Mohamed
class ClaimPredictionView(LoginRequiredMixin, DetailView):
    """View for handling MLaaS prediction requests."""
    model = Claim
    
    def get(self, request, *args, **kwargs):
        """Get prediction for a specific claim."""
        claim = self.get_object()
        # Placeholder for MLaaS integration
        # This will be replaced with actual API call when MLaaS is ready
        prediction_data = {
            'status': 'pending',
            'message': 'Prediction service not yet available'
        }
        return JsonResponse(prediction_data)