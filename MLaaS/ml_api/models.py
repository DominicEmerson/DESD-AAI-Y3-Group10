# ml_api/models.py

from django.db import models  # Import models from Django ORM

class Endpoint(models.Model):
    """
    Represents a logical grouping for related Machine Learning (ML) algorithms.
    This model defines an endpoint, which acts as a container or a high-level
    category for one or more ML algorithms that serve a similar purpose or
    belong to the same project.
    Attributes:
        name (models.CharField): The name of the ML endpoint. This is a
            human-readable identifier for the endpoint, limited to 128 characters.
            Example: 'Insurance Claim Prediction'.
        owner (models.CharField): The owner or team responsible for maintaining
            and managing this endpoint. Limited to 128 characters.
        created_at (models.DateTimeField): The date and time when this endpoint
            was first created. This field is automatically set to the current
            timestamp upon creation and is not editable.
    Meta:
        ordering (list): Specifies the default ordering for queries on the
            Endpoint model. Endpoints will be ordered by their 'name'
            in ascending order by default.
    Methods:
        __str__(): Returns a string representation of the Endpoint instance,
            displaying its name and owner. For example:
            "Insurance Claim Prediction (Owner: Data Science Team)".
    """
    """Represents a logical grouping for related ML algorithms."""
    name = models.CharField(
        max_length=128,
        help_text="Name of the ML endpoint (e.g., 'Insurance Claim Prediction')."  # Help text for endpoint name
    )
    owner = models.CharField(
        max_length=128,
        help_text="Owner or team responsible for the endpoint."  # Help text for endpoint owner
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the endpoint was created."  # Help text for creation timestamp
    )

    class Meta:
        ordering = ['name']  # Default ordering by name

    def __str__(self):
        return f"{self.name} (Owner: {self.owner})"  # String representation of the endpoint

class MLAlgorithm(models.Model):
    """
    Represents a specific version of a machine learning algorithm.
    This model stores metadata and the actual model file for a particular
    version of an ML algorithm. It is associated with an `Endpoint`.
    Attributes:
        MODEL_TYPE_CHOICES (list): A list of tuples defining the choices for the
            `model_type` field. Includes 'RANDOM_FOREST', 'XGBOOST', and 'OTHER'.
        name (CharField): User-friendly name for the algorithm (e.g., 'Claim Severity Predictor').
            Max length is 128 characters.
        description (TextField): Detailed description of the algorithm, its purpose,
            and features used. This field is optional.
        version (CharField): Version string for the algorithm (e.g., '1.0.0', '2.1-alpha').
            Max length is 128 characters.
        code (TextField): Optional field to store small code snippets, configuration,
            or metadata related to the model.
        model_file (FileField): Path to the saved/pickled model file (e.g., .pkl, .joblib),
            relative to `MEDIA_ROOT`. Uploaded files are stored in 'ml_models/'.
            Max length for the path/name is 255 characters.
        model_type (CharField): Type of the underlying ML model framework used (e.g., 'RANDOM_FOREST').
            Max length is 50 characters. Defaults to 'OTHER'.
        parent_endpoint (ForeignKey): A foreign key relationship to the `Endpoint` model,
            indicating which endpoint this algorithm belongs to. Deletion of the parent
            endpoint will cascade and delete associated algorithms.
            The `related_name` 'algorithms' allows easy access from an Endpoint instance
            (e.g., `endpoint.algorithms.all()`).
        created_at (DateTimeField): Timestamp automatically set to when this algorithm
            version was created/registered.
        updated_at (DateTimeField): Timestamp automatically set to the last time this
            algorithm record was updated.
        is_active (BooleanField): A flag indicating whether this is the currently
            active/recommended version of the algorithm. Defaults to `True`.
    Meta:
        ordering (list): Specifies the default ordering for querysets: by `parent_endpoint`,
            then by `name`, and then by `version` in descending order (newest first).
        unique_together (tuple): Ensures that the combination of `name`, `version`,
            and `parent_endpoint` is unique.
    Methods:
        __str__(): Returns a string representation of the algorithm, including its name,
            version, and display name of its model type.
            Example: "Claim Severity Predictor v1.0.0 (Random Forest)".
    """
    """Represents a specific version of a machine learning algorithm."""
    MODEL_TYPE_CHOICES = [
        ('RANDOM_FOREST', 'Random Forest'),  # Choice for Random Forest model type
        ('XGBOOST', 'XGBoost'),  # Choice for XGBoost model type
        ('OTHER', 'Other'),  # Choice for other model types
    ]

    name = models.CharField(
        max_length=128,
        help_text="User-friendly name for the algorithm (e.g., 'Claim Severity Predictor')."  # Help text for algorithm name
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the algorithm, its purpose, and features used."  # Help text for algorithm description
    )
    version = models.CharField(
        max_length=128,
        help_text="Version string for the algorithm (e.g., '1.0.0', '2.1-alpha')."  # Help text for algorithm version
    )
    code = models.TextField(
        blank=True,
        help_text="Optional: Store small code snippets, configuration, or metadata related to the model."  # Help text for model code
    )
    model_file = models.FileField(
        upload_to='ml_models/',
        max_length=255,  # Allow for longer file paths/names if needed
        help_text="Path to the saved/pickled model file (e.g., .pkl, .joblib), relative to MEDIA_ROOT."  # Help text for model file path
    )
    model_type = models.CharField(
        max_length=50,
        choices=MODEL_TYPE_CHOICES,
        default='OTHER',
        help_text="Type of the underlying ML model framework used."  # Help text for model type
    )
    parent_endpoint = models.ForeignKey(
        Endpoint,
        on_delete=models.CASCADE,
        related_name='algorithms',  # Allows easy access from Endpoint: endpoint.algorithms.all()
        help_text="The endpoint this algorithm belongs to."  # Help text for parent endpoint
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this algorithm version was created/registered."  # Help text for creation timestamp
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp of the last update to this algorithm record."  # Help text for update timestamp
    )
    # Add an is_active flag for easier version management via API
    is_active = models.BooleanField(default=True, help_text="Is this the currently active/recommended version?")  # Help text for active status

    class Meta:
        ordering = ['parent_endpoint', 'name', '-version']  # Order by endpoint, name, then newest version
        unique_together = ('name', 'version', 'parent_endpoint')  # Ensure unique name/version per endpoint

    def __str__(self):
        return f"{self.name} v{self.version} ({self.get_model_type_display()})"  # String representation of the algorithm

