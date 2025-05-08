# ml_api/urls.py
app_name = 'ml_api'
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EndpointViewSet, MLAlgorithmViewSet, MLRequestViewSet, engineer_list_models, engineer_set_active_model
# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'endpoints', EndpointViewSet, basename='endpoint')
router.register(r'algorithms', MLAlgorithmViewSet, basename='mlalgorithm')
router.register(r'requests', MLRequestViewSet, basename='mlrequest')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('engineer/models/', engineer_list_models, name='engineer_list_models'),
    path('engineer/set_active_model/', engineer_set_active_model, name='engineer_set_active_model'),
    path('', include(router.urls)),
]