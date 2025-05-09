from .forms import ClaimSubmissionForm
from claims.models import Accident, Claim, Vehicle, Driver, Injury
from authentication.models import CustomUser
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.generic import ListView, CreateView, DetailView
from django.views.decorators.http import require_http_methods
import logging
import requests
from utils.ml_service_utils import get_active_insurance_model_id
from utils.preprocessing import preprocess_single_claim_for_prediction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import ClaimExportSerializer

User = get_user_model()  # Get the user model
logger = logging.getLogger(__name__)  # Set up logging

# ------------------------
# Claims Views (Author: Ahmed Mohamed)
# ------------------------

class ClaimDashboardView(LoginRequiredMixin, ListView):
    """
    View for displaying the claims dashboard.

    This view lists all claims associated with the logged-in user,
    with pagination support. The displayed claims vary based on user role.
    """
    model = Claim  # Model to use for the view
    template_name = 'claims/dashboard.html'  # Template for rendering the view
    context_object_name = 'claims'  # Context variable name for claims
    paginate_by = 10  # Number of claims to display per page

    def get_queryset(self):
        """Returns a queryset of claims based on user role."""
        user = self.request.user  # Get the logged-in user
        if user.role == 'enduser':
            # Order by newest first for endusers
            return Claim.objects.filter(accident__reported_by=user).select_related('accident').order_by('-id')
        elif user.role in ['admin', 'finance']:
            return Claim.objects.all().select_related('accident').order_by('-id')
        elif user.role == 'engineer':
            return Claim.objects.all().select_related(
                'accident', 'accident__vehicle', 'accident__driver', 'accident__injury'
            ).order_by('-id')
        return Claim.objects.none()

    def get_context_data(self, **kwargs):
        """Adds additional context data to the template."""
        context = super().get_context_data(**kwargs)  # Get existing context
        qs = self.get_queryset()  # Get the queryset
        context.update({
            'user_role': self.request.user.role,  # Add user role to context
            'total_claims': qs.count(),  # Total number of claims
            'pending_claims': qs.filter(settlement_value=0).count(),  # Count of pending claims
            'approved_claims': qs.exclude(settlement_value=0).count(),  # Count of approved claims
        })
        return context

class ClaimSubmissionView(LoginRequiredMixin, CreateView):
    """
    View for submitting a new claim.

    This view handles the creation of a new claim and its associated data.
    """
    form_class = ClaimSubmissionForm  # Form class for claim submission
    template_name = 'claims/claim_form.html'  # Template for rendering the form

    def get_context_data(self, **kwargs):
        """Adds accident, vehicle, driver, and injury forms to the context."""
        context = super().get_context_data(**kwargs)  # Get existing context
        form = kwargs.get('form') or self.get_form()  # Get the form
        context.update({
            'accident_form': form.accident_form,  # Add accident form to context
            'vehicle_form': form.vehicle_form,  # Add vehicle form to context
            'driver_form': form.driver_form,  # Add driver form to context
            'injury_form': form.injury_form,  # Add injury form to context
        })
        return context

    def form_valid(self, form):
        """Handles valid form submission."""
        try:
            self.request.session.pop('claim_id', None)  # Clear previous claim ID from session
            self.object = form.save(commit=False)  # Save the form but do not commit to the database yet
            if self.object.accident:
                self.object.accident.reported_by = self.request.user  # Set the user who reported the accident
                self.object.accident.save()  # Save the accident
            self.object.save()  # Save the claim
            self.request.session['claim_id'] = self.object.id  # Store claim ID in session
            self.request.session.modified = True  # Mark session as modified
            messages.success(self.request, 'Claim submitted successfully!')  # Success message

            # Call the ML service for prediction
            self.request_prediction(self.object)  # Request prediction for the claim

            return redirect('claims:claim_submission_success')  # Redirect to success page
        except Exception as e:
            messages.error(self.request, f'Error submitting claim: {str(e)}')  # Error message
            return self.form_invalid(form)  # Return invalid form

    def request_prediction(self, claim):
        """
        Sends claim data to the MLaaS API to get a prediction.
        Updates the claim object's 'prediction_result' field with the response.
        """
        if not getattr(settings, 'MLAAS_SERVICE_URL', None):
            logger.warning("MLAAS_SERVICE_URL not configured. Skipping prediction.")
            claim.prediction_result = {'error': 'MLaaS not configured'}  # Set error in prediction result
            claim.save(update_fields=['prediction_result'])  # Save the claim
            return
        try:
            accident = claim.accident
            driver = Driver.objects.filter(accident=accident).first()
            vehicle = Vehicle.objects.filter(accident=accident).first()
            injury = Injury.objects.filter(accident=accident).first()
            # Use new preprocessing function to get 18 features
            input_features = preprocess_single_claim_for_prediction(
                claim_instance=claim,
                driver_instance=driver,
                accident_instance=accident,
                vehicle_instance=vehicle,
                injury_instance=injury
            )
            payload = {"input_data": [input_features]}
            algorithm_id = get_active_insurance_model_id()

            if not algorithm_id:
                logger.error(f"Could not determine active ML algorithm for Claim {claim.id}. Prediction skipped.")
                claim.prediction_result = {'error': 'MLaaS: Could not determine active model ID for prediction.'}
                claim.save(update_fields=['prediction_result'])
                return

            predict_url = f"{settings.MLAAS_SERVICE_URL.rstrip('/')}/algorithms/{algorithm_id}/predict/"
            logger.info(f"Sending ML prediction request for Claim {claim.id} to {predict_url} (using active model ID: {algorithm_id})")
            response = requests.post(predict_url, json=payload, timeout=10)
            response.raise_for_status()
            result_json = response.json()
            claim.prediction_result = result_json
            claim.save(update_fields=['prediction_result'])
            logger.info(f"Claim {claim.id} prediction stored: {result_json}")
        except requests.exceptions.RequestException as ex:
            logger.error(f"ML prediction request failed for Claim {claim.id}: {ex}")
            claim.prediction_result = {'error': str(ex)}
            claim.save(update_fields=['prediction_result'])
        except Exception as ex:
            logger.exception(f"Unexpected error during ML prediction for Claim {claim.id}")
            claim.prediction_result = {'error': f'Unexpected error during prediction: {ex}'}
            claim.save(update_fields=['prediction_result'])

