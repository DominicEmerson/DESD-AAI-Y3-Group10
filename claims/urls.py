# claims/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.role_redirect, name='home'),
    path('engineer/', views.engineer_page, name='engineer_page'),
    path('finance/', views.finance_page, name='finance_page'),
    path('enduser/', views.enduser_page, name='enduser_page'),
    path('redirect/', views.role_redirect, name='role_redirect'),
    path('admin-page/', views.admin_page, name='admin_page'),

    # Auth URLs
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
]

