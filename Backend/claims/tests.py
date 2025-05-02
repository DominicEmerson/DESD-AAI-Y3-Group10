from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import json

from claims.models import Accident, Claim, Vehicle, Driver, Injury
from authentication.models import CustomUser
from claims.forms import ClaimSubmissionForm
from claims.views import ClaimSubmissionView

class ModelValidationTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser', password='testpass', role='enduser'
        )
        
        self.accident = Accident.objects.create(
            reported_by=self.user,
            accident_date=timezone.now(),
            accident_type='Rear end',
            police_report_filed=False,
            witness_present=True
        )

    def test_claim_model_validation(self):
        # Test settlementvalue constraints
        with self.assertRaises(ValidationError):
            Claim.objects.create(
                accident=self.accident,
                settlementvalue=Decimal('100000000.01')
            )

        # Test injuryprognosis range
        valid_claim = Claim.objects.create(
            accident=self.accident,
            injuryprognosis=60
        )
        with self.assertRaises(ValidationError):
            Claim.objects.create(
                accident=self.accident,
                injuryprognosis=61
            )

    def test_vehicle_age_validation(self):
        # Test vehicle age boundaries
        valid_vehicle = Vehicle.objects.create(
            accident=self.accident,
            vehicleage=100
        )
        with self.assertRaises(ValidationError):
            Vehicle.objects.create(
                accident=self.accident,
                vehicleage=101
            )

class FormValidationTests(TestCase):
    def test_claim_form_validation(self):
        # Test required fields
        form_data = {
            'settlementvalue': '',
            'injuryprognosis': 30
        }
        form = ClaimSubmissionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('settlementvalue', form.errors)

        # Test valid choice selection
        valid_data = {
            'settlementvalue': '5000.00',
            'injuryprognosis': 30,
            'injurydescription': 'Whiplash and minor bruises.',
            'vehicletype': 'Car',
            'weatherconditions': 'Sunny',
            'driverage': 25,
            'gender': 'Male'
        }
        form = ClaimSubmissionForm(data=valid_data)
        self.assertTrue(form.is_valid())

class ViewIntegrationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username='testuser', password='testpass', role='enduser'
        )
        self.client.login(username='testuser', password='testpass')

    def test_claim_submission_flow(self):
        # Test full submission workflow
        url = reverse('claims:claim_submission')
        valid_data = {
            'accident_date': '2025-05-01 12:00',
            'accident_type': 'Rear end',
            'settlementvalue': '5000.00',
            'injuryprognosis': 30,
            'vehicleage': 5,
            'driverage': 25,
            'gender': 'Male',
            'whiplash': 'False'
        }
        
        response = self.client.post(url, valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('claims:claim_submission_success'))

    def test_ml_service_integration(self):
        # Test ML service interaction
        from unittest.mock import patch
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'prediction': 5000}
            
            claim = Claim.objects.create(
                accident=self.accident,
                settlementvalue=5000.00
            )
            
            view = ClaimSubmissionView()
            view.request_prediction(claim)
            
            self.assertEqual(claim.prediction_result['prediction'], 5000)

class EdgeCaseTests(TestCase):
    def test_boundary_values(self):
        # Test age boundaries
        driver = Driver(driverage=16)
        driver.full_clean()  # Should not raise
        
        with self.assertRaises(ValidationError):
            Driver(driverage=15).full_clean()

    def test_choice_validation(self):
        # Test invalid choice submission
        form_data = {
            'accident_type': 'Invalid Type',
            'settlementvalue': '5000.00'
        }
        form = ClaimSubmissionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('accident_type', form.errors)

class ManagementCommandTests(TestCase):
    def test_csv_import(self):
        from io import StringIO
        from django.core.management import call_command
        
        # Test CSV import with sample data
        with open('clean_df.csv') as csv_file:
            out = StringIO()
            call_command('import_claims_data', stdout=out)
            self.assertIn('Successfully imported', out.getvalue())
            
            # Verify relationships
            self.assertEqual(Accident.objects.count(), Claim.objects.count())
            self.assertEqual(Accident.objects.count(), Vehicle.objects.count())
