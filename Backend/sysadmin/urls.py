# sysadmin/urls.py
from django.urls import path, include
from django.views.generic import TemplateView
from . import views

app_name = 'sysadmin'

urlpatterns = [
    path('', views.admin_page, name='admin_page'),
    path('create-user/', views.create_user, name='create_user'),
    path('user-management/', views.user_management, name='user_management'),

    # HTML page with your traffic‐light UI
    path(
        'system-health/',
        TemplateView.as_view(template_name='sysadmin/system_health.html'),
        name='system_health'
    ),

    # JSON API endpoint for django‐health‐check
    path(
        'system-health/api/',
        include(
            ('health_check.urls', 'health_check'),
            namespace='health_check'
        )
    ),
]
