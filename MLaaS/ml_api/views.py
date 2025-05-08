# ml_api/views.py

import logging
import os
import time
import traceback
import joblib
import numpy as np
import matplotlib.pyplot as plt
import shap
import io
import pandas as pd
import base64
from django.conf import settings  
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from shap import LinearExplainer, KernelExplainer
from rest_framework.permissions import AllowAny

from sklearn.linear_model import LinearRegression, LogisticRegression

# Import logic and CUSTOM exceptions from the retraining module
from .retraining_logic import ( 
    RetrainingError,
    get_retrainer,
)
from .models import Endpoint, MLAlgorithm, MLRequest
from .serializers import (
    AlgorithmPredictInputSerializer,
    EndpointSerializer,
    MLAlgorithmSerializer,
    MLRequestSerializer,
)

# Configure logging
logger = logging.getLogger(__name__)

class EndpointViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing logical ML Endpoints.

    Provides standard CRUD operations (Create, Retrieve, Update, Destroy)
    for Endpoint resources. Requires authentication (currently set to AllowAny).
    """

    queryset = Endpoint.objects.all().order_by("name")  # Queryset for all endpoints ordered by name
    serializer_class = EndpointSerializer  # Serializer for endpoint data
    # Keep AllowAny for debugging, remember to switch back later
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.AllowAny]  # Allow any user for now

class MLAlgorithmViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing ML Algorithms.

    Provides CRUD operations for MLAlgorithm resources. Also includes custom
    actions for making predictions (`/predict/`) and triggering model
    retraining (`/retrain/`). Requires authentication (currently set to AllowAny).
    """

    queryset = MLAlgorithm.objects.all().order_by("-created_at")  # Show newest first
    serializer_class = MLAlgorithmSerializer  # Serializer for ML algorithm data
    # Keep AllowAny for debugging, remember to switch back later 
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.AllowAny]  # Allow any user for now

    # --- Standard ViewSet Methods ---

    def perform_create(self, serializer):
        """Customises behaviour after creating an MLAlgorithm instance."""
        instance = serializer.save()  # Save the new instance
        logger.info(
            "ML Algorithm '%s' (ID: %d, Version: %s) created via API.",
            instance.name,
            instance.id,
            instance.version,
        )

    def perform_update(self, serializer):
        """Customises behaviour after updating an MLAlgorithm instance."""
        instance = serializer.save()  # Save the updated instance
        logger.info(
            "ML Algorithm '%s' (ID: %d, Version: %s) updated via API.",
            instance.name,
            instance.id,
            instance.version,
        )

    def perform_destroy(self, instance):
        """
        Customises behaviour when deleting an MLAlgorithm instance.

        Logs the deletion and attempts to delete the model file relative to BASE_DIR.
        """
        algorithm_id = instance.id  # Get the algorithm ID
        algorithm_name = instance.name  # Get the algorithm name
        model_file_rel_path = None  # Initialise variable for model file path
        model_file_abs_path = None  # Initialise variable for absolute model file path

        # Get the relative path stored in the DB
        if instance.model_file and hasattr(instance.model_file, "name"):
            model_file_rel_path = instance.model_file.name  # Get the relative path

        # Try to construct the absolute path for deletion check
        if model_file_rel_path:
            try:
                model_file_abs_path = os.path.join(settings.BASE_DIR, model_file_rel_path)  # Construct absolute path
            except Exception as e:
                logger.warning(
                    "Could not construct absolute path for Algorithm ID %d: %s",
                    algorithm_id, e
                )

        # Delete DB record first
        try:
            instance.delete()  # Delete the instance from the database
            logger.info(
                "ML Algorithm '%s' (ID: %d) deleted from DB.",
                algorithm_name, algorithm_id
            )
        except Exception as db_error:
            logger.error(
                "Error deleting ML Algorithm '%s' (ID: %d) from DB: %s",
                algorithm_name, algorithm_id, db_error
            )
            
        # Attempt to delete the physical file using the absolute path
        if model_file_abs_path and os.path.exists(model_file_abs_path):
            try:
                os.remove(model_file_abs_path)  # Remove the model file
                logger.info(
                    "Associated model file deleted: %s", model_file_abs_path
                )
            except OSError as e:
                logger.warning(
                    "Error deleting model file %s for Algorithm ID %d: %s",
                    model_file_abs_path, algorithm_id, e
                )
        elif model_file_rel_path and (not model_file_abs_path or not os.path.exists(model_file_abs_path)):
            # Log if path was expected but not found or couldn't be constructed
             logger.warning(
                "Model file path '%s' was associated with Algorithm ID %d, "
                "but file was not found at calculated absolute path '%s' for deletion.",
                 model_file_rel_path, algorithm_id, model_file_abs_path
            )

    # --- Custom Actions ---

    @action(
        detail=True,
        methods=["post"],
        url_path="predict",
        serializer_class=AlgorithmPredictInputSerializer,
    )
    def predict(self, request, pk=None):
        """
        Perform prediction using a specific ML algorithm version.

        Loads model file based on relative path stored in DB joined with BASE_DIR.
        """
        try:
            algorithm = MLAlgorithm.objects.select_related("parent_endpoint").get(
                pk=pk  # Get the algorithm by primary key
            )
        except MLAlgorithm.DoesNotExist:  # Use specific exception from model
            logger.warning("Prediction failed: Algorithm with ID %s not found.", pk)
            return Response(
                {"error": f"Algorithm with ID {pk} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(data=request.data)  # Validate input data
        if not serializer.is_valid():
            logger.warning(
                "Prediction failed for Algorithm ID %s: Invalid input data. Errors: %s",
                pk, serializer.errors
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # --- Get relative path from DB ---
        model_file_rel_path = None
        if algorithm.model_file and hasattr(algorithm.model_file, 'name'):
            model_file_rel_path = algorithm.model_file.name  # Get the model file path

        if not model_file_rel_path:
            logger.error("Prediction failed: No model file path registered in DB for Algorithm ID %s.", pk)
            return Response(
                {"error": f"No model file path found in database for algorithm ID {pk}."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Indicate internal config issue
            )

        # --- Construct absolute path and check existence ---
        try:
            model_file_abs_path = os.path.join(settings.BASE_DIR, model_file_rel_path)  # Construct absolute path
            if not os.path.exists(model_file_abs_path):
                logger.error(
                    "Prediction failed: Model file for Algorithm ID %s not found "
                    "at expected absolute path: %s", pk, model_file_abs_path
                )
                return Response(
                    {
                        "error": f"Model file not found or inaccessible at calculated path "
                                 f"'{model_file_abs_path}' for algorithm ID {pk}. Cannot predict."
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,  # Service unavailable as model file missing
                )
        except Exception as path_error:
            logger.error(
                "Prediction failed: Error constructing/checking model file path for Algorithm ID %s. Rel path: '%s'. Error: %s",
                 pk, model_file_rel_path, path_error, exc_info=True
            )
            return Response(
                 {"error": f"Server error determining model file location for algorithm ID {pk}."},
                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # --- Load model using absolute path ---
        try:
            load_start = time.time()  # Start timer for loading model
            model = joblib.load(model_file_abs_path)  # Load the model
            load_time = time.time() - load_start  # Calculate load time
            logger.info(
                "Loaded model for Algorithm ID %s from '%s' in %.4fs",
                pk, model_file_abs_path, load_time
            )

            # --- Prediction logic  ---
            input_data = np.array(serializer.validated_data["input_data"])  # Prepare input data

            expected_features = getattr(model, "n_features_in_", None)  # Get expected number of features
            if expected_features is not None and input_data.shape[1] != expected_features:
                error_msg = (
                    f"Input data shape mismatch: received {input_data.shape[1]} features, "
                    f"but model expects {expected_features}."
                )
                logger.warning(
                    "Prediction failed for Algorithm ID %s: %s", pk, error_msg
                )
                return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)

            predict_start = time.time()  # Start timer for prediction
            prediction = model.predict(input_data)  # Perform prediction
            predict_time = time.time() - predict_start  # Calculate prediction time

            prediction_list = (
                prediction.tolist()
                if isinstance(prediction, np.ndarray)
                else prediction
            )
            response_time_secs = load_time + predict_time  # Total processing time

            # --- Logging request  ---
            ml_request = None
            try:
                ml_request = MLRequest.objects.create(
                    input_data=serializer.validated_data["input_data"],
                    prediction=prediction_list,
                    algorithm=algorithm,
                    response_time=response_time_secs,
                )
                response_data = {
                    "prediction": prediction_list,
                    "request_id": ml_request.id,
                    "algorithm_version": algorithm.version,
                    "processing_time_ms": round(response_time_secs * 1000, 2),
                }
                logger.info(
                    "Prediction successful for Algorithm ID %s. Request ID: %d. Time: %.4fs",
                    pk, ml_request.id, response_time_secs
                )
                return Response(response_data, status=status.HTTP_200_OK)
            except Exception as db_error:
                logger.critical(
                    "Error saving MLRequest log for algorithm %s (ID: %s): %s",
                    algorithm.name, pk, db_error, exc_info=True
                )
                response_data = {
                    "prediction": prediction_list,
                    "warning": "Prediction successful, but failed to log request details.",
                    "algorithm_version": algorithm.version,
                    "processing_time_ms": round(response_time_secs * 1000, 2),
                }
                return Response(response_data, status=status.HTTP_200_OK)

        # --- Specific Error Handling for Prediction Process ---
        except FileNotFoundError:  # Should be caught by os.path.exists check, but handle defensively
            logger.error(
                "Prediction failed: Model file disappeared between check and load: %s",
                model_file_abs_path, exc_info=True  # Log absolute path
            )
            return Response(
                {
                    "error": f"Model file became inaccessible during prediction process: "
                             f"{model_file_abs_path}."  # Report absolute path
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except ValueError as ve:  # Input data format/shape errors
            logger.error(
                "Prediction ValueError for Algorithm ID %s: %s", pk, ve, exc_info=True
            )
            return Response(
                {
                    "error": f"Prediction failed due to invalid input data format or "
                             f"shape for the loaded model: {str(ve)}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except (AttributeError, TypeError) as te:  # Model incompatibility
            logger.error(
                "Prediction TypeError/AttributeError for Algorithm ID %s: %s", pk, te, exc_info=True
            )
            return Response(
                {
                    "error": f"Prediction failed due to model incompatibility or "
                             f"internal error: {str(te)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:  # Other unexpected errors
            logger.error(
                "Unexpected prediction error for Algorithm ID %s: %s", pk, e, exc_info=True
            )
            return Response(
                {
                    "error": "An unexpected server error occurred during prediction."
                             f" Details: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # --- Retrain method remains the same ---
    @action(detail=True, methods=["post"], url_path="retrain")
    def retrain(self, request, pk=None):
        """Handles POST request to trigger retraining for a specific algorithm ID."""
        try:
            algorithm_to_retrain = self.get_object()  # Get the algorithm instance
        except ObjectDoesNotExist:
            logger.warning("Retraining trigger failed: Algorithm with ID %s not found.", pk)
            return Response(
                {"error": f"Algorithm with ID {pk} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        logger.info(
            "Received request to retrain Algorithm ID: %s (Type: %s, Version: %s)",
            pk,
            algorithm_to_retrain.get_model_type_display(),
            algorithm_to_retrain.version,
        )

        try:
            retrainer = get_retrainer(algorithm_to_retrain)  # Get retrainer for the algorithm
            new_algorithm_instance, results = retrainer.retrain()  # Perform retraining

            if results.get("status") == "no_data":
                logger.info(
                    "Retraining for Algorithm ID %s resulted in no action: %s",
                    pk, results.get('message')
                )
                return Response(results, status=status.HTTP_200_OK)

            new_serializer = self.get_serializer(new_algorithm_instance)  # Serialize new algorithm instance
            response_data = {
                "message": results.get(
                    "message", "Retraining process completed successfully."
                ),
                "new_algorithm": new_serializer.data,
                "metrics": {
                    k: v
                    for k, v in results.items()
                    if k.endswith("_seconds") or k.startswith("data_points")
                },
            }
            logger.info(
                "Retraining successful for Algorithm ID %s. New version created: %s (ID: %d)",
                pk, new_algorithm_instance.version, new_algorithm_instance.id
            )
            return Response(response_data, status=status.HTTP_201_CREATED)

        except FileNotFoundError as e:
            logger.error(
                "Retraining failed for Algorithm ID %s. Error: %s: %s",
                pk, type(e).__name__, e, exc_info=True
            )
            return Response(
                {"error": f"Retraining failed: Required file not found - {str(e)}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except NotImplementedError as e:
            logger.error(
                "Retraining failed for Algorithm ID %s. Error: %s: %s",
                pk, type(e).__name__, e, exc_info=True
            )
            return Response(
                {"error": f"Retraining failed: Not implemented for this algorithm type - {str(e)}"},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        except EnvironmentError as e:
            logger.error(
                "Retraining failed for Algorithm ID %s. Error: %s: %s",
                pk, type(e).__name__, e, exc_info=True
            )
            return Response(
                {"error": f"Retraining failed: Environment error (e.g., DB access) - {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except RetrainingError as e:
            logger.error(
                "Retraining failed for Algorithm ID %s. Error: %s: %s",
                pk, type(e).__name__, e, exc_info=True
            )
            return Response(
                {"error": f"Retraining failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.error(
                "Unexpected error during retraining trigger for Algorithm ID %s: %s",
                pk, e, exc_info=True
            )
            return Response(
                {
                    "error": "An unexpected server error occurred during the "
                             f"retraining request: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class MLRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing ML prediction request logs.

    Provides read-only access (List, Retrieve) to MLRequest resources.
    Supports filtering based on related algorithm and endpoint fields.
    Requires authentication (currently set to AllowAny).
    """

    queryset = MLRequest.objects.all().select_related(
        'algorithm', 'algorithm__parent_endpoint'
    ).order_by("-created_at")  # Order by creation date
    serializer_class = MLRequestSerializer  # Serializer for ML request data
    # Keep AllowAny for debugging, remember to switch back
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.AllowAny]  # Allow any user for now

    filterset_fields = [
        "algorithm__id",  # Filter by algorithm ID
        "algorithm__name",  # Filter by algorithm name
        "algorithm__version",  # Filter by algorithm version
        "algorithm__model_type",  # Filter by algorithm model type
        "algorithm__parent_endpoint__id",  # Filter by parent endpoint ID
        "algorithm__parent_endpoint__name",  # Filter by parent endpoint name
    ]
    search_fields = ["input_data", "prediction"]  # Fields to search in

    @action(detail=True, methods=['get'], url_path='explain')
    def explain(self, request, pk=None):
        """
        Provides SHAP explanations for a specific prediction request.

        Loads the model and input data, then generates SHAP values and plots.
        """
        ml_req = self.get_object()  # Get the ML request object
        df = pd.DataFrame(ml_req.input_data)  # Convert input data to DataFrame

        # Build path under your MODEL_ROOT
        filename = os.path.basename(ml_req.algorithm.model_file.name)  # Get model file name
        model_fp = os.path.join(settings.MODEL_ROOT, filename)  # Construct model file path
        if not os.path.exists(model_fp):
            return Response(
                {"error": f"Model file not found at {model_fp}."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        model = joblib.load(model_fp)  # Load the model

        try:
            explainer = shap.Explainer(model, df)  # Create SHAP explainer
            shap_out = explainer(df)  # Generate SHAP values
            plt.figure()  # Create a new figure
            shap.plots.bar(shap_out, show=False)  # Create SHAP bar plot
            importances = np.abs(shap_out.values).mean(axis=0)  # Calculate feature importances
        except Exception:
            # Fallback to coef_ or feature_importances_
            if hasattr(model, "coef_"):
                importances = np.abs(model.coef_).ravel()  # Get coefficients
            elif hasattr(model, "feature_importances_"):
                importances = model.feature_importances_  # Get feature importances
            else:
                return Response(
                    {"error": "Could not compute SHAP or fallback importances."},
                    status=status.HTTP_501_NOT_IMPLEMENTED
                )
            plt.figure()  # Create a new figure
            plt.bar(df.columns.astype(str), importances)  # Create bar plot for importances
            plt.xticks(rotation=45, ha="right")  # Rotate x-axis labels
            plt.ylabel("importance")  # Y-axis label

        buf = io.BytesIO()  # Create a buffer for the plot
        plt.tight_layout()  # Adjust layout
        plt.savefig(buf, format="png")  # Save plot to buffer
        plt.close()  # Close the plot
        buf.seek(0)  # Reset buffer position
        img_b64 = base64.b64encode(buf.read()).decode("utf-8")  # Encode plot as base64

        top5 = sorted(
            zip(importances, df.columns),  # Pair importances with feature names
            key=lambda x: x[0], reverse=True  # Sort by importance
        )[:5]  # Get top 5 features
        top_feats = [{"feature": str(col), "importance": float(val)} for val, col in top5]  # Prepare top features list

        return Response({
            "request_id": ml_req.pk,  # Return request ID
            "algorithm": ml_req.algorithm.name,  # Return algorithm name
            "prediction": ml_req.prediction,  # Return prediction result
            "shap_image": img_b64,  # Return SHAP image
            "top_features": top_feats,  # Return top features
        })

@api_view(['GET'])
@permission_classes([AllowAny])
def engineer_list_models(request):
    """
    Lists all MLAlgorithms, intended for the engineer's dashboard or similar.
    """
    algorithms = MLAlgorithm.objects.all().order_by('-created_at')
    serializer = MLAlgorithmSerializer(algorithms, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def engineer_set_active_model(request):
    """Set a model as active (by id) and deactivate others with the same name/endpoint."""
    model_id = request.data.get('model_id')
    if not model_id:
        return Response({'error': 'No model_id provided'}, status=400)
    try:
        model = MLAlgorithm.objects.get(pk=model_id)
        # Deactivate all models with the same name and parent_endpoint
        MLAlgorithm.objects.filter(name=model.name, parent_endpoint=model.parent_endpoint).update(is_active=False)
        model.is_active = True
        model.save()
        return Response({'success': True, 'active_model_id': model.id})
    except MLAlgorithm.DoesNotExist:
        return Response({'error': 'Model not found'}, status=404)