# engineer/urls.py
"""
URL config for engineer app: dashboard, model upload, retraining trigger.
"""
from django.urls import path
from . import views # Import views from the current directory
from .views import swap_active_model

app_name = 'engineer' # Namespace for URLs

urlpatterns = [
    # Main dashboard page (GET request displays, POST handled by upload_model)
    path(
        '', # Root URL for the engineer section
        views.engineer_page,
        name='engineer_page'
    ),
    # Separate URL specifically for handling the POST request from the upload form
    path(
        'upload_model/',
        views.upload_model,
        name='upload_model' # Name used in the form's action attribute
    ),
    # URL for triggering retraining via POST request
    path(
        'retrain_model/<int:algorithm_id>/', # Takes algorithm ID as parameter
        views.trigger_retrain,
        name='trigger_retrain' # Name used in the retrain button form's action
    ),
    # Removed or commented out the predict_claim_for_engineer URL unless needed
    # path('predict/<int:claim_id>/', views.predict_claim_for_engineer, name='predict_engineer_claim'),
    path('swap_active_model/', swap_active_model, name='swap_active_model'),
]