# sysadmin/urls.py
from django.urls import path, include  # Import path and include for URL routing
from django.views.generic import TemplateView  # Import TemplateView for rendering templates
from . import views  # Import views from the current directory

app_name = 'sysadmin'  # Namespace for the sysadmin app

urlpatterns = [
    path('', views.admin_page, name='admin_page'),  # Admin dashboard view
    path('create-user/', views.create_user, name='create_user'),  # User creation view
    path('user-management/', views.user_management, name='user_management'),  # User management view



    # JSON API endpoint for django-health-check
    path(
        'system-health/api/',
        include(
            ('health_check.urls', 'health_check'),  # Include health check URLs
            namespace='health_check'
        )
    ),
]