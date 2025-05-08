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

logger = logging.getLogger(__name__)  # Set up logging

# --- Helper Function for MLaaS API Calls ---
def _call_mlaas_api(method: str, endpoint_path: str, json_payload: dict = None,
                    data_payload: dict = None, files: dict = None,
                    timeout: int = 30) -> dict:
    """
    Makes a request to the configured MLaaS API endpoint.
    Returns a dictionary with 'data'/'status_code' or 'error'/'status_code'.
    """
    mlaas_base_url = os.environ.get('MLAAS_SERVICE_URL', 'http://mlaas:8009/api/')  # Get MLaaS base URL from environment
    if not mlaas_base_url:
        logger.error("MLAAS_SERVICE_URL environment variable is not set.")  # Log error if URL is not set
        return {'error': 'MLaaS service URL not configured.', 'status_code': 500}  # Return error response

    url = f"{mlaas_base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"  # Construct full URL
    headers = {}  # Initialise headers
    # Add Auth headers here if needed, e.g.,
    # headers['Authorization'] = f"Bearer {your_token_logic()}"

    logger.debug("Calling MLaaS API: %s %s", method.upper(), url)  # Log API call
    try:
        with requests.Session() as session:  # Use a session for the request
            session.headers.update(headers)  # Update session headers
            if files:
                response = session.request(
                    method, url, data=data_payload, files=files, timeout=timeout  # Send request with files
                )
            else:
                response = session.request(
                    method, url, json=json_payload, timeout=timeout  # Send request with JSON payload
                )

        response.raise_for_status()  # Raise an HTTPError if status >= 400

        if response.status_code == 204:
            return {'data': None, 'status_code': response.status_code}  # Return empty response for 204

        try:
            response_data = response.json()  # Parse response as JSON
            return {'data': response_data, 'status_code': response.status_code}  # Return data and status code
        except requests.exceptions.JSONDecodeError:
            logger.warning(
                "MLaaS API (%s %s) returned non-JSON response (status %d): %s",
                method.upper(), url, response.status_code, response.text[:150]  # Log non-JSON response
            )
            if 200 <= response.status_code < 300:
                 return {
                    'data': {'raw_response': response.text},  # Return raw response for successful status
                    'status_code': response.status_code,
                    'warning': 'Non-JSON response received'  # Warning for non-JSON response
                 }
            else:
                 return {
                     'error': f'MLaaS returned status {response.status_code} with non-JSON content.',  # Return error for non-JSON response
                     'status_code': response.status_code
                 }

    except requests.exceptions.Timeout:
        logger.error("MLaaS API request timed out: %s %s", method.upper(), url)  # Log timeout error
        return {'error': f'Request to MLaaS timed out ({url}).', 'status_code': 504}  # Return timeout error
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code  # Get status code from error
        error_detail = f"MLaaS returned status {status_code}"  # Prepare error detail
        error_data = None  # Initialise error data
        try:
            error_data = e.response.json()  # Try to parse error response as JSON
            error_detail = error_data.get('detail', error_data.get('error', str(error_data)))  # Get detailed error message
        except requests.exceptions.JSONDecodeError:
            error_detail = e.response.text[:150].strip() or f"MLaaS returned status {status_code}"  # Fallback for non-JSON error
        logger.warning("MLaaS API HTTP Error (%s): %s %s -> %s",
                       status_code, method.upper(), url, error_detail)  # Log HTTP error
        return {
            'error': f"MLaaS Error ({status_code}): {error_detail}",  # Return error response
            'status_code': status_code
        }
    except requests.exceptions.RequestException as e:
        logger.error("MLaaS API connection error: %s %s -> %s",
                       method.upper(), url, e, exc_info=True)  # Log connection error
        return {'error': f'Network error connecting to MLaaS ({url}).', 'status_code': 503}  # Return network error
    except Exception as e:
        logger.exception("Unexpected error during MLaaS API call to %s", url)  # Log unexpected error
        return {'error': f'Unexpected client-side error: {e}', 'status_code': 500}  # Return unexpected error

