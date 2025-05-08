# claims/urls.py
from django.urls import path  # Import path for URL routing
from . import views  # Import views from the current directory

app_name = 'claims'  # Namespace for the claims app
urlpatterns = [
    # Claims URLs
    # Author: Ahmed Mohamed
    path('', views.ClaimDashboardView.as_view(), name='claim_dashboard'),  # Dashboard view
    path('new/', views.ClaimSubmissionView.as_view(), name='claim_submission'),  # Claim submission view
    path('success/', views.ClaimSuccessView.as_view(), name='claim_submission_success'),  # Claim success view
    path('<int:pk>/prediction/', views.ClaimPredictionView.as_view(), name='claim_prediction'),  # Prediction view
    path('details/<int:claim_id>/', views.claim_detail, name='claim_detail'),  # Claim detail view
]