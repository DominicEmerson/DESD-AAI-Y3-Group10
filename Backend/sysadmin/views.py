from .forms import CreateUserForm
from authentication.models import CustomUser
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
import docker
import logging
import utils

User = get_user_model()  # Get the user model
logger = logging.getLogger(__name__)  # Set up logging

@login_required
@user_passes_test(utils.is_admin)
def admin_page(request):
    """Renders the admin dashboard page."""
    return render(request, 'sysadmin/admin_page.html')  # Render admin page

# ------------------------
# Admin User Management
# ------------------------
@login_required
@user_passes_test(utils.is_admin)
def create_user(request):
    """Handles the creation of a new user."""
    if request.method == 'POST':
        form = CreateUserForm(request.POST)  # Get form data
        if form.is_valid():  # Check if form is valid
            user = form.save()  # Save the new user
            messages.success(request, f'User "{user.username}" created successfully!')  # Success message
            form = CreateUserForm()  # Reset form for new user creation
        else:
            messages.error(request, "There was an error creating the user.")  # Error message
    else:
        form = CreateUserForm()  # Create a new form instance

    return render(request, 'sysadmin/create_user.html', {'form': form})  # Render user creation form

@login_required
@user_passes_test(utils.is_admin)
def user_management(request):
    """Handles user management, including searching and updating user roles."""
    query = request.GET.get('query', '')  # Get search query
    users = User.objects.all()  # Get all users

    if query:  # If a query is provided
        users = users.filter(email__icontains=query)  # Filter users by email

    if request.method == 'POST':
        action = request.POST.get('action')  # Get action from form
        user_id = request.POST.get('user_id')  # Get user ID from form
        user = get_object_or_404(User, id=user_id)  # Get user object or return 404

        if action == 'update_role':  # If action is to update role
            first_name = request.POST.get('first_name', '').strip()  # Get first name
            last_name = request.POST.get('last_name', '').strip()  # Get last name
            new_role = request.POST.get('role')  # Get new role

            user.first_name = first_name  # Update first name
            user.last_name = last_name  # Update last name
            user.role = new_role  # Update user role
            if new_role == 'admin':
                user.is_staff = True  # Set staff status for admin
                user.is_superuser = True  # Set superuser status for admin
            elif new_role in ['engineer', 'finance']:
                user.is_staff = True  # Set staff status for engineer/finance
                user.is_superuser = False  # Not a superuser
            else:
                user.is_staff = False  # Not a staff member
                user.is_superuser = False  # Not a superuser

            user.save()  # Save user changes
            messages.success(
                request,
                f'Updated "{user.username}": '
                f'name set to {first_name} {last_name}, '
                f'role set to {new_role}.'  # Success message for user update
            )

        elif action == 'reset_password':  # If action is to reset password
            new_password = request.POST.get('new_password')  # Get new password
            if new_password:  # If new password is provided
                user.set_password(new_password)  # Set new password
                user.save()  # Save user changes
                messages.success(
                    request,
                    f'Password for "{user.username}" has been reset.'  # Success message for password reset
                )

        elif action == 'delete_user':  # If action is to delete user
            user.delete()  # Delete user
            messages.success(
                request,
                f'User "{user.username}" deleted successfully.'  # Success message for user deletion
            )

        return redirect('sysadmin:user_management')  # Redirect to user management page

    return render(
        request,
        'sysadmin/user_management.html',
        {'users': users, 'query': query}  # Render user management page with users and query
    )

@login_required
@user_passes_test(utils.is_admin)
def container_status_api(request):
    """
    Provides a JSON response with the status of Docker containers.
    """
    try:
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')  # Connect to Docker
        containers = client.containers.list(all=True)  # Get all containers
        data = []  # Initialise list for container data
        for c in containers:
            info = c.attrs  # Get container attributes
            state = info['State']['Status']  # Get container state
            health = info['State'].get('Health', {}).get('Status')  # Get container health status
            data.append({
                'name': c.name,  # Container name
                'state': state,  # Container state
                'health': health  # Container health status
            })
        return JsonResponse(data, safe=False)  # Return container data as JSON
    except Exception as e:
        return JsonResponse(
            {'error': 'Cannot connect to Docker', 'detail': str(e)},  # Return error message
            status=500  # Internal server error status
        )