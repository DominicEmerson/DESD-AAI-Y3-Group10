# insurance_ai/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('claims.urls')),  # include all URLs from your claims app
]
