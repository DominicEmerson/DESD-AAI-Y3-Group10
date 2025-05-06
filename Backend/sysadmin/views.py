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

User = get_user_model()
logger = logging.getLogger(__name__)

@login_required
@user_passes_test(utils.is_admin)
def admin_page(request):
    return render(request, 'sysadmin/admin_page.html')

# ------------------------
# Admin User Management
# ------------------------
@login_required
@user_passes_test(utils.is_admin)
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

    return render(request, 'sysadmin/create_user.html', {'form': form})

@login_required
@user_passes_test(utils.is_admin)
def user_management(request):
    query = request.GET.get('query', '')
    users = User.objects.all()

    if query:
        users = users.filter(email__icontains=query)

    if request.method == 'POST':
        action  = request.POST.get('action')
        user_id = request.POST.get('user_id')
        user    = get_object_or_404(User, id=user_id)

        if action == 'update_role':

            first_name = request.POST.get('first_name', '').strip()
            last_name  = request.POST.get('last_name',  '').strip()
            new_role   = request.POST.get('role')

            user.first_name = first_name
            user.last_name  = last_name
            user.role       = new_role
            if new_role == 'admin':
                user.is_staff     = True
                user.is_superuser = True
            elif new_role in ['engineer', 'finance']:
                user.is_staff     = True
                user.is_superuser = False
            else:
                user.is_staff     = False
                user.is_superuser = False


            user.save()
            messages.success(
                request,
                f'Updated "{user.username}": '
                f'name set to {first_name} {last_name}, '
                f'role set to {new_role}.'
            )

        elif action == 'reset_password':
            new_password = request.POST.get('new_password')
            if new_password:
                user.set_password(new_password)
                user.save()
                messages.success(
                    request,
                    f'Password for "{user.username}" has been reset.'
                )

        elif action == 'delete_user':
            user.delete()
            messages.success(
                request,
                f'User "{user.username}" deleted successfully.'
            )

        return redirect('sysadmin:user_management')

    return render(
        request,
        'sysadmin/user_management.html',
        {'users': users, 'query': query}
    )

@login_required
@user_passes_test(utils.is_admin)
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