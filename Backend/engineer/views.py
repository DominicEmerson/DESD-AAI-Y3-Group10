# engineer/views.py
import logging
import os
import requests

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET

# Local application/project imports
from .forms import ModelUploadForm
import utils  # Assuming utils.py contains is_engineer role check

logger = logging.getLogger(__name__)


# --- Helper Function for MLaaS API Calls ---
def _call_mlaas_api(method: str, endpoint_path: str, json_payload: dict = None,
                    data_payload: dict = None, files: dict = None,
                    timeout: int = 30) -> dict:
    """
    Makes a request to the configured MLaaS API endpoint.
    Returns a dictionary with 'data'/'status_code' or 'error'/'status_code'.
    """
    mlaas_base_url = os.environ.get('MLAAS_SERVICE_URL', 'http://mlaas:8009/api/')
    if not mlaas_base_url:
        logger.error("MLAAS_SERVICE_URL environment variable is not set.")
        return {'error': 'MLaaS service URL not configured.', 'status_code': 500}

    url = f"{mlaas_base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
    headers = {}
    # Add Auth headers here if needed, e.g.,
    # headers['Authorization'] = f"Bearer {your_token_logic()}"

    logger.debug("Calling MLaaS API: %s %s", method.upper(), url)
    try:
        with requests.Session() as session:
            session.headers.update(headers)
            if files:
                response = session.request(
                    method, url, data=data_payload, files=files, timeout=timeout
                )
            else:
                response = session.request(
                    method, url, json=json_payload, timeout=timeout
                )

        response.raise_for_status()

        if response.status_code == 204:
            return {'data': None, 'status_code': response.status_code}

        try:
            response_data = response.json()
            return {'data': response_data, 'status_code': response.status_code}
        except requests.exceptions.JSONDecodeError:
            logger.warning(
                "MLaaS API (%s %s) returned non-JSON response (status %d): %s",
                method.upper(), url, response.status_code, response.text[:150]
            )
            if 200 <= response.status_code < 300:
                 return {
                    'data': {'raw_response': response.text},
                    'status_code': response.status_code,
                    'warning': 'Non-JSON response received'
                 }
            else:
                 return {
                     'error': f'MLaaS returned status {response.status_code} with non-JSON content.',
                     'status_code': response.status_code
                 }

    except requests.exceptions.Timeout:
        logger.error("MLaaS API request timed out: %s %s", method.upper(), url)
        return {'error': f'Request to MLaaS timed out ({url}).', 'status_code': 504}
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_detail = f"MLaaS returned status {status_code}"
        error_data = None
        try:
            error_data = e.response.json()
            error_detail = error_data.get('detail', error_data.get('error', str(error_data)))
        except requests.exceptions.JSONDecodeError:
            error_detail = e.response.text[:150].strip() or f"MLaaS returned status {status_code}"
        logger.warning("MLaaS API HTTP Error (%s): %s %s -> %s",
                       status_code, method.upper(), url, error_detail)
        return {
            'error': f"MLaaS Error ({status_code}): {error_detail}",
            'status_code': status_code,
            'error_data': error_data
        }
    except requests.exceptions.RequestException as e:
        logger.error("MLaaS API connection error: %s %s -> %s",
                       method.upper(), url, e, exc_info=True)
        return {'error': f'Network error connecting to MLaaS ({url}).', 'status_code': 503}
    except Exception as e:
        logger.exception("Unexpected error during MLaaS API call to %s", url)
        return {'error': f'Unexpected client-side error: {e}', 'status_code': 500}


