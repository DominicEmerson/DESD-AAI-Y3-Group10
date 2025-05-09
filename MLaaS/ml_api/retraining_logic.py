# ml_api/retraining_logic.py

import os
import time
import traceback
from datetime import datetime
import abc  # Abstract Base Classes

import joblib
import pandas as pd
import numpy as np
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.core.files.base import ContentFile
import requests  # Added for Backend API calls

from .models import MLAlgorithm, Endpoint, MLRequest
from .retrain_preprocessing import _preprocess_raw_dataframe_for_retraining  # Import the preprocessor
from .serializers import MLAlgorithmSerializer  # For creating new algorithm instances


class RetrainingError(Exception):
    """Custom exception for specific retraining failures."""
    pass


# --- Base Retrainer Class (Abstract) ---
class BaseRetrainer(abc.ABC):
    """Abstract base class for model retraining strategies."""

    def __init__(self, algorithm_instance: MLAlgorithm):
        """
        Initializes the retrainer with the algorithm instance to be updated.
        Models are expected to be found relative to settings.MODEL_ROOT.
        """
        if not isinstance(algorithm_instance, MLAlgorithm):
            raise TypeError("algorithm_instance must be an MLAlgorithm object.")
        self.algorithm = algorithm_instance
        self.original_model_path = None

        if not self.algorithm.model_file or not hasattr(self.algorithm.model_file, 'name') or not self.algorithm.model_file.name:
            raise ValueError(
                "Algorithm instance provided (ID: {}) has no model file name associated in its 'model_file' field.".format(self.algorithm.id)
            )

        # Get the base filename from the FileField's name attribute.
        # self.algorithm.model_file.name is typically "ml_models/filename.pkl" or just "filename.pkl"
        # os.path.basename() will correctly extract "filename.pkl".
        model_basename = os.path.basename(self.algorithm.model_file.name)

        if not model_basename:
             raise ValueError(
                "Could not determine model basename from algorithm's model_file.name: '{}'".format(self.algorithm.model_file.name)
            )

        # Construct path using MODEL_ROOT.
        # settings.MODEL_ROOT is expected to be like '/app/ml_models'
        self.original_model_path = os.path.join(settings.MODEL_ROOT, model_basename)
        
        print(f"[BaseRetrainer Debug] Algorithm ID: {self.algorithm.id}")
        print(f"[BaseRetrainer Debug] model_file.name from DB: '{self.algorithm.model_file.name}'")
        print(f"[BaseRetrainer Debug] Extracted model_basename: '{model_basename}'")
        print(f"[BaseRetrainer Debug] settings.MODEL_ROOT: '{settings.MODEL_ROOT}'")
        print(f"[BaseRetrainer Debug] Constructed original_model_path: '{self.original_model_path}'")

        if not os.path.exists(self.original_model_path):
            # For clarity, log the FileField's default path (based on MEDIA_ROOT)
            file_field_default_path = "N/A (model_file attribute missing or no path method)"
            if hasattr(self.algorithm.model_file, 'path'):
                 file_field_default_path = self.algorithm.model_file.path
            
            error_msg = (
                f"Original model file not found at derived MODEL_ROOT path: '{self.original_model_path}'. "
                f"FileField's default path (using MEDIA_ROOT) would be: '{file_field_default_path}'."
            )
            print(f"[BaseRetrainer Error] {error_msg}")
            raise FileNotFoundError(error_msg)
        
        print(f"Retrainer initialized for Algorithm ID: {self.algorithm.id}, Path from MODEL_ROOT: {self.original_model_path}")

    def _get_combined_data_for_retraining(self) -> tuple:
        """
        Fetches data from the Backend service's export API,
        transforms it into a suitable DataFrame, and then preprocesses it.
        """
        print("Fetching combined dataset for retraining via Backend API...")
        backend_export_url = getattr(settings, 'BACKEND_DATA_EXPORT_URL', None)
        if not backend_export_url:
            backend_export_url = 'http://backend:8000/claims/api/export/'
            print(f"Warning: BACKEND_DATA_EXPORT_URL not found in MLaaS settings. Using default: {backend_export_url}")
        if not backend_export_url:
            raise RetrainingError("Backend data export URL is not configured or found.")

        try:
            print(f"Calling Backend API at: {backend_export_url}")
            response = requests.get(backend_export_url, timeout=180)
            response.raise_for_status()
            claims_data_from_api = response.json()
            if not claims_data_from_api:
                raise RetrainingError("No data received from Backend data export API or data is empty.")

            flattened_data_list = []
            for claim_export_item in claims_data_from_api:
                current_flat_item = {}
                for k, v in claim_export_item.items():
                    if k not in ['accident', 'driver', 'vehicle', 'injury', 'id', 'prediction_result']:
                        transformed_key = k.replace('_', '')
                        current_flat_item[transformed_key] = v
                nested_sources = ['accident', 'driver', 'vehicle', 'injury']
                for source_key in nested_sources:
                    nested_dict = claim_export_item.get(source_key)
                    if isinstance(nested_dict, dict):
                        for k, v in nested_dict.items():
                            if k != 'id' and not k.endswith("_id"):
                                transformed_key = k.replace('_', '')
                                current_flat_item[transformed_key] = v
                flattened_data_list.append(current_flat_item)

            if not flattened_data_list:
                raise RetrainingError("Data fetched from Backend API resulted in an empty list after flattening.")

            raw_df_for_mlaas = pd.DataFrame(flattened_data_list)
            raw_df_for_mlaas.columns = raw_df_for_mlaas.columns.str.lower()
            new_column_names = [col.replace('_', '') for col in raw_df_for_mlaas.columns]
            raw_df_for_mlaas.columns = new_column_names
            print(f"Successfully transformed {len(raw_df_for_mlaas)} records from Backend API into DataFrame.")
            print(f"DataFrame columns AFTER renaming (before MLaaS preprocessing): {raw_df_for_mlaas.columns.tolist()}")
            if raw_df_for_mlaas.empty:
                raise RetrainingError("DataFrame created from Backend API data is empty.")

        except requests.exceptions.RequestException as e:
            detailed_error = f"Failed to fetch/process training data from Backend API ({backend_export_url}): {e}."
            if hasattr(e, 'response') and e.response is not None:
                detailed_error += f" Status: {e.response.status_code}. Response text: {e.response.text[:500]}"
            print(detailed_error)
            raise RetrainingError(detailed_error)
        except ValueError as e:
            raise RetrainingError(f"Failed to decode JSON or process data from Backend API: {e}")
        except Exception as e:
            print(f"Unexpected error during data fetching/preparation: {e}")
            traceback.print_exc()
            raise RetrainingError(f"Unexpected error during MLaaS data fetching: {e}")

        try:
            X_processed, y_processed = _preprocess_raw_dataframe_for_retraining(raw_df_for_mlaas)
        except Exception as e:
            print(f"Error during MLaaS preprocessing of data from Backend API: {e}")
            traceback.print_exc()
            raise RetrainingError(f"Data preprocessing failed in MLaaS: {e}")

        if X_processed.empty or y_processed.empty:
            raise RetrainingError("MLaaS preprocessing resulted in no valid data points from API data.")
        if X_processed.shape[0] != y_processed.shape[0]:
            raise RetrainingError(f"Mismatch in feature ({X_processed.shape[0]}) and target ({y_processed.shape[0]}) counts after MLaaS preprocessing.")

        return X_processed, y_processed

    def _generate_new_version_string(self):
        """Generates an incremented version string (e.g., 1.0.0 -> 1.0.1)."""
        current_version = self.algorithm.version
        parts = current_version.split('.')
        try:
            if len(parts) > 0:
                # Increment the last part if it's numeric
                parts[-1] = str(int(parts[-1]) + 1)
                return '.'.join(parts)
            else:
                # Fallback for simple version strings
                return f"{current_version}_retrained_{datetime.now().strftime('%Y%m%d')}"
        except (ValueError, IndexError):
             # Fallback if last part isn't an integer or other issues
            return f"{current_version}_retrained_{datetime.now().strftime('%Y%m%d%H%M')}"

    def _save_new_version(self, trained_model, new_version_str):
        # Define New File Path using MODEL_ROOT
        # model_dir = os.path.join(settings.MEDIA_ROOT, 'ml_models') # OLD, used MEDIA_ROOT
        model_dir = settings.MODEL_ROOT # NEW, use MODEL_ROOT directly
        os.makedirs(model_dir, exist_ok=True) # Ensure directory exists

        # Clean base name (remove potential old version markers from the original path's basename)
        original_basename_for_new_file = os.path.splitext(os.path.basename(self.original_model_path))[0] # Use basename of the path we loaded from
        base_name_parts = original_basename_for_new_file.split('_v')
        clean_base_name = base_name_parts[0]

        # Create new filename
        new_model_filename = f"{clean_base_name}_v{new_version_str.replace('.', '_')}.pkl"
        new_model_full_path = os.path.join(model_dir, new_model_filename) # Path in MODEL_ROOT

        # Save Model File
        print(f"Saving retrained model version {new_version_str} to {new_model_full_path} (in MODEL_ROOT)...")
        try:
            joblib.dump(trained_model, new_model_full_path)
        except Exception as e:
            print(f"Error saving model file to MODEL_ROOT: {e}")
            traceback.print_exc()
            raise RetrainingError(f"Failed to save retrained model file to MODEL_ROOT: {e}")

        # Create Database Record
        print(f"Creating new MLAlgorithm database record for version {new_version_str}...")
        # The MLAlgorithm.model_file field is a FileField.
        new_model_db_path_representation = os.path.join('ml_models', new_model_filename)


        try:
            with transaction.atomic():
                new_algorithm = MLAlgorithm.objects.create(
                    name=self.algorithm.name,
                    description=f"{self.algorithm.description} (Retrained on {datetime.now().isoformat()})",
                    version=new_version_str,
                    code=self.algorithm.code,
                    model_type=self.algorithm.model_type,
                    parent_endpoint=self.algorithm.parent_endpoint,
                    model_file=new_model_db_path_representation, # This is the string stored in DB
                    is_active=False # New retrained models are not active by default
                )
            print(f"Successfully created new algorithm record ID: {new_algorithm.id} with model_file='{new_model_db_path_representation}'")
            return new_algorithm
        except Exception as e:
            # If DB creation fails, attempt to clean up the saved model file
            print(f"Error creating database record: {e}")
            traceback.print_exc()
            if os.path.exists(new_model_full_path):
                try:
                    os.remove(new_model_full_path)
                    print(f"Cleaned up saved model file due to DB error: {new_model_full_path}")
                except OSError as cleanup_error:
                    # Log cleanup error but prioritize reporting the original DB error
                    print(f"Warning: Error during cleanup of model file {new_model_full_path}: {cleanup_error}")
            raise RetrainingError(f"Failed to create new MLAlgorithm database record: {e}")

    @abc.abstractmethod
    def _fit_model(self, model, X_combined, y_combined):
        """
        Fits the model instance using the combined dataset.
        Must be implemented by concrete subclasses.

        Args:
            model: The loaded model object (with original hyperparameters).
            X_combined (pd.DataFrame): Processed feature matrix.
            y_combined (pd.Series): Processed target vector.

        Returns:
            The fitted model object.
        Raises:
            RetrainingError: If fitting fails.
        """
        pass

    def retrain(self):
        """
        Orchestrates the full retraining process:
        1. Fetch and preprocess the combined dataset.
        2. Load the existing model architecture/hyperparameters.
        3. Fit the model from scratch on the combined data.
        4. Save the new model version and create its DB record.

        Returns:
            tuple: (MLAlgorithm: new_algorithm_instance, dict: results_summary)
                   Returns (None, results_summary) if no data found.
        Raises:
            RetrainingError: If any critical step fails.
            EnvironmentError: If DB access fails.
            FileNotFoundError: If the original model file is missing.
        """
        retrain_start_time = time.time()
        print(f"--- Starting Retraining Workflow ---")
        print(f"Algorithm ID: {self.algorithm.id}, Type: {self.algorithm.get_model_type_display()}, Version: {self.algorithm.version}")

        # Get & Preprocess Combined Data 
        data_start_time = time.time()
        X_combined, y_combined = self._get_combined_data_for_retraining()
        preprocess_time = time.time() - data_start_time
        if X_combined.empty:
            # Handle case where preprocessing yields no data (already logged inside)
             results = {"message": "Preprocessing resulted in no valid data points. Retraining aborted.", "status": "no_data"}
             return None, results # Return None for algorithm, indicate status

        print(f"Data fetching & preprocessing completed in {preprocess_time:.4f}s")
        print(f"Combined dataset shape: X={X_combined.shape}, y={y_combined.shape}")


        #  Load Existing Model Structure/Hyperparams 
        load_start_time = time.time()
        try:
            # Path existence already checked in __init__
            model = joblib.load(self.original_model_path)
            print(f"Loaded existing model structure/hyperparams from: {self.original_model_path}")
        except Exception as e:
            print(f"Error loading original model file: {e}")
            traceback.print_exc()
            raise RetrainingError(f"Failed to load original model: {e}")
        load_time = time.time() - load_start_time

        # Fit Model From Scratch (using subclass logic) 
        fit_start_time = time.time()
        fitted_model = self._fit_model(model, X_combined, y_combined)
        fit_time = time.time() - fit_start_time
        print(f"Model fitting completed in {fit_time:.4f} seconds.")

        # Save New Version (File & DB) 
        save_start_time = time.time()
        new_version_str = self._generate_new_version_string()
        new_algorithm_instance = self._save_new_version(fitted_model, new_version_str)
        save_time = time.time() - save_start_time

        # Final Summary 
        total_time = time.time() - retrain_start_time
        print(f"--- Retraining Workflow Completed Successfully ---")
        print(f"Total time: {total_time:.4f}s")

        results = {
            "message": "Retraining successful. New model version created.",
            "status": "success",
            "new_algorithm_id": new_algorithm_instance.id,
            "new_version": new_algorithm_instance.version,
            "data_points_used": X_combined.shape[0],
            "features_count": X_combined.shape[1],
            "preprocess_time_seconds": round(preprocess_time, 4),
            "load_time_seconds": round(load_time, 4),
            "fit_time_seconds": round(fit_time, 4),
            "save_time_seconds": round(save_time, 4),
            "total_time_seconds": round(total_time, 4),
        }
        return new_algorithm_instance, results


