# ml_api/serializers.py

import os
from rest_framework import serializers
from .models import Endpoint, MLAlgorithm, MLRequest
import numpy as np # Needed for isnumeric check example

# Define validation constants
VALID_MODEL_EXTENSIONS = ['.pkl', '.joblib']
MAX_MODEL_FILE_SIZE_MB = 50  # Max size in Megabytes
MAX_MODEL_FILE_SIZE_BYTES = MAX_MODEL_FILE_SIZE_MB * 1024 * 1024


class EndpointSerializer(serializers.ModelSerializer):
    """Serializer for the Endpoint model."""
    # Provides URLs to related algorithms for API navigability
    algorithms = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='ml_api:mlalgorithm-detail'# Matches the basename used in urls.py router
    )

    class Meta:
        model = Endpoint
        fields = [
            'id', 'name', 'owner', 'created_at', 'algorithms'
        ]
        read_only_fields = ('id', 'created_at', 'algorithms')


class MLAlgorithmSerializer(serializers.ModelSerializer):
    """Serializer for the MLAlgorithm model, handling file uploads and model type."""
    # Provides readable details of the parent endpoint
    parent_endpoint_details = serializers.SerializerMethodField()

    class Meta:
        model = MLAlgorithm
        fields = [
            'id',
            'name',
            'description',
            'version',
            'code',
            'model_file',      # For upload and displaying the file path
            'model_type',      # Added field
            'is_active',       # Added field
            'parent_endpoint', # Writable FK field for associating with an endpoint
            'parent_endpoint_details', 
            'created_at',
            'updated_at'
        ]
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
        )
        extra_kwargs = {
            # File is not required on updates (PATCH) unless explicitly provided
            'model_file': {'required': False, 'allow_null': True},
        }

    def validate_model_file(self, value):
        """Validate the uploaded model file's extension and size."""
        if value is None:
            # Allow null only if the field itself allows null (e.g., during PATCH)
            return value

        # Validate file extension
        ext = os.path.splitext(value.name)[1]
        if not ext.lower() in VALID_MODEL_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file extension '{ext}'. "
                f"Allowed extensions are: {', '.join(VALID_MODEL_EXTENSIONS)}"
            )

        # Validate file size
        if value.size > MAX_MODEL_FILE_SIZE_BYTES:
            raise serializers.ValidationError(
                f"Model file size ({value.size // 1024 // 1024}MB) exceeds the "
                f"limit of {MAX_MODEL_FILE_SIZE_MB}MB."
            )
        return value

    def get_parent_endpoint_details(self, obj):
        """
        Serialize the parent_endpoint with context.
        """
        if obj.parent_endpoint:
            request = self.context.get('request')
            return EndpointSerializer(obj.parent_endpoint, context={'request': request}).data
        return None


class MLRequestSerializer(serializers.ModelSerializer):
    """Serializer for the MLRequest model (prediction logs)."""
    # Provides a readable string representation of the algorithm used
    algorithm_details = serializers.StringRelatedField(source='algorithm', read_only=True)

    class Meta:
        model = MLRequest
        fields = [
            'id',
            'input_data',
            'prediction',
            'algorithm', # The FK id
            'algorithm_details', # Read-only string representation
            'created_at',
            'response_time'
        ]
        # Logs are typically read-only once created
        read_only_fields = (
            'id',
            'input_data', # Usually set on creation, not modified
            'prediction',
            'algorithm', # Usually set on creation
            'algorithm_details',
            'created_at',
            'response_time',
        )


class AlgorithmPredictInputSerializer(serializers.Serializer):
    """Serializer specifically for validating input to the 'predict' action."""
    input_data = serializers.JSONField(
        help_text=(
            "Input data for prediction. Must be a list of lists (rows), where each "
            "inner list represents a data point's features (e.g., "
            "[[feature1, feature2, ...], [feature1, feature2, ...]])."
        )
    )

    def validate_input_data(self, value):
        """Validate the structure and basic types within input_data."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Input data must be a list (array).")
        if not value:
             raise serializers.ValidationError("Input data list cannot be empty.")
        if not all(isinstance(item, list) for item in value):
            raise serializers.ValidationError(
                "Each item in the input_data list must be a list representing features."
            )

        # Check if all inner lists (rows) have the same number of features
        first_row_len = len(value[0])
        if not all(len(item) == first_row_len for item in value):
            raise serializers.ValidationError("All feature lists (rows) must have the same number of features.")

        # Check if all feature values are numeric (int or float)
        for row_idx, item in enumerate(value):
             for col_idx, num in enumerate(item):
                 if not isinstance(num, (int, float)):
                      raise serializers.ValidationError(
                          f"All features must be numeric (int or float). Found non-numeric value "
                          f"'{num}' (type: {type(num).__name__}) at row {row_idx}, column {col_idx}."
                      )

        return value