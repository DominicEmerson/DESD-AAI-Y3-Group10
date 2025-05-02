# claims/urls.py
from django.urls import path
from . import views

app_name = 'claims'
urlpatterns = [
    # Claims URLs
    # Author: Ahmed Mohamed
    path('', views.ClaimDashboardView.as_view(), name='claim_dashboard'),
    path('new/', views.ClaimSubmissionView.as_view(), name='claim_submission'),
    path('success/', views.ClaimSuccessView.as_view(), name='claim_submission_success'),
    path('<int:pk>/prediction/', views.ClaimPredictionView.as_view(), name='claim_prediction'),
    path('details/<int:claim_id>/', views.claim_detail, name='claim_detail'),
]