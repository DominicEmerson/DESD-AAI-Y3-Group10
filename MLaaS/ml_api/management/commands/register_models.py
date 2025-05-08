"""
Django management command to register pre-trained ML models in the database.

This command explicitly defines the models to register, setting their names,
versions, descriptions, types, and the relative path to their saved file
within the project structure (e.g., 'ml_models/model_name.pkl').
"""

from django.core.management.base import BaseCommand  # Import base command for management commands

from ml_api.models import Endpoint, MLAlgorithm  # Import models for endpoints and algorithms

class Command(BaseCommand):
    """Registers predefined ML models with their metadata in the database."""

    help = "Register ML models explicitly defined in this command in the database."  # Help text for command

    def handle(self, *args, **kwargs):
        """Executes the model registration logic."""
        self.stdout.write("--- Starting Model Registration ---")  # Log start of registration

        # --- Create default endpoint ---
        # get_or_create returns a tuple: (object, created_boolean)
        endpoint, endpoint_created = Endpoint.objects.get_or_create(
            name="Insurance Claim Prediction",  # Name for the endpoint
            # Use defaults for fields only needed on initial creation
            defaults={'owner': "Insurance AI Team"}  # Default owner for the endpoint
        )
        if endpoint_created:
            self.stdout.write(
                self.style.SUCCESS(f"Created Endpoint: {endpoint.name}")  # Log successful endpoint creation
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Using existing Endpoint: {endpoint.name}")  # Log existing endpoint usage
            )
        self.stdout.write("")  # Add a blank line for spacing

        # --- Model Definitions ---
        # Define models as a list of dictionaries for easier management
        # when registering a new model update the version number to match what is in the file name
        models_to_register = [
            {
                "name": "3-Feature Regression Model",  # Name of the model
                "version": "1.0.0",  # Version of the model
                "relative_path": "ml_models/3feature_regression_model.pkl",  # Relative path to model file
                "description": "Predicts insurance claim values based on three key features.",  # Description of the model
                "model_type": "OTHER",  # Model type
                "is_active": True,  # Mark this model as active
            },
            {
                "name": "Random Forest Claim Predictor",
                "version": "20250507",  # <-- NEW VERSION
                "relative_path": "ml_models/random_forest_20250507.pkl",
                "description": "Predicts insurance claims using a Random Forest model.",
                "model_type": "RANDOM_FOREST",
                "is_active": True,
            },
            {
                "name": "XGBoost Claim Predictor",
                "version": "20250507",  # <-- NEW VERSION
                "relative_path": "ml_models/xgboost_20250507.pkl",
                "description": "Predicts insurance claims using an XGBoost model.",
                "model_type": "XGBOOST",
                "is_active": True,
            },
        ]

        # --- Loop through and register/update models ---
        for model_data in models_to_register:
            model_path = model_data["relative_path"]  # Get model file path
            algorithm, created = MLAlgorithm.objects.get_or_create(
                name=model_data["name"],  # Get or create algorithm by name
                version=model_data["version"],  # Get or create algorithm by version
                parent_endpoint=endpoint,  # Associate with the created endpoint
                # Fields to set/update if creating OR finding
                defaults={
                    'description': model_data["description"],  # Set description
                    'code': "",  # Add model code/config if needed
                    'model_file': model_path,  # Store the relative path
                    'model_type': model_data["model_type"],  # Set model type
                    'is_active': model_data["is_active"],  # Set active status
                }
            )

            # Check if the model was found (not created) and if the path needs updating
            updated = False  # Initialise updated flag
            if not created:  # If the model already exists
                # Check multiple fields that might need updating if defaults change
                fields_to_check = ['description', 'model_file', 'model_type', 'is_active']  # Fields to check for updates
                for field in fields_to_check:
                    if getattr(algorithm, field) != model_data.get(field, getattr(algorithm, field)):
                        setattr(algorithm, field, model_data[field])  # Update field value
                        updated = True  # Set updated flag
                if updated:
                    algorithm.save()  # Save updated algorithm
                    self.stdout.write(
                        self.style.WARNING(
                            f"Updated details for existing model "
                            f"{algorithm.name} v{algorithm.version}"  # Log updated model details
                        )
                    )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully registered model "
                        f"{algorithm.name} v{algorithm.version}"  # Log successful model registration
                    )
                )
            elif not updated:  # Only print 'already exists' if no updates were made
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Model {algorithm.name} v{algorithm.version} "
                        f"already exists and is up-to-date."  # Log existing model status
                    )
                )
            self.stdout.write("-" * 20)  # Separator for output

        # --- Now, after the registration loop, do the legacy/active logic ---
        for model_data in models_to_register:
            name = model_data["name"]
            all_versions = MLAlgorithm.objects.filter(name=name, parent_endpoint=endpoint)
            if not all_versions.exists():
                continue
            # Mark all as legacy
            for m in all_versions:
                m.is_active = False
                if m.description and "(Legacy)" not in m.description:
                    m.description = m.description.strip() + " (Legacy)"
                elif not m.description:
                    m.description = "(Legacy)"
                m.save()
            # Find the latest version (max by string, works for date-based)
            latest = max(all_versions, key=lambda m: str(m.version))
            latest.is_active = True
            if latest.description and "(Legacy)" in latest.description:
                latest.description = latest.description.replace("(Legacy)", "").strip()
            latest.save()
            self.stdout.write(self.style.SUCCESS(f"Set {latest.name} v{latest.version} as ACTIVE (latest version)"))

        self.stdout.write("--- Model Registration Finished ---")