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

# Local imports (ensure these paths are correct for your structure)
from .models import MLAlgorithm
from .preprocessing import preprocess_data_from_queryset # Import the adapted preprocessor

# --- Data Fetching Dependency ---
# Assumes this ML API service shares the same DB/environment as 'claims' app.
try:
    from claims.models import Claim
    CAN_ACCESS_CLAIMS_DB = True
except ImportError:
    Claim = None
    CAN_ACCESS_CLAIMS_DB = False
# --- End Data Fetching Dependency ---


class RetrainingError(Exception):
    """Custom exception for specific retraining failures."""
    pass


# --- Base Retrainer Class (Abstract) ---
class BaseRetrainer(abc.ABC):
    """Abstract base class for model retraining strategies."""

    def __init__(self, algorithm_instance: MLAlgorithm):
        """
        Initializes the retrainer with the algorithm instance to be updated.

        Args:
            algorithm_instance: The MLAlgorithm object representing the model
                                version to be retrained.
        Raises:
            TypeError: If algorithm_instance is not an MLAlgorithm object.
            ValueError: If the algorithm instance lacks a valid model file path.
            FileNotFoundError: If the model file path exists in the DB record
                               but the file is not found on the filesystem.
        """
        if not isinstance(algorithm_instance, MLAlgorithm):
            raise TypeError("algorithm_instance must be an MLAlgorithm object.")
        self.algorithm = algorithm_instance
        self.original_model_path = None

        # Validate model file path and existence
        if self.algorithm.model_file and hasattr(self.algorithm.model_file, 'path'):
            self.original_model_path = self.algorithm.model_file.path
            if not os.path.exists(self.original_model_path):
                print(f"Error: Original model file not found at path: {self.original_model_path}")
                raise FileNotFoundError(f"Original model file not found at {self.original_model_path}")
        else:
            raise ValueError("Algorithm instance provided has no valid model file path.")
        print(f"Retrainer initialized for Algorithm ID: {self.algorithm.id}, Path: {self.original_model_path}")

    def _get_combined_data_for_retraining(self):
        """
        Fetches ALL relevant data from the 'claims' DB using the ORM
        and preprocesses it using the dedicated preprocessing module.

        Returns:
            tuple: (pd.DataFrame: Processed features X, pd.Series: Processed target y)
        Raises:
            EnvironmentError: If 'claims' DB models cannot be accessed.
            RetrainingError: If preprocessing fails or returns no valid data.
        """
        if not CAN_ACCESS_CLAIMS_DB:
            raise EnvironmentError("Cannot access 'claims' database models. Retraining aborted.")

        print("Fetching combined dataset for retraining...")
        # Fetch ALL data deemed relevant for training the model from scratch
        # Add specific filters here if necessary (e.g., exclude outliers, specific date ranges)
        try:
            claims_queryset = Claim.objects.select_related(
                'accident', 'accident__driver', 'accident__vehicle', 'accident__injury'
            ).all() # Modify this query as needed
            print(f"Retrieved {claims_queryset.count()} potential claim records from DB.")
        except Exception as e:
             raise RetrainingError(f"Database error during data fetching: {e}")

        # Delegate preprocessing
        try:
            X_processed, y_processed = preprocess_data_from_queryset(claims_queryset)
        except Exception as e:
            print(f"Error during preprocessing: {e}")
            traceback.print_exc()
            raise RetrainingError(f"Data preprocessing failed: {e}")

        if X_processed.empty or y_processed.empty:
            raise RetrainingError("Preprocessing resulted in no valid data points.")
        if X_processed.shape[0] != y_processed.shape[0]:
             raise RetrainingError(f"Mismatch in feature ({X_processed.shape[0]}) and target ({y_processed.shape[0]}) counts after preprocessing.")

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
        """
        Saves the retrained model file to a new path and creates the
        corresponding MLAlgorithm database record within a transaction.

        Args:
            trained_model: The newly fitted model object.
            new_version_str: The generated version string for the new model.

        Returns:
            MLAlgorithm: The newly created database instance.
        Raises:
            RetrainingError: If saving the file or creating the DB record fails.
        """
        # Define New File Path 
        model_dir = os.path.join(settings.MEDIA_ROOT, 'ml_models')
        os.makedirs(model_dir, exist_ok=True) # Ensure directory exists

        # Clean base name (remove potential old version markers)
        original_basename = os.path.splitext(os.path.basename(self.original_model_path))[0]
        base_name_parts = original_basename.split('_v')
        clean_base_name = base_name_parts[0]

        # Create new filename
        new_model_filename = f"{clean_base_name}_v{new_version_str.replace('.', '_')}.pkl"
        new_model_full_path = os.path.join(model_dir, new_model_filename)

        # Save Model File
        print(f"Saving retrained model version {new_version_str} to {new_model_full_path}...")
        try:
            joblib.dump(trained_model, new_model_full_path)
        except Exception as e:
            print(f"Error saving model file: {e}")
            traceback.print_exc()
            raise RetrainingError(f"Failed to save retrained model file: {e}")

        # Create Database Record 
        print(f"Creating new MLAlgorithm database record for version {new_version_str}...")
        new_model_db_path = os.path.join('ml_models', new_model_filename) # Relative path for DB field

        try:
            # Use atomic transaction for DB safety
            with transaction.atomic():
                new_algorithm = MLAlgorithm.objects.create(
                    name=self.algorithm.name, # Keep the same logical name
                    description=f"{self.algorithm.description} (Retrained on {datetime.now().isoformat()})",
                    version=new_version_str,
                    code=self.algorithm.code, # Copy code/metadata if any
                    model_type=self.algorithm.model_type, # Critical: copy type
                    parent_endpoint=self.algorithm.parent_endpoint,
                    model_file=new_model_db_path # Assign the relative file path
                    # Set is_active=True if using that flag
                )
                # Optional: Deactivate the old version within the same transaction
                # if hasattr(self.algorithm, 'is_active'):
                #     self.algorithm.is_active = False
                #     self.algorithm.save(update_fields=['is_active'])

            print(f"Successfully created new algorithm record ID: {new_algorithm.id}")
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