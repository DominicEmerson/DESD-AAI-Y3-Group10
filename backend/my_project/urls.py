from django.contrib import admin
from django.urls import path
from .views import login_page

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", login_page, name="login"), 
]