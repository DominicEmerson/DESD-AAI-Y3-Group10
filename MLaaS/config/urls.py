from django.contrib import admin  # Import Django admin
from django.urls import path, include  # Import path and include for URL routing
from django.conf import settings  # Import settings for configuration
from django.conf.urls.static import static  # Import static for serving static files

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin site URL
    path('api/', include('ml_api.urls')),  # Include URLs from the ml_api app
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Serve media files in development
