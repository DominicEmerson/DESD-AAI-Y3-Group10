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
import utils

User = get_user_model()
logger = logging.getLogger(__name__)

# @never_cache
# @login_required
# @user_passes_test(utils.is_enduser, login_url='role_redirect')
# def enduser_page(request):
#     return render(request, 'claims/dashboard.html')

# ------------------------
# Claims Views (Author: Ahmed Mohamed)
# ------------------------

class ClaimDashboardView(LoginRequiredMixin, ListView):
    model = Claim
    template_name = 'claims/dashboard.html'
    context_object_name = 'claims'
    paginate_by = 10  # This will show only 10 records per page

    def get_queryset(self):
        user = self.request.user
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
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context.update({
            'user_role': self.request.user.role,
            'total_claims': qs.count(),
            'pending_claims': qs.filter(settlement_value=0).count(),
            'approved_claims': qs.exclude(settlement_value=0).count(),
        })
        return context



class ClaimSubmissionView(LoginRequiredMixin, CreateView):
    form_class = ClaimSubmissionForm
    template_name = 'claims/claim_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = kwargs.get('form') or self.get_form()
        context.update({
            'accident_form': form.accident_form,
            'vehicle_form': form.vehicle_form,
            'driver_form': form.driver_form,
            'injury_form': form.injury_form,
        })
        return context

    def form_valid(self, form):
        try:
            self.request.session.pop('claim_id', None)
            self.object = form.save(commit=False)
            if self.object.accident:
                self.object.accident.reported_by = self.request.user
                self.object.accident.save()
            self.object.save()
            self.request.session['claim_id'] = self.object.id
            self.request.session.modified = True
            messages.success(self.request, 'Claim submitted successfully!')

            #  call the ML service
            self.request_prediction(self.object)

            return redirect('claims:claim_submission_success')
        except Exception as e:
            messages.error(self.request, f'Error submitting claim: {str(e)}')
            return self.form_invalid(form)

    # Implement a minimal MLaaS API call
    def request_prediction(self, claim):
        """
        Sends claim data to the MLaaS API to get a prediction.
        Updates the claim object's 'prediction_result' field with the response.
        """
        # Check if MLaaS URL is configured
        if not getattr(settings, 'MLAAS_SERVICE_URL', None):
            logger.warning("MLAAS_SERVICE_URL not configured. Skipping prediction.")
            claim.prediction_result = {'error': 'MLaaS not configured'}
            claim.save(update_fields=['prediction_result'])
            return

        # For a simple 3-feature regressor, let's pick any 3 fields from the claim:
        try:
            # fetch related data (accident, vehicle, etc.) if needed
            accident = claim.accident
            driver = Driver.objects.filter(accident=accident).first()

            # If your model expects exactly 3 numeric inputs, just pick 3:
            input_features = [
                float(claim.special_health_expenses or 0),
                float(claim.special_earnings_loss or 0),
                float(driver.driver_age if driver else 0)
            ]

            # The MLaaS expects a JSON payload like this:
            payload = {
                "input_data": [input_features],  # a list of lists
                "algorithm_name": "3feature_regression_model"  # or whatever your ML service expects
            }

            # Construct endpoint URL 
            algorithm_id = getattr(settings, 'DEFAULT_ML_ALGORITHM_ID', 5)
            predict_url = f"{settings.MLAAS_SERVICE_URL.rstrip('/')}/algorithms/{algorithm_id}/predict/"

            logger.info(f"Sending ML prediction request for Claim {claim.id} to {predict_url}")

            response = requests.post(predict_url, json=payload, timeout=10)
            response.raise_for_status()  # Raise an HTTPError if status >= 400

            result_json = response.json()
            claim.prediction_result = result_json
            claim.save(update_fields=['prediction_result'])

            logger.info(f"Claim {claim.id} prediction stored: {result_json}")

        except requests.exceptions.RequestException as ex:
            logger.error(f"ML prediction request failed for Claim {claim.id}: {ex}")
            claim.prediction_result = {'error': str(ex)}
            claim.save(update_fields=['prediction_result'])

        except Exception as ex:
            logger.exception(f"Unexpected error during ML prediction for Claim {claim.id}: {ex}")
            claim.prediction_result = {'error': f'Unexpected: {ex}'}
            claim.save(update_fields=['prediction_result'])



