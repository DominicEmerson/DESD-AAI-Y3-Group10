from django.contrib import admin
from django.urls import path
from .views import home, hello_world

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("api/hello/", hello_world),
]
