# engineer/urls.py
from django.urls import path
from . import views

app_name = 'engineer'
urlpatterns = [
    path('', views.engineer_page, name='engineer_page'),
]