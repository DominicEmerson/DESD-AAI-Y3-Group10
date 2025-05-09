# Backend/ml_service_utils.py
import os
import requests
import logging
from django.conf import settings 

logger = logging.getLogger(__name__)

def get_active_insurance_model_id():
    """
    Returns the ID of the single MLaaS algorithm that is 'is_active=True' for the
    'Insurance Claim Prediction' endpoint. Logs an error if more than one is found.
    """
    mlaas_base_url = getattr(settings, 'MLAAS_SERVICE_URL', None)
    if not mlaas_base_url:
        logger.error("MLAAS_SERVICE_URL not configured in Backend/insurance_ai/settings.py.")
        return None

    list_models_url = f"{mlaas_base_url.rstrip('/')}/engineer/models/"
    logger.debug(f"Querying MLaaS for the active model ID for 'Insurance Claim Prediction' at: {list_models_url}")

    try:
        response = requests.get(list_models_url, timeout=10)
        response.raise_for_status()
        models_data = response.json()

        if not isinstance(models_data, list):
            logger.error(f"MLaaS endpoint {list_models_url} did not return a list. Response: {models_data}")
            return None

        active_models = [
            m for m in models_data
            if m.get('parent_endpoint_details', {}).get('name') == "Insurance Claim Prediction"
            and m.get('is_active')
        ]
        if len(active_models) == 1:
            return int(active_models[0]['id'])
        elif len(active_models) > 1:
            logger.error("More than one active model found for Insurance Claim Prediction! This should not happen.")
            return int(active_models[0]['id'])
        else:
            logger.warning("No active model found for Insurance Claim Prediction.")
            return None
    except Exception as ex:
        logger.error(f"Error in get_active_insurance_model_id: {ex}", exc_info=True)
        return None