class ClaimPredictionView(LoginRequiredMixin, DetailView):
    """
    View for retrieving predictions for a specific claim.

    This view checks if a prediction exists and fetches it if not.
    """
    model = Claim  # Model to use for the view

    def get(self, request, *args, **kwargs):
        claim = self.get_object()  # Get the claim object
        
        try:
            # Check if we already have a prediction
            if claim.prediction_result and not request.GET.get('force_refresh'):
                return JsonResponse(claim.prediction_result)  # Return existing prediction

            # Get related data for prediction
            accident = claim.accident
            driver = Driver.objects.filter(accident=accident).first()
            vehicle = Vehicle.objects.filter(accident=accident).first()
            injury = Injury.objects.filter(accident=accident).first()

            # Use new preprocessing function to get 18 features
            input_features = preprocess_single_claim_for_prediction(
                claim_instance=claim,
                driver_instance=driver,
                accident_instance=accident,
                vehicle_instance=vehicle,
                injury_instance=injury
            )

            # Check if MLaaS URL is configured
            if not getattr(settings, 'MLAAS_SERVICE_URL', None):
                return JsonResponse({
                    'status': 'error',
                    'message': 'MLaaS service not configured'  # Return error if MLaaS is not configured
                }, status=500)

            # Construct endpoint URL 
            algorithm_id = get_active_insurance_model_id()

            if not algorithm_id:
                logger.error(f"Could not determine active ML algorithm for Claim {claim.id} (ClaimPredictionView).")
                return JsonResponse({'status': 'error', 'message': 'MLaaS: Could not determine active model ID for prediction.'}, status=500)

            predict_url = f"{settings.MLAAS_SERVICE_URL.rstrip('/')}/algorithms/{algorithm_id}/predict/"

            # Make prediction request
            payload = {"input_data": [input_features]}
            logger.info(f"Sending ML prediction request for Claim {claim.id} to {predict_url} (ClaimPredictionView, active_id: {algorithm_id})")
            response = requests.post(
                predict_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()  # Raise an HTTPError if status >= 400

            # Store and return prediction
            result_json = response.json()  # Parse response as JSON
            claim.prediction_result = result_json  # Store prediction result in claim
            claim.save(update_fields=['prediction_result'])  # Save the claim

            return JsonResponse(result_json)  # Return prediction result

        except requests.exceptions.RequestException as ex:
            logger.error(f"ML prediction request failed for Claim {claim.id} (ClaimPredictionView): {ex}")  # Log prediction request failure
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to get prediction: {str(ex)}'  # Return error message
            }, status=503)
        except Exception as ex:
            logger.error(f"Unexpected error during prediction for Claim {claim.id} (ClaimPredictionView)")
            return JsonResponse({
                'status': 'error',
                'message': f'Unexpected error: {str(ex)}'  # Return unexpected error message
            }, status=500)

