"""
URL configuration for insurance_ai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# from claims.views import container_status_page, container_status_api

urlpatterns = [
    # path('admin/containers/',     container_status_page, name='container_status_page'),
    # path('admin/api/containers/', container_status_api,  name='container_status_api'),
    path('admin/', admin.site.urls),
    path('', include('authentication.urls')),
    path('claims/', include('claims.urls')),
    path('engineer/', include('engineer.urls')),
    path('finance/', include('finance.urls')),
    path('sysadmin/', include('sysadmin.urls')),
]