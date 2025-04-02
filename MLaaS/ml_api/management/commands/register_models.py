from django.core.management.base import BaseCommand
from ml_api.models import Endpoint, MLAlgorithm
import os

class Command(BaseCommand):
    help = 'Register ML models in the database'

    def handle(self, *args, **kwargs):
        # Create default endpoint
        endpoint, _ = Endpoint.objects.get_or_create(
            name="Insurance Claim Prediction",
            owner="Insurance AI Team"
        )

        # Register the regression model
        model_path = 'ml_models/3feature_regression_model.pkl'
        algorithm, created = MLAlgorithm.objects.get_or_create(
            name="3-Feature Regression Model",
            description="Predicts insurance claim values based on three key features",
            version="1.0.0",
            code="",  # Add model code if needed
            model_file=model_path,
            parent_endpoint=endpoint
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Successfully registered model {algorithm.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Model {algorithm.name} already exists'))
