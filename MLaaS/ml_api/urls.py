# ml_api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EndpointViewSet, MLAlgorithmViewSet, MLRequestViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'endpoints', EndpointViewSet, basename='endpoint')
router.register(r'algorithms', MLAlgorithmViewSet, basename='mlalgorithm')
router.register(r'requests', MLRequestViewSet, basename='mlrequest')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]