# finance/urls.py
from django.urls import path  # Import path for URL routing
from . import views  # Import views from the current directory

app_name = 'finance'  # Namespace for the finance app
urlpatterns = [
    path('', views.finance_page, name='finance_page'),  # Finance dashboard view
    path('filter_claims/', views.filter_claims, name='filter_claims'),  # Claims filtering view
]