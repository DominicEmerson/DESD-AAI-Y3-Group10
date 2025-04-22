from django.contrib import admin
from django.urls import path, include
from claims.views import container_status_page, container_status_api

urlpatterns = [
    path('admin/containers/',     container_status_page, name='container_status_page'),
    path('admin/api/containers/', container_status_api,  name='container_status_api'),
    path('admin/', admin.site.urls),
    path('', include('claims.urls')),
]