def _get_dashboard_context_data(request) -> dict:
    """Helper to fetch models, logs, and endpoints for the dashboard context."""
    context = {}
    ml_models = []
    prediction_logs = []
    available_endpoints = []

    # Fetch Models (use new engineer endpoint)
    mlaas_model_response = _call_mlaas_api('GET', 'engineer/models/')
    if 'error' in mlaas_model_response:
        messages.error(request, f"Could not fetch models: {mlaas_model_response['error']}")
    elif 'data' in mlaas_model_response:
        ml_models = mlaas_model_response['data']
        if isinstance(ml_models, list):
            logger.info("Fetched %d models from MLaaS.", len(ml_models))
        else:
            messages.warning(request, "Received unexpected model data format from MLaaS.")
            logger.warning("Unexpected model data format: %s", ml_models)

    # Fetch Prediction Logs
    mlaas_log_response = _call_mlaas_api('GET', 'requests/?limit=50')
    if 'error' in mlaas_log_response:
        messages.error(request, f"Could not fetch prediction logs: {mlaas_log_response['error']}")
    elif 'data' in mlaas_log_response:
        log_data = mlaas_log_response['data']
        results = log_data.get('results') if isinstance(log_data, dict) else log_data
        if isinstance(results, list):
            prediction_logs = results
            logger.info("Fetched %d prediction logs from MLaaS.", len(prediction_logs))
        else:
            messages.warning(request, "Received unexpected prediction log format from MLaaS.")
            logger.warning("Unexpected prediction log data format: %s", log_data)

    # Fetch Available Endpoints
    mlaas_endpoint_response = _call_mlaas_api('GET', 'endpoints/')
    if 'error' in mlaas_endpoint_response:
        messages.warning(request, f"Could not fetch endpoint list: {mlaas_endpoint_response['error']}")
    elif 'data' in mlaas_endpoint_response:
        endpoint_data = mlaas_endpoint_response['data']
        results = endpoint_data.get('results') if isinstance(endpoint_data, dict) else endpoint_data
        if isinstance(results, list):
            # Filter for valid entries and store id/name needed for dropdown
            available_endpoints = [
                {'id': ep.get('id'), 'name': ep.get('name')}
                for ep in results if ep.get('id') and ep.get('name')
            ]
            logger.info("Fetched %d endpoints from MLaaS.", len(available_endpoints))
        else:
            messages.warning(request, "No endpoints found via API or unexpected format.")
            logger.warning("No endpoints fetched or unexpected endpoint format: %s", endpoint_data)

    context['ml_models'] = ml_models
    context['prediction_logs'] = prediction_logs
    context['available_endpoints'] = available_endpoints
    return context


# --- Engineer Dashboard View ---
@never_cache
@login_required
@user_passes_test(utils.is_engineer, login_url='role_redirect')
def engineer_page(request):
    """Displays the Engineer dashboard (GET) with models, logs, and registration form."""
    logger.info("Engineer dashboard requested by user '%s'", request.user.username)
    context = _get_dashboard_context_data(request)
    if 'upload_form' not in context: # Ensure form instance exists for GET requests
        context['upload_form'] = ModelUploadForm()
    return render(request, 'engineer/engineer.html', context)


