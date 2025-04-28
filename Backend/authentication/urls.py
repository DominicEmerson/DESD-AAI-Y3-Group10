# authentication/urls.py
from django.urls import path
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.role_redirect, name='home'),
    path('redirect/', views.role_redirect, name='role_redirect'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='authentication/login.html'), name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('session-info/', views.session_info, name='session_info'),
]