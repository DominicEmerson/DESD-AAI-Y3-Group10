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
                "is_active": False,  # Not active by default
            },
            {
                "name": "Random Forest Claim Predictor",
                "version": "20250507",  # <-- NEW VERSION
                "relative_path": "ml_models/random_forest_20250507.pkl",
                "description": "Predicts insurance claims using a Random Forest model.",
                "model_type": "RANDOM_FOREST",
                "is_active": False,  # Not active by default
            },
            {
                "name": "XGBoost Claim Predictor",
                "version": "20250507",  # <-- NEW VERSION
                "relative_path": "ml_models/xgboost_20250507.pkl",
                "description": "Predicts insurance claims using an XGBoost model.",
                "model_type": "XGBOOST",
                "is_active": True,  # Only this one is active
            },
        ]

        # --- Loop through and register/update models ---
        for model_data in models_to_register:
            model_path = model_data["relative_path"]  # Get model file path
            algorithm, created = MLAlgorithm.objects.get_or_create(
                name=model_data["name"],  # Get or create algorithm by name
                version=model_data["version"],  # Get or create algorithm by version
                parent_endpoint=endpoint,  # Associate with the created endpoint
                defaults={
                    'description': model_data["description"],
                    'code': "",
                    'model_file': model_path,
                    'model_type': model_data["model_type"],
                    'is_active': model_data["is_active"],
                }
            )

            updated = False
            if not created:
                fields_to_check = ['description', 'model_file', 'model_type', 'is_active']
                for field in fields_to_check:
                    if getattr(algorithm, field) != model_data.get(field, getattr(algorithm, field)):
                        setattr(algorithm, field, model_data[field])
                        updated = True
                if updated:
                    algorithm.save()
                    self.stdout.write(
                        self.style.WARNING(
                            f"Updated details for existing model "
                            f"{algorithm.name} v{algorithm.version}"
                        )
                    )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully registered model "
                        f"{algorithm.name} v{algorithm.version}"
                    )
                )
            elif not updated:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Model {algorithm.name} v{algorithm.version} "
                        f"already exists and is up-to-date."
                    )
                )
            self.stdout.write("-" * 20)

        # --- Explicitly set ONE default active model for the endpoint ---
        endpoint, _ = Endpoint.objects.get_or_create(name="Insurance Claim Prediction", defaults={'owner': "Insurance AI Team"})
        default_model_name = "XGBoost Claim Predictor"
        try:
            default_algo_to_activate = MLAlgorithm.objects.filter(
                name=default_model_name,
                parent_endpoint=endpoint
            ).latest('version')
            default_algo_to_activate.is_active = True
            default_algo_to_activate.save()
            self.stdout.write(self.style.SUCCESS(
                f"Set {default_algo_to_activate.name} v{default_algo_to_activate.version} as DEFAULT ACTIVE for endpoint '{endpoint.name}'"
            ))
        except MLAlgorithm.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"Could not find model named '{default_model_name}' to set as default active for endpoint '{endpoint.name}'."
            ))
        except MLAlgorithm.MultipleObjectsReturned:
            self.stdout.write(self.style.ERROR(
                f"Found multiple 'latest' versions for '{default_model_name}'. Manual intervention needed or refine 'latest' logic."
            ))

        self.stdout.write("--- Model Registration Finished ---")