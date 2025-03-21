from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from claims.models import CustomUser, Accident, Claim, Vehicle, Driver, Injury
from .forms import SignupForm, CreateUserForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

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

# Finance page
@never_cache 
@login_required
def finance_page(request):
    return render(request, 'finance/finance.html')

# Generating and then exporting finance reports
@login_required
def generate_report(request):
    # Render the report generation template
    return render(request, 'finance/generate_report.html')

# Generating finance invoices
@login_required
def generate_invoice(request):
    # Render the invoice generation template
    return render(request, 'finance/generate_invoice.html')

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
def admin_page(request):
    return render(request, 'admin/admin_page.html')