class MLRequest(models.Model):
    """
    Represents a log of a prediction request made to an MLAlgorithm.
    This model stores details about each prediction request, including the input data,
    the prediction result, the algorithm used, and timing information.
    Attributes:
        input_data (JSONField): The input data provided for the prediction.
        prediction (JSONField): The prediction result from the model.
                                This can be null if the prediction failed or is not applicable.
        algorithm (ForeignKey to MLAlgorithm): A reference to the `MLAlgorithm`
                                               instance that processed this request.
                                               If the `MLAlgorithm` is deleted,
                                               associated `MLRequest` instances are also deleted.
        created_at (DateTimeField): The timestamp indicating when the prediction
                                    request was received. Automatically set on creation.
        response_time (FloatField): The time taken (in seconds) for the prediction
                                    to be processed. This can be null.
    Meta:
        ordering (list): Specifies the default ordering for queries,
                         set to `['-created_at']` to show the most recent requests first.
    Methods:
        __str__(): Returns a string representation of the request, including the
                   algorithm name, version, and the request timestamp.
                   Example: "Request for MyAlgorithm v1.0 at 2023-01-01 12:00:00".
    """
    # ... (rest of the code remains the same)
    """Logs prediction requests made to an MLAlgorithm."""
    input_data = models.JSONField(
        help_text="The input data sent for prediction."  # Help text for input data
    )
    prediction = models.JSONField(
        null=True, blank=True,  # Prediction might fail or not be applicable
        help_text="The prediction result returned by the model."  # Help text for prediction result
    )
    algorithm = models.ForeignKey(
        MLAlgorithm,
        on_delete=models.CASCADE,  # If the algorithm version is deleted, associated requests are too
        related_name='requests',  # Allows easy access from MLAlgorithm: algorithm.requests.all()
        help_text="The specific algorithm version used for this prediction."  # Help text for algorithm reference
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the prediction request was received."  # Help text for request timestamp
    )
    response_time = models.FloatField(
        null=True, blank=True,  # Might not always be recorded
        help_text="Time taken for the prediction processing (in seconds)."  # Help text for response time
    )

    class Meta:
        ordering = ['-created_at']  # Show most recent requests first

    def __str__(self):
        # Check if algorithm still exists (might be None if deleted unexpectedly)
        algo_str = f"{self.algorithm.name} v{self.algorithm.version}" if self.algorithm else "N/A"  # String representation of the request
        return f"Request for {algo_str} at {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"  # Return formatted string