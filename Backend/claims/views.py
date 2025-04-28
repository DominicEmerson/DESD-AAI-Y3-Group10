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

    def get_queryset(self):
        user = self.request.user
        if user.role == 'enduser':
            return Claim.objects.filter(accident__reported_by=user).select_related('accident')
        elif user.role in ['admin', 'finance']:
            return Claim.objects.all().select_related('accident')
        elif user.role == 'engineer':
            return Claim.objects.all().select_related(
                'accident', 'accident__vehicle', 'accident__driver', 'accident__injury'
            )
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
            algorithm_id = getattr(settings, 'DEFAULT_ML_ALGORITHM_ID', 1)
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
        return JsonResponse({
            'status': 'pending',
            'message': 'Prediction service not yet available'
        })


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