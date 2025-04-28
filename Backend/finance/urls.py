# finance/urls.py
from django.urls import path
from . import views

app_name = 'finance'
urlpatterns = [
    path('', views.finance_page, name='finance_page'),
    path('generate_report/', views.generate_report, name='generate_report'),
    path('generate_invoice/', views.generate_invoice, name='generate_invoice'),
]