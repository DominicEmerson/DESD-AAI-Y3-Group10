from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from claims.models import CustomUser  # Import your custom user model

# Role-Based Pages
@login_required
def engineer_page(request):
    return render(request, 'role_pages/engineer.html')

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
