from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse

from .models import CustomUser, Accident, Claim, Vehicle, Driver, Injury
from .forms import SignupForm, CreateUserForm, ClaimSubmissionForm, ForgotPasswordForm

User = get_user_model()

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


@never_cache
@login_required
@user_passes_test(is_finance, login_url='role_redirect')
def finance_page(request):
    return render(request, 'role_pages/finance.html')


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
            return redirect('enduser_page')
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
    response = redirect('login')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


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
                # FIXED QUOTE HERE:
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
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exists():
                messages.success(
                    request,
                    "An email has been sent to the admin. You will receive an email with steps to reset password shortly."
                )
            else:
                messages.error(request, "No user with that email exists.")
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
            self.request_prediction(self.object)
            return redirect('claim_submission_success')
        except Exception as e:
            messages.error(self.request, f'Error submitting claim: {str(e)}')
            return self.form_invalid(form)

    def request_prediction(self, claim):
        # ML integration placeholder
        pass


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