class ClaimPredictionView(LoginRequiredMixin, DetailView):
    model = Claim

    def get(self, request, *args, **kwargs):
        claim = self.get_object()
        
        try:
            # Check if we already have a prediction
            if claim.prediction_result and not request.GET.get('force_refresh'):
                return JsonResponse(claim.prediction_result)

            # Get related data for prediction
            accident = claim.accident
            driver = Driver.objects.filter(accident=accident).first()

            # Prepare input features (same as in ClaimSubmissionView)
            input_features = [
                float(claim.special_health_expenses or 0),
                float(claim.special_earnings_loss or 0),
                float(driver.driver_age if driver else 0)
            ]

            # Check if MLaaS URL is configured
            if not getattr(settings, 'MLAAS_SERVICE_URL', None):
                return JsonResponse({
                    'status': 'error',
                    'message': 'MLaaS service not configured'
                }, status=500)

            # Construct endpoint URL 
            algorithm_id = getattr(settings, 'DEFAULT_ML_ALGORITHM_ID', 5)
            predict_url = f"{settings.MLAAS_SERVICE_URL.rstrip('/')}/algorithms/{algorithm_id}/predict/"

            # Make prediction request
            response = requests.post(
                predict_url,
                json={"input_data": [input_features]},
                timeout=10
            )
            response.raise_for_status()

            # Store and return prediction
            result_json = response.json()
            claim.prediction_result = result_json
            claim.save(update_fields=['prediction_result'])

            return JsonResponse(result_json)

        except requests.exceptions.RequestException as ex:
            logger.error(f"ML prediction request failed for Claim {claim.id}: {ex}")
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to get prediction: {str(ex)}'
            }, status=503)
        except Exception as ex:
            logger.error(f"Unexpected error during prediction for Claim {claim.id}: {ex}")
            return JsonResponse({
                'status': 'error',
                'message': f'Unexpected error: {str(ex)}'
            }, status=500)


class ClaimSuccessView(LoginRequiredMixin, DetailView):
    model = Claim
    template_name = 'claims/claim_success.html'
    context_object_name = 'claim'

    def get_object(self):
        claim_id = self.request.session.get('claim_id')
        if not claim_id:
            return None
        return Claim.objects.select_related('accident').get(id=claim_id)

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('claim_id'):
            return redirect('claims:claim_dashboard')
        return super().dispatch(request, *args, **kwargs)

def claim_detail(request, claim_id):
   
    logger = logging.getLogger(__name__)

    claim = get_object_or_404(Claim, id=claim_id)
    error = None
    prediction = None

    if request.method == 'POST' and 'get_prediction' in request.POST:
        # Only fetch prediction if not already present
        if not claim.prediction_result or 'error' in claim.prediction_result:
            try:
                accident = claim.accident
                driver = Driver.objects.filter(accident=accident).first()
                input_features = [
                    float(getattr(claim, 'special_health_expenses', 0)),
                    float(getattr(claim, 'special_earnings_loss', 0)),
                    float(getattr(driver, 'driver_age', 0) if driver else 0)
                ]
                if not getattr(settings, 'MLAAS_SERVICE_URL', None):
                    error = 'MLaaS service not configured.'
                else:
                    algorithm_id = getattr(settings, 'DEFAULT_ML_ALGORITHM_ID', 5)
                    predict_url = f"{settings.MLAAS_SERVICE_URL.rstrip('/')}/algorithms/{algorithm_id}/predict/"
                    response = requests.post(
                        predict_url,
                        json={"input_data": [input_features]},
                        timeout=10
                    )
                    response.raise_for_status()
                    result_json = response.json()
                    claim.prediction_result = result_json
                    claim.save(update_fields=['prediction_result'])
            except Exception as ex:
                logger.error(f"Prediction error: {ex}")
                error = f"Prediction error: {ex}"
                claim.prediction_result = {'error': str(ex)}
                claim.save(update_fields=['prediction_result'])
        return redirect('claims:claim_detail', claim_id=claim.id)

    # Prepare context
    if claim.prediction_result:
        if 'error' in claim.prediction_result:
            error = claim.prediction_result.get('error')
        elif 'prediction' in claim.prediction_result:
            prediction = claim.prediction_result['prediction']
        else:
            prediction = claim.prediction_result

    return render(request, 'claims/claim_detail.html', {
        'claim': claim,
        'prediction': prediction,
        'error': error,
    })