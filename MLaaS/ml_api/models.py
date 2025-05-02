# ml_api/models.py

from django.db import models

class Endpoint(models.Model):
    """Represents a logical grouping for related ML algorithms."""
    name = models.CharField(
        max_length=128,
        help_text="Name of the ML endpoint (e.g., 'Insurance Claim Prediction')."
    )
    owner = models.CharField(
        max_length=128,
        help_text="Owner or team responsible for the endpoint."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the endpoint was created."
    )

    class Meta:
        ordering = ['name'] # Default ordering

    def __str__(self):
        return f"{self.name} (Owner: {self.owner})"


class MLAlgorithm(models.Model):
    """Represents a specific version of a machine learning algorithm."""
    MODEL_TYPE_CHOICES = [
        ('RANDOM_FOREST', 'Random Forest'),
        ('XGBOOST', 'XGBoost'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(
        max_length=128,
        help_text="User-friendly name for the algorithm (e.g., 'Claim Severity Predictor')."
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the algorithm, its purpose, and features used."
    )
    version = models.CharField(
        max_length=128,
        help_text="Version string for the algorithm (e.g., '1.0.0', '2.1-alpha')."
    )
    code = models.TextField(
        blank=True,
        help_text="Optional: Store small code snippets, configuration, or metadata related to the model."
    )
    model_file = models.FileField(
        upload_to='ml_models/',
        max_length=255, # Allow for longer file paths/names if needed
        help_text="Path to the saved/pickled model file (e.g., .pkl, .joblib), relative to MEDIA_ROOT."
    )
    model_type = models.CharField(
        max_length=50,
        choices=MODEL_TYPE_CHOICES,
        default='OTHER',
        help_text="Type of the underlying ML model framework used."
    )
    parent_endpoint = models.ForeignKey(
        Endpoint,
        on_delete=models.CASCADE,
        related_name='algorithms', # Allows easy access from Endpoint: endpoint.algorithms.all()
        help_text="The endpoint this algorithm belongs to."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this algorithm version was created/registered."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp of the last update to this algorithm record."
    )
    # Add an is_active flag for easier version management via API
    is_active = models.BooleanField(default=True, help_text="Is this the currently active/recommended version?")

    class Meta:
        ordering = ['parent_endpoint', 'name', '-version'] # Order by endpoint, name, then newest version
        unique_together = ('name', 'version', 'parent_endpoint') # Ensure unique name/version per endpoint

    def __str__(self):
        return f"{self.name} v{self.version} ({self.get_model_type_display()})"


class MLRequest(models.Model):
    """Logs prediction requests made to an MLAlgorithm."""
    input_data = models.JSONField(
        help_text="The input data sent for prediction."
    )
    prediction = models.JSONField(
        null=True, blank=True, # Prediction might fail or not be applicable
        help_text="The prediction result returned by the model."
    )
    algorithm = models.ForeignKey(
        MLAlgorithm,
        on_delete=models.CASCADE, # If the algorithm version is deleted, associated requests are too
        related_name='requests', # Allows easy access from MLAlgorithm: algorithm.requests.all()
        help_text="The specific algorithm version used for this prediction."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the prediction request was received."
    )
    response_time = models.FloatField(
        null=True, blank=True, # Might not always be recorded
        help_text="Time taken for the prediction processing (in seconds)."
    )

    class Meta:
        ordering = ['-created_at'] # Show most recent requests first

    def __str__(self):
        # Check if algorithm still exists (might be None if deleted unexpectedly)
        algo_str = f"{self.algorithm.name} v{self.algorithm.version}" if self.algorithm else "N/A"
        return f"Request for {algo_str} at {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"