# --- Model Registration View ---
@require_POST
@login_required
@user_passes_test(utils.is_engineer, login_url='role_redirect')
def upload_model(request):
    """Handles POST request for registering a new model via MLaaS API."""
    logger.info("Engineer model registration submission by user '%s'", request.user.username)
    form = ModelUploadForm(request.POST, request.FILES)

    if form.is_valid():
        cleaned_data = form.cleaned_data
        model_file = cleaned_data['model_file']

        payload_data = {
            'name': cleaned_data['name'],
            'version': cleaned_data['version'],
            'model_type': cleaned_data['model_type'],
            'description': cleaned_data.get('description', ''),
            'parent_endpoint': cleaned_data['parent_endpoint'], # Send the integer ID
            'is_active': cleaned_data.get('is_active', False),
        }
        files_data = {
            'model_file': (model_file.name, model_file.read(), model_file.content_type)
        }

        logger.debug("Attempting registration for model '%s' v'%s' via MLaaS API.",
                     cleaned_data['name'], cleaned_data['version'])

        mlaas_response = _call_mlaas_api(
            'POST', 'algorithms/', data_payload=payload_data, files=files_data, timeout=60
        )

        # Process MLaaS API response
        if 'error' in mlaas_response:
            error_msg = f"Model registration failed: {mlaas_response['error']}"
            if mlaas_response.get('status_code') == 400 and mlaas_response.get('error_data'):
                # Map MLaaS validation errors back to Django form if possible
                form_errors = mlaas_response['error_data']
                if isinstance(form_errors, dict):
                    for field, errors in form_errors.items():
                        form.add_error(field if field in form.fields else None, errors)
                elif isinstance(form_errors, list):
                    form.add_error(None, "; ".join(form_errors))
                error_msg = "Model registration failed. Please check form errors." # User-friendly summary
            messages.error(request, error_msg)
            # Re-render the page with form errors and existing context data
            context = _get_dashboard_context_data(request)
            context['upload_form'] = form
            return render(request, 'engineer/engineer.html', context)

        elif mlaas_response.get('status_code') in [200, 201]:
            messages.success(
                request,
                f"Model '{cleaned_data['name']}' v'{cleaned_data['version']}' registered successfully!"
            )
            return redirect('engineer:engineer_page')
        else:
            status = mlaas_response.get('status_code', 'N/A')
            messages.error(request, f"Registration failed: Unexpected MLaaS response (Status: {status}).")
            context = _get_dashboard_context_data(request)
            context['upload_form'] = form
            return render(request, 'engineer/engineer.html', context)

    else:
        # Form is invalid (client-side validation failed)
        logger.warning("Model registration form validation failed: %s", form.errors.as_json())
        messages.error(request, "Registration failed. Please check the form errors below.")
        # Re-render the page with the invalid form and existing context data
        context = _get_dashboard_context_data(request)
        context['upload_form'] = form
        return render(request, 'engineer/engineer.html', context)


# --- Retraining Trigger View ---
@require_POST
@login_required
@user_passes_test(utils.is_engineer, login_url='role_redirect')
def trigger_retrain(request, algorithm_id: int):
    """Handles POST request to trigger retraining for a specific algorithm ID."""
    logger.info("Engineer retraining request for Algorithm ID %s by user '%s'",
                algorithm_id, request.user.username)

    mlaas_response = _call_mlaas_api(
        'POST', f'algorithms/{algorithm_id}/retrain/', timeout=300
    )

    if 'error' in mlaas_response:
        messages.error(
            request,
            f"Retraining trigger for model ID {algorithm_id} failed: {mlaas_response['error']}"
        )
    elif 'data' in mlaas_response:
        mlaas_data = mlaas_response['data'] or {}
        status_code = mlaas_response.get('status_code')
        message = mlaas_data.get('message', f'Retraining request processed (Status: {status_code}).')
        new_model_info = mlaas_data.get('new_algorithm')

        if mlaas_data.get("status") == "no_data":
            messages.info(request, f"Retraining for model ID {algorithm_id}: {message}")
        elif status_code in [200, 201, 202]:
            messages.success(request, f"Retraining for model ID {algorithm_id}: {message}")
            if new_model_info:
                logger.info("Retraining created new model: ID %s, Version %s",
                            new_model_info.get('id'), new_model_info.get('version'))
        else:
            messages.info(request, f"Retraining status for model ID {algorithm_id}: {message}")
    else:
        messages.error(
            request,
            f"Retraining trigger for model ID {algorithm_id}: Unknown response from MLaaS."
        )

    return redirect('engineer:engineer_page')


# --- Model Swap View ---
@require_POST
@login_required
@user_passes_test(utils.is_engineer, login_url='role_redirect')
def swap_active_model(request):
    """Handles POST request to swap the active model via MLaaS API."""
    model_id = request.POST.get('model_id')
    if not model_id:
        messages.error(request, "No model ID provided for model swap.")
        return redirect('engineer:engineer_page')
    response = _call_mlaas_api('POST', 'engineer/set_active_model/', json_payload={'model_id': model_id})
    if response.get('error'):
        messages.error(request, f"Failed to activate model: {response['error']}")
    else:
        messages.success(request, "Model activated successfully.")
    return redirect('engineer:engineer_page')