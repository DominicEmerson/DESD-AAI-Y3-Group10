from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views  # Import the login view
from claims import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.role_redirect, name='home'),
    path('engineer/', views.engineer_page, name='engineer_page'),
    path('finance/', views.finance_page, name='finance_page'),
    path('enduser/', views.enduser_page, name='enduser_page'),
    path('redirect/', views.role_redirect, name='role_redirect'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),  # Add this line
    path('claims/', include('claims.urls')),  # Include the claims app URLs here
]