def _get_dashboard_context_data(request) -> dict:
    """Helper to fetch models, logs, and endpoints for the dashboard context."""
    context = {}  # Initialise context dictionary
    ml_models = []  # Initialise list for ML models
    prediction_logs = []  # Initialise list for prediction logs
    available_endpoints = []  # Initialise list for available endpoints

    # Fetch Models (use new engineer endpoint)
    mlaas_model_response = _call_mlaas_api('GET', 'engineer/models/')
    if 'error' in mlaas_model_response:
        messages.error(request, f"Could not fetch models: {mlaas_model_response['error']}")  # Log error if fetching models fails
    elif 'data' in mlaas_model_response:
        ml_models = mlaas_model_response['data']
        if isinstance(ml_models, list):
            logger.info("Fetched %d models from MLaaS.", len(ml_models))
        else:
            messages.warning(request, "Received unexpected model data format from MLaaS.")
            logger.warning("Unexpected model data format: %s", ml_models)

    # Fetch Prediction Logs
    mlaas_log_response = _call_mlaas_api('GET', 'requests/?limit=50')  # Call MLaaS API to get prediction logs
    if 'error' in mlaas_log_response:
        messages.error(request, f"Could not fetch prediction logs: {mlaas_log_response['error']}")  # Log error if fetching logs fails
    elif 'data' in mlaas_log_response:
        log_data = mlaas_log_response['data']  # Get log data from response
        results = log_data.get('results') if isinstance(log_data, dict) else log_data  # Get results
        if isinstance(results, list):
            prediction_logs = results  # Store logs in context
            logger.info("Fetched %d prediction logs from MLaaS.", len(prediction_logs))  # Log number of logs fetched
        else:
            messages.warning(request, "Received unexpected prediction log format from MLaaS.")  # Log warning for unexpected format
            logger.warning("Unexpected prediction log data format: %s", log_data)  # Log unexpected format

    # Fetch Available Endpoints
    mlaas_endpoint_response = _call_mlaas_api('GET', 'endpoints/')  # Call MLaaS API to get endpoints
    if 'error' in mlaas_endpoint_response:
        messages.warning(request, f"Could not fetch endpoint list: {mlaas_endpoint_response['error']}")  # Log warning if fetching endpoints fails
    elif 'data' in mlaas_endpoint_response:
        endpoint_data = mlaas_endpoint_response['data']  # Get endpoint data from response
        results = endpoint_data.get('results') if isinstance(endpoint_data, dict) else endpoint_data  # Get results
        if isinstance(results, list):
            # Filter for valid entries and store id/name needed for dropdown
            available_endpoints = [
                {'id': ep.get('id'), 'name': ep.get('name')}  # Store endpoint ID and name
                for ep in results if ep.get('id') and ep.get('name')  # Ensure ID and name are present
            ]
            logger.info("Fetched %d endpoints from MLaaS.", len(available_endpoints))  # Log number of endpoints fetched
        else:
            messages.warning(request, "No endpoints found via API or unexpected format.")  # Log warning for unexpected format
            logger.warning("No endpoints fetched or unexpected endpoint format: %s", endpoint_data)  # Log unexpected format

    context['ml_models'] = ml_models  # Add models to context
    context['prediction_logs'] = prediction_logs  # Add logs to context
    context['available_endpoints'] = available_endpoints  # Add endpoints to context
    return context  # Return context dictionary

# --- Engineer Dashboard View ---
@never_cache
@login_required
@user_passes_test(utils.is_engineer, login_url='role_redirect')
def engineer_page(request):
    """Displays the Engineer dashboard (GET) with models, logs, and registration form."""
    logger.info("Engineer dashboard requested by user '%s'", request.user.username)  # Log dashboard request
    context = _get_dashboard_context_data(request)  # Get context data for dashboard
    if 'upload_form' not in context:  # Ensure form instance exists for GET requests
        context['upload_form'] = ModelUploadForm()  # Add model upload form to context
    return render(request, 'engineer/engineer.html', context)  # Render engineer dashboard

