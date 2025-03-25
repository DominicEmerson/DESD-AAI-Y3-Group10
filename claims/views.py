from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from claims.models import CustomUser, Accident, Claim, Vehicle, Driver, Injury
from .forms import SignupForm, CreateUserForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
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
    return render(request, 'admin/admin_page.html')