class RandomForestRetrainer(BaseRetrainer):
    """Retraining logic specific to RandomForest models."""
    def _fit_model(self, model, X_combined, y_combined):
        """Fits the RandomForest model from scratch on the combined data."""
        print("Fitting RandomForest model...")
        try:
            # model.fit() retrains the RF entirely using existing hyperparameters
            model.fit(X_combined, y_combined)
            # For scikit-learn, fit modifies in-place and returns self
            return model
        except Exception as e:
            print(f"Error during RandomForest fitting: {e}")
            traceback.print_exc()
            raise RetrainingError(f"RandomForest fitting failed: {e}")


class XGBoostRetrainer(BaseRetrainer):
    """Retraining logic specific to XGBoost models."""
    def _fit_model(self, model, X_combined, y_combined):
        """Fits the XGBoost model from scratch on the combined data."""
        print("Fitting XGBoost model...")
        try:
            # model.fit() for XGBoost also typically retrains from scratch
            # using the hyperparameters stored in the loaded model object.
            model.fit(X_combined, y_combined)
            return model
        except Exception as e:
            print(f"Error during XGBoost fitting: {e}")
            traceback.print_exc()
            raise RetrainingError(f"XGBoost fitting failed: {e}")


def get_retrainer(algorithm_instance: MLAlgorithm):
    """
    Factory function to return the appropriate retrainer class instance
    based on the algorithm's model_type.

    Args:
        algorithm_instance: The MLAlgorithm instance to retrain.

    Returns:
        An instance of a BaseRetrainer subclass.
    Raises:
        NotImplementedError: If no retrainer is defined for the algorithm's model_type.
        TypeError: If algorithm_instance is not valid.
        ValueError: If algorithm lacks a model file.
        FileNotFoundError: If model file is missing.
    """
    # Initial checks are now handled in BaseRetrainer.__init__
    model_type = algorithm_instance.model_type

    if model_type == 'RANDOM_FOREST':
        return RandomForestRetrainer(algorithm_instance)
    elif model_type == 'XGBOOST':
        return XGBoostRetrainer(algorithm_instance)
    # Add 'elif' blocks for other supported model types if needed in the future
    else:
        raise NotImplementedError(f"Retraining is not implemented for model type: '{model_type}'")