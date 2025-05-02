# engineer/forms.py
import os
from django import forms
from django.core.exceptions import ValidationError

# --- Constants needed for the form ---

# Define model type choices directly, mirroring ml_api.models
MODEL_TYPE_CHOICES = [
    ('RANDOM_FOREST', 'Random Forest'),
    ('XGBOOST', 'XGBoost'),
    ('OTHER', 'Other'),
]

# Define allowed file extensions and size limit
VALID_MODEL_EXTENSIONS = ['.pkl']
ACCEPT_FILE_TYPES = ','.join(VALID_MODEL_EXTENSIONS)
MAX_UPLOAD_SIZE_MB = 50
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024


class ModelUploadForm(forms.Form):
    """Form for registering a new ML model file and metadata via API."""
    name = forms.CharField(
        max_length=128,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    version = forms.CharField(
        max_length=128,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 1.0.0 or 20240515.1'})
    )
    model_type = forms.ChoiceField(
        choices=[('', '---------')] + MODEL_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    parent_endpoint = forms.IntegerField(
        required=True,
        initial=1,  # Default to 1, assuming it's common
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Parent Endpoint ID",
        help_text="Enter the ID of the logical endpoint (e.g., 1)."
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False
    )
    model_file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': ACCEPT_FILE_TYPES}),
        label=f"Model File ({VALID_MODEL_EXTENSIONS[0]} only)"
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Set as active model upon registration?"
    )

    def clean_model_file(self):
        """Validate file extension is '.pkl' and size is within limit."""
        file = self.cleaned_data.get('model_file')
        if file:
            # Validate extension
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in VALID_MODEL_EXTENSIONS:
                raise ValidationError(
                    f"Unsupported file type '{ext}'. Only {VALID_MODEL_EXTENSIONS[0]} files are allowed."
                )
            # Validate file size
            if file.size > MAX_UPLOAD_SIZE_BYTES:
                raise ValidationError(
                    f"File size ({file.size // 1024 // 1024}MB) exceeds the limit of {MAX_UPLOAD_SIZE_MB}MB."
                )
        return file

    def clean_parent_endpoint(self):
        """Validate Endpoint ID is positive."""
        endpoint_id = self.cleaned_data.get('parent_endpoint')
        if endpoint_id is not None and endpoint_id <= 0:
            raise ValidationError("Endpoint ID must be a positive number.")
        # Existence check relies on the receiving MLaaS API.
        return endpoint_id