# --- Model Registration View ---
@require_POST
@login_required
@user_passes_test(utils.is_engineer, login_url='role_redirect')
def upload_model(request):
    """Handles POST request for registering a new model via MLaaS API."""
    logger.info("Engineer model registration submission by user '%s'", request.user.username)  # Log model registration submission
    form = ModelUploadForm(request.POST, request.FILES)  # Get form data

    if form.is_valid():  # Check if form is valid
        cleaned_data = form.cleaned_data  # Get cleaned data from form
        model_file = cleaned_data['model_file']  # Get model file from cleaned data

        payload_data = {
            'name': cleaned_data['name'],  # Model name
            'version': cleaned_data['version'],  # Model version
            'model_type': cleaned_data['model_type'],  # Model type
            'description': cleaned_data.get('description', ''),  # Model description
            'parent_endpoint': cleaned_data['parent_endpoint'],  # Parent endpoint ID
            'is_active': cleaned_data.get('is_active', False),  # Active status
        }
        files_data = {
            'model_file': (model_file.name, model_file.read(), model_file.content_type)  # Prepare file data for upload
        }

        logger.debug("Attempting registration for model '%s' v'%s' via MLaaS API.",
                     cleaned_data['name'], cleaned_data['version'])  # Log model registration attempt

        mlaas_response = _call_mlaas_api(
            'POST', 'algorithms/', data_payload=payload_data, files=files_data, timeout=60  # Call MLaaS API to register model
        )

        # Process MLaaS API response
        if 'error' in mlaas_response:  # Check for errors in response
            error_msg = f"Model registration failed: {mlaas_response['error']}"  # Prepare error message
            if mlaas_response.get('status_code') == 400 and mlaas_response.get('error_data'):
                # Map MLaaS validation errors back to Django form if possible
                form_errors = mlaas_response['error_data']  # Get error data
                if isinstance(form_errors, dict):
                    for field, errors in form_errors.items():
                        form.add_error(field if field in form.fields else None, errors)  # Add errors to form
                elif isinstance(form_errors, list):
                    form.add_error(None, "; ".join(form_errors))  # Add non-field errors to form
                error_msg = "Model registration failed. Please check form errors."  # User-friendly summary
            messages.error(request, error_msg)  # Display error message
            # Re-render the page with form errors and existing context data
            context = _get_dashboard_context_data(request)  # Get context data
            context['upload_form'] = form  # Add form to context
            return render(request, 'engineer/engineer.html', context)  # Render engineer page with errors

        elif mlaas_response.get('status_code') in [200, 201]:  # Check for successful response
            messages.success(
                request,
                f"Model '{cleaned_data['name']}' v'{cleaned_data['version']}' registered successfully!"  # Success message
            )
            return redirect('engineer:engineer_page')  # Redirect to engineer page
        else:
            status = mlaas_response.get('status_code', 'N/A')  # Get status code from response
            messages.error(request, f"Registration failed: Unexpected MLaaS response (Status: {status}).")  # Error message
            context = _get_dashboard_context_data(request)  # Get context data
            context['upload_form'] = form  # Add form to context
            return render(request, 'engineer/engineer.html', context)  # Render engineer page with errors

    else:
        # Form is invalid (client-side validation failed)
        logger.warning("Model registration form validation failed: %s", form.errors.as_json())  # Log form validation errors
        messages.error(request, "Registration failed. Please check the form errors below.")  # Error message
        # Re-render the page with the invalid form and existing context data
        context = _get_dashboard_context_data(request)  # Get context data
        context['upload_form'] = form  # Add form to context
        return render(request, 'engineer/engineer.html', context)  # Render engineer page with errors

# --- Retraining Trigger View ---
@require_POST
@login_required
@user_passes_test(utils.is_engineer, login_url='role_redirect')
def trigger_retrain(request, algorithm_id: int):
    """Handles POST request to trigger retraining for a specific algorithm ID."""
    logger.info("Engineer retraining request for Algorithm ID %s by user '%s'",
                algorithm_id, request.user.username)  # Log retraining request

    mlaas_response = _call_mlaas_api(
        'POST', f'algorithms/{algorithm_id}/retrain/', timeout=300  # Call MLaaS API to trigger retraining
    )

    if 'error' in mlaas_response:  # Check for errors in response
        messages.error(
            request,
            f"Retraining trigger for model ID {algorithm_id} failed: {mlaas_response['error']}"  # Error message
        )
    elif 'data' in mlaas_response:  # Check for data in response
        mlaas_data = mlaas_response['data'] or {}  # Get data from response
        status_code = mlaas_response.get('status_code')  # Get status code from response
        message = mlaas_data.get('message', f'Retraining request processed (Status: {status_code}).')  # Prepare message
        new_model_info = mlaas_data.get('new_algorithm')  # Get new algorithm info

        if mlaas_data.get("status") == "no_data":  # Check if no data returned
            messages.info(request, f"Retraining for model ID {algorithm_id}: {message}")  # Info message
        elif status_code in [200, 201, 202]:  # Check for successful status codes
            messages.success(request, f"Retraining for model ID {algorithm_id}: {message}")  # Success message
            if new_model_info:  # Check if new model info exists
                logger.info("Retraining created new model: ID %s, Version %s",
                            new_model_info.get('id'), new_model_info.get('version'))  # Log new model creation
        else:
            messages.info(request, f"Retraining status for model ID {algorithm_id}: {message}")  # Info message
    else:
        messages.error(
            request,
            f"Retraining trigger for model ID {algorithm_id}: Unknown response from MLaaS."  # Error message
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