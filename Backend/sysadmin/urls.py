# sysadmin/urls.py
from django.urls import path
from . import views

app_name = 'sysadmin'
urlpatterns = [
    path('', views.admin_page, name='admin_page'),
    path('create-user/', views.create_user, name='create_user'),
    path('user-management/', views.user_management, name='user_management'),
    path('system-health/', views.container_status_api, name='system_health'),
    
]