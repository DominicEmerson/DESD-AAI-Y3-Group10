"""
Django management command to register pre-trained ML models in the database.

This command explicitly defines the models to register, setting their names,
versions, descriptions, types, and the relative path to their saved file
within the project structure (e.g., 'ml_models/model_name.pkl').
"""


from django.core.management.base import BaseCommand

from ml_api.models import Endpoint, MLAlgorithm


class Command(BaseCommand):
    """Registers predefined ML models with their metadata in the database."""

    help = "Register ML models explicitly defined in this command in the database."

    def handle(self, *args, **kwargs):
        """Executes the model registration logic."""
        self.stdout.write("--- Starting Model Registration ---")

        # --- Create default endpoint ---
        # get_or_create returns a tuple: (object, created_boolean)
        endpoint, endpoint_created = Endpoint.objects.get_or_create(
            name="Insurance Claim Prediction",
            # Use defaults for fields only needed on initial creation
            defaults={'owner': "Insurance AI Team"}
        )
        if endpoint_created:
            self.stdout.write(
                self.style.SUCCESS(f"Created Endpoint: {endpoint.name}")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Using existing Endpoint: {endpoint.name}")
            )
        self.stdout.write("")  # Add a blank line for spacing

        # --- Model Definitions ---
        # Define models as a list of dictionaries for easier management
        # when registering a new model update the version number to match what is in the file name
        models_to_register = [
            {
                "name": "3-Feature Regression Model",
                "version": "1.0.0",
                "relative_path": "ml_models/3feature_regression_model.pkl",
                "description": "Predicts insurance claim values based on three key features.",
                "model_type": "OTHER",
                "is_active": True,  # Example: Mark this one as active
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
            model_path = model_data["relative_path"]
            algorithm, created = MLAlgorithm.objects.get_or_create(
                name=model_data["name"],
                version=model_data["version"],
                parent_endpoint=endpoint,
                # Fields to set/update if creating OR finding
                defaults={
                    'description': model_data["description"],
                    'code': "",  # Add model code/config if needed
                    'model_file': model_path,  # Stores the relative path
                    'model_type': model_data["model_type"],
                    'is_active': model_data["is_active"],
                }
            )

            # Check if the model was found (not created) and if the path needs updating
            updated = False
            if not created:
                # Check multiple fields that might need updating if defaults change
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
            elif not updated: # Only print 'already exists' if no updates were made
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Model {algorithm.name} v{algorithm.version} "
                        f"already exists and is up-to-date."
                    )
                )
            self.stdout.write("-" * 20) # Separator

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