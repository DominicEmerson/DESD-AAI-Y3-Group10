# ml_api/urls.py
app_name = 'ml_api'  # Namespace for the ml_api app
from django.urls import path, include  # Import path and include for URL routing
from rest_framework.routers import DefaultRouter  # Import DefaultRouter for API routing
from .views import EndpointViewSet, MLAlgorithmViewSet, MLRequestViewSet  # Import viewsets

# Create a router and register our viewsets with it.
router = DefaultRouter()  # Create a router instance
router.register(r'endpoints', EndpointViewSet, basename='endpoint')  # Register endpoint viewset
router.register(r'algorithms', MLAlgorithmViewSet, basename='mlalgorithm')  # Register algorithm viewset
router.register(r'requests', MLRequestViewSet, basename='mlrequest')  # Register request viewset

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),  # Include router URLs
]