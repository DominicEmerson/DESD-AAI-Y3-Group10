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
from django.contrib import admin  # Import Django admin
from django.urls import path, include  # Import path and include for URL routing
from django.conf import settings  # Import settings for configuration
from django.conf.urls.static import static  # Import static for serving static files

urlpatterns = [
    # path('admin/containers/',     container_status_page, name='container_status_page'),
    # path('admin/api/containers/', container_status_api,  name='container_status_api'),
    path('admin/', admin.site.urls),  # Admin site URL
    path('', include('authentication.urls')),  # Include URLs from the authentication app
    path('claims/', include('claims.urls')),  # Include URLs from the claims app
    path('engineer/', include('engineer.urls')),  # Include URLs from the engineer app
    path('finance/', include('finance.urls')),  # Include URLs from the finance app
    path('sysadmin/', include('sysadmin.urls')),  # Include URLs from the sysadmin app
    path('health/', include('health_check.urls')),  # Include health check URLs
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])  # Serve static files in development