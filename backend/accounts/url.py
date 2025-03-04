# backend/accounts/urls.py
from django.urls import path
from accounts.views import hello_user

urlpatterns = [
    path("hello/", hello_user, name="hello_user"),
]
