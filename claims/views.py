from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from claims.models import CustomUser, Accident, Claim, Vehicle, Driver, Injury
from .forms import SignupForm
from django.contrib.auth import login, logout
from django.contrib import messages

# Role-Based Pages
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


@login_required
def finance_page(request):
    return render(request, 'role_pages/finance.html')


@login_required
def enduser_page(request):
    return render(request, 'role_pages/enduser.html')


# Role-Based Redirect After Login
@login_required
def role_redirect(request):
    """ Redirect users to the correct page based on their role. """
    user = request.user
    if user.is_authenticated:  # Ensure the user is authenticated
        if isinstance(user, CustomUser):  # Ensure it's a CustomUser instance
            if user.role == 'engineer':
                return redirect('engineer_page')
            elif user.role == 'finance':
                return redirect('finance_page')
            else:
                return redirect('enduser_page')
    return redirect('login')  # If the user is not authenticated, redirect to login



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
    return redirect('login')