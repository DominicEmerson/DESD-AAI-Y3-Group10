# finance/urls.py
from django.urls import path
from . import views

app_name = 'finance'
urlpatterns = [
    path('', views.finance_page, name='finance_page'),
    path('filter_claims/', views.filter_claims, name='filter_claims'),
]