class ClaimSuccessView(LoginRequiredMixin, DetailView):
    """
    View for displaying the success page after a claim submission.

    This view retrieves the claim based on the session ID.
    """
    model = Claim  # Model to use for the view
    template_name = 'claims/claim_success.html'  # Template for rendering the success page
    context_object_name = 'claim'  # Context variable name for claim

    def get_object(self):
        claim_id = self.request.session.get('claim_id')  # Get claim ID from session
        if not claim_id:
            return None  # Return None if no claim ID found
        return Claim.objects.select_related('accident').get(id=claim_id)  # Get the claim object

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('claim_id'):
            return redirect('claims:claim_dashboard')  # Redirect to dashboard if no claim ID
        return super().dispatch(request, *args, **kwargs)  # Proceed with normal dispatch

def claim_detail(request, claim_id):
    """
    View for displaying the details of a specific claim.

    This view also handles prediction requests for the claim.
    """
    logger = logging.getLogger(__name__)  # Set up logging

    claim = get_object_or_404(Claim, id=claim_id)  # Get the claim object or return 404
    error = None  # Initialise error variable
    prediction = None  # Initialise prediction variable
    request_id = None  # Initialise request_id variable

    if request.method == 'POST' and 'get_prediction' in request.POST:
        # Only fetch prediction if not already present
        if not claim.prediction_result or 'error' in claim.prediction_result or request.GET.get('force_refresh'):
            try:
                accident = claim.accident
                driver = Driver.objects.filter(accident=accident).first()
                vehicle = Vehicle.objects.filter(accident=accident).first()
                injury = Injury.objects.filter(accident=accident).first()
                input_features = preprocess_single_claim_for_prediction(
                    claim_instance=claim,
                    driver_instance=driver,
                    accident_instance=accident,
                    vehicle_instance=vehicle,
                    injury_instance=injury
                )
                if not getattr(settings, 'MLAAS_SERVICE_URL', None):
                    error = 'MLaaS service not configured.'  # Set error if MLaaS is not configured
                else:
                    algorithm_id = get_active_insurance_model_id()
                    
                    if not algorithm_id:
                        error = 'MLaaS: Could not determine active model ID for prediction.'
                    else:
                        predict_url = f"{settings.MLAAS_SERVICE_URL.rstrip('/')}/algorithms/{algorithm_id}/predict/"
                        payload = {"input_data": [input_features]}
                        
                        logger.info(f"Sending ML prediction request for Claim {claim.id} to {predict_url} (claim_detail view, active_id: {algorithm_id})")
                        response = requests.post(predict_url, json=payload, timeout=10)
                        response.raise_for_status()
                        result_json = response.json()
                        claim.prediction_result = result_json
                        claim.save(update_fields=['prediction_result'])
                        request_id = result_json.get('request_id')
            except Exception as ex:
                logger.exception(f"Prediction error in claim_detail for Claim {claim.id}")
                error = f"Prediction error: {ex}"
                claim.prediction_result = {'error': str(ex)}
                claim.save(update_fields=['prediction_result'])
        return redirect('claims:claim_detail', claim_id=claim.id)

    # Prepare context
    if claim.prediction_result:
        if 'error' in claim.prediction_result:
            error = claim.prediction_result.get('error')  # Get error from prediction result
        elif 'prediction' in claim.prediction_result:
            prediction = claim.prediction_result['prediction']  # Get prediction from prediction result
            request_id = claim.prediction_result.get('request_id')
        else:
            prediction = claim.prediction_result  # Set prediction to prediction result

    return render(request, 'claims/claim_detail.html', {
        'claim': claim,  # Pass claim to template
        'prediction': prediction,  # Pass prediction to template
        'error': error,  # Pass error to template
        'request_id': request_id,
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def export_claims_data(request):
    queryset = Claim.objects.select_related('accident').all()
    serializer = ClaimExportSerializer(queryset, many=True)
    return Response(serializer.data)