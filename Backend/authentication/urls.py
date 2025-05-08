# authentication/urls.py
from django.urls import path  # Import path for URL routing
from django.shortcuts import redirect  # Import redirect for URL redirection
from django.contrib.auth import views as auth_views  # Import authentication views
from . import views  # Import views from the current directory
from django.views.generic import TemplateView  # Import TemplateView for rendering templates

urlpatterns = [
    path('', views.role_redirect, name='home'),  # Redirect to the appropriate role page
    path('redirect/', views.role_redirect, name='role_redirect'),  # Role redirect URL
    path('forgot-password/', views.forgot_password, name='forgot_password'),  # Forgot password URL
    path('accounts/login/', auth_views.LoginView.as_view(template_name='authentication/login.html'), name='login'),  # Login URL
    path('signup/', views.signup, name='signup'),  # Signup URL
    path('logout/', views.user_logout, name='logout'),  # Logout URL
    path('session-info/', views.session_info, name='session_info'),  # Session info URL
    path('gdpr/', views.gdpr, name='gdpr'),  # GDPR notice URL
    path('privacy-policy/', TemplateView.as_view(template_name='authentication/privacy_policy.html'), name='privacy_policy'),  # Privacy policy URL
]