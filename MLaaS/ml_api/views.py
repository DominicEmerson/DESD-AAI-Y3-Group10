# ml_api/views.py

import os
import time
import traceback
import joblib
import numpy as np

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Endpoint, MLAlgorithm, MLRequest
from .serializers import (
    EndpointSerializer,
    MLAlgorithmSerializer, # Ensure this includes model_type field
    MLRequestSerializer,
    AlgorithmPredictInputSerializer, # Use the specific input serializer
)
# Import logic and exceptions from the retraining module
from .retraining_logic import get_retrainer, RetrainingError


class EndpointViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing logical ML Endpoints.
    Provides standard CRUD operations.
    """
    queryset = Endpoint.objects.all().order_by('name')
    serializer_class = EndpointSerializer
    permission_classes = [permissions.IsAuthenticated] # Requires user to be logged in


class MLAlgorithmViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing ML Algorithms.
    Provides CRUD operations for algorithms, plus custom actions
    for prediction and triggering retraining.
    """
    queryset = MLAlgorithm.objects.all().order_by('-created_at') # Show newest first
    serializer_class = MLAlgorithmSerializer # Make sure this includes model_type
    permission_classes = [permissions.IsAuthenticated] # Add role-based permissions if needed

    # --- Standard ViewSet Methods ---

    def perform_create(self, serializer):
        """Logs algorithm creation when using POST request."""
        instance = serializer.save()
        print(f"ML Algorithm '{instance.name}' (ID: {instance.id}, Version: {instance.version}) created via API.")

    def perform_update(self, serializer):
        """Logs algorithm update when using PUT/PATCH request."""
        instance = serializer.save()
        print(f"ML Algorithm '{instance.name}' (ID: {instance.id}, Version: {instance.version}) updated via API.")

    def perform_destroy(self, instance):
        """Logs deletion and attempts to delete the associated model file when using DELETE request."""
        algorithm_id = instance.id
        algorithm_name = instance.name
        model_path = None
        # Safely check for path attribute before accessing it
        if instance.model_file and hasattr(instance.model_file, 'path'):
            model_path = instance.model_file.path

        # Delete DB record first
        instance.delete()
        print(f"ML Algorithm '{algorithm_name}' (ID: {algorithm_id}) deleted from DB.")

        # Attempt to delete the physical file
        if model_path and os.path.exists(model_path):
            try:
                os.remove(model_path)
                print(f"Associated model file deleted: {model_path}")
            except OSError as e:
                # Log error but don't fail the request as DB record is gone
                print(f"Warning: Error deleting model file {model_path}: {e}")
        elif instance.model_file:
             # Log if path was expected but not found or missing
            print(f"Warning: Model file path was associated but not found for deleted algorithm: {model_path}")

    # --- Custom Actions ---

    @action(detail=True, methods=['post'], url_path='predict', serializer_class=AlgorithmPredictInputSerializer)
    def predict(self, request, pk=None):
        """
        Perform prediction using the specified ML algorithm instance (by ID).
        Expects 'input_data' in the request body.
        """
        try:
            # Fetch the specific algorithm version
            algorithm = MLAlgorithm.objects.select_related('parent_endpoint').get(pk=pk)
        except MLAlgorithm.DoesNotExist:
            return Response(
                {'error': f"Algorithm with ID {pk} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate the incoming request data
        serializer = self.get_serializer(data=request.data) # Use the serializer defined in @action
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Check model file existence and accessibility
        model_file_path = None
        if algorithm.model_file and hasattr(algorithm.model_file, 'path'):
            model_file_path = algorithm.model_file.path
            if not os.path.exists(model_file_path):
                print(f"Error: Model file for Algorithm ID {pk} not found at configured path: {model_file_path}")
                model_file_path = None # Mark as non-existent

        if not model_file_path:
            return Response(
                {'error': f"Model file not found or inaccessible for algorithm ID {algorithm.id}. Cannot predict."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE # Service unavailable as model is missing
            )

        try:
            # Load the model file
            load_start = time.time()
            model = joblib.load(model_file_path)
            load_time = time.time() - load_start
            print(f"Loaded model for Algorithm ID {pk} in {load_time:.4f}s")

            # Prepare input data (validated by serializer)
            input_data = np.array(serializer.validated_data['input_data'])

            # Optional: Validate input data shape if model supports it
            expected_features = getattr(model, 'n_features_in_', None)
            if expected_features is not None and input_data.shape[1] != expected_features:
                return Response(
                    {'error': (f"Input data shape mismatch: received {input_data.shape[1]} features, "
                               f"but model expects {expected_features}.")},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Perform the prediction
            predict_start = time.time()
            prediction = model.predict(input_data)
            predict_time = time.time() - predict_start

            # Format prediction for JSON response
            prediction_list = prediction.tolist() if isinstance(prediction, np.ndarray) else prediction

            # Calculate total processing time
            response_time = load_time + predict_time

            # Log the prediction request to the database
            try:
                ml_request = MLRequest.objects.create(
                    input_data=serializer.validated_data['input_data'],
                    prediction=prediction_list,
                    algorithm=algorithm,
                    response_time=response_time
                )
                response_data = {
                    'prediction': prediction_list,
                    'request_id': ml_request.id,
                    'algorithm_version': algorithm.version,
                    'processing_time_ms': round(response_time * 1000, 2)
                }
                print(f"Prediction successful for Algorithm ID {pk}. Request ID: {ml_request.id}. Time: {response_time:.4f}s")
            except Exception as db_error:
                # Log the DB saving error, but still return the prediction result
                print(f"CRITICAL: Error saving MLRequest log for algorithm {algorithm.id}: {db_error}")
                traceback.print_exc()
                response_data = {
                    'prediction': prediction_list,
                    'warning': 'Prediction successful, but failed to log request details.',
                    'algorithm_version': algorithm.version,
                    'processing_time_ms': round(response_time * 1000, 2)
                }

            return Response(response_data, status=status.HTTP_200_OK)

        # --- Specific Error Handling for Prediction Process ---
        except FileNotFoundError:
            # Should be caught by earlier check, but handle defensively
            print(f"Error: Model file disappeared between check and load: {model_file_path}")
            return Response(
                {'error': f"Model file became inaccessible during prediction process: {model_file_path}."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except ValueError as ve:
            # Errors from np.array conversion or model.predict() due to data shape/type
            print(f"Prediction ValueError for Algorithm ID {pk}: {ve}")
            traceback.print_exc()
            return Response(
                {'error': f"Prediction failed due to invalid input data format or shape: {str(ve)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except (AttributeError, TypeError) as te:
             # Errors if model object doesn't have predict or handles data unexpectedly
             print(f"Prediction TypeError/AttributeError for Algorithm ID {pk}: {te}")
             traceback.print_exc()
             return Response(
                {'error': f"Prediction failed due to model incompatibility or internal error: {str(te)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            # Catch-all for other unexpected issues (e.g., loading corrupted file, memory errors)
            print(f"Unexpected prediction error for Algorithm ID {pk}: {e}")
            traceback.print_exc()
            return Response(
                {'error': f"An unexpected server error occurred during prediction: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='retrain')
    def retrain(self, request, pk=None):
        """
        Triggers the synchronous retraining process for the specified algorithm.
        Delegates the core logic to the appropriate retrainer class found via
        the `get_retrainer` factory in `retraining_logic.py`.

        WARNING: This is a synchronous operation and may time out for large
                 datasets or complex models.
        """
        try:
            # Get the specific algorithm instance to be retrained
            algorithm_to_retrain = self.get_object()
        except MLAlgorithm.DoesNotExist:
            return Response(
                {'error': f"Algorithm with ID {pk} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        print(f"Received request to retrain Algorithm ID: {pk} (Type: {algorithm_to_retrain.get_model_type_display()}, Version: {algorithm_to_retrain.version})")

        
        try:
            # Get the appropriate retrainer instance based on the algorithm's type
            retrainer = get_retrainer(algorithm_to_retrain)

            # Execute the retraining process (fetches data, preprocesses, fits, saves, updates DB)
            # This call blocks until retraining is complete.
            new_algorithm_instance, results = retrainer.retrain()

            # Handle cases where retraining logic determines no action is needed (e.g., no new data)
            if results.get("status") == "no_data":
                print(f"Retraining for Algorithm ID {pk} resulted in no action: {results.get('message')}")
                return Response(results, status=status.HTTP_200_OK) # Indicate success but no change

            # If successful, serialize the *new* algorithm instance for the response
            new_serializer = self.get_serializer(new_algorithm_instance)
            response_data = {
                "message": results.get("message", "Retraining process completed successfully."),
                "new_algorithm": new_serializer.data, # Details of the newly created version
                "metrics": { # Provide performance metrics of the retraining process itself
                    k: v for k, v in results.items()
                    if k.endswith("_seconds") or k.startswith("data_points")
                }
            }
            print(f"Retraining successful for Algorithm ID {pk}. New version created: {new_algorithm_instance.version} (ID: {new_algorithm_instance.id})")
            return Response(response_data, status=status.HTTP_201_CREATED) # 201 Created for the new algorithm version

            # --- Handle Specific Errors from Retraining Logic ---
            except (RetrainingError, FileNotFoundError, EnvironmentError, NotImplementedError) as e:
            print(f"Retraining failed for Algorithm ID {pk}. Error: {type(e).__name__}: {e}")

            if isinstance(e, FileNotFoundError):
                error_status = status.HTTP_404_NOT_FOUND  # model file missing
            elif isinstance(e, NotImplementedError):
                error_status = status.HTTP_501_NOT_IMPLEMENTED  # retrainer not implemented
            elif isinstance(e, EnvironmentError):
                error_status = status.HTTP_503_SERVICE_UNAVAILABLE  # DB or resources unavailable
            else:  # generic retraining error
                error_status = status.HTTP_500_INTERNAL_SERVER_ERROR

            return Response(
                {"error": f"Retraining failed: {e}"},
                status=error_status,
            )

        # --- Handle Unexpected Errors in the View ---
        except Exception as e:
            print(f"Unexpected error during retraining trigger for Algorithm ID {pk}: {e}")
            traceback.print_exc()
            return Response(
                {'error': f"An unexpected server error occurred during the retraining request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MLRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing ML prediction request logs.
    Provides read-only access with filtering and searching.
    """
    queryset = MLRequest.objects.all().order_by('-created_at')
    serializer_class = MLRequestSerializer
    permission_classes = [permissions.IsAuthenticated] # Allow any authenticated user to view

    # Enable filtering based on related algorithm fields
    filterset_fields = [
        'algorithm__id',
        'algorithm__name',
        'algorithm__version',
        'algorithm__model_type',
        'algorithm__parent_endpoint__id',
        'algorithm__parent_endpoint__name'
    ]
    # Enable basic text search within JSON fields (should double check it works with django)
    search_fields = ['input_data', 'prediction']