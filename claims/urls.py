# claims/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.role_redirect, name='home'),
    path('engineer/', views.engineer_page, name='engineer_page'),
    path('finance/', views.finance_page, name='finance_page'),
    path('finance/generate_report/', views.generate_report, name='generate_report'),
    path('finance/generate_invoice/', views.generate_invoice, name='generate_invoice'),
    path('enduser/', views.enduser_page, name='enduser_page'),
    path('redirect/', views.role_redirect, name='role_redirect'),
    path('admin-page/', views.admin_page, name='admin_page'),
    path('create-user/', views.create_user, name='create_user'),
    path('user-management/', views.user_management, name='user_management'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),

    # Claims URLs
    # Author: Ahmed Mohamed
    path('dashboard/', views.ClaimDashboardView.as_view(), name='claim_dashboard'),
    path('claim/new/', views.ClaimSubmissionView.as_view(), name='claim_submission'),
    path('claim/success/', views.ClaimSuccessView.as_view(), name='claim_submission_success'),
    path('claim/<int:pk>/prediction/', views.ClaimPredictionView.as_view(), name='claim_prediction'),

    # Auth URLs
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),

]


