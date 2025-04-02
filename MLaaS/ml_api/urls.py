from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EndpointViewSet, MLAlgorithmViewSet, MLRequestViewSet

router = DefaultRouter()
router.register(r'endpoints', EndpointViewSet)
router.register(r'algorithms', MLAlgorithmViewSet)
router.register(r'requests', MLRequestViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
