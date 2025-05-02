# claims/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from claims.models import Accident, Claim, Vehicle, Driver, Injury

# Author: Ahmed Mohamed
class AccidentForm(forms.ModelForm):
    """Form for accident details in a claim."""
    class Meta:
        model = Accident
        fields = ['accident_date', 'accident_type', 'accident_description',
                  'police_report_filed', 'witness_present', 'weather_conditions']
        widgets = {
            'accident_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'accident_type': forms.Select(choices=Accident._meta.get_field('accident_type').choices, attrs={'class': 'form-control'}),
            'accident_description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'weather_conditions': forms.Select(choices=Accident._meta.get_field('weather_conditions').choices, attrs={'class': 'form-control'}),
            'police_report_filed': forms.Select(choices=[(True, 'Yes'), (False, 'No')], attrs={'class': 'form-control'}),
            'witness_present': forms.Select(choices=[(True, 'Yes'), (False, 'No')], attrs={'class': 'form-control'}),
        }

    def clean_accident_date(self):
        date = self.cleaned_data.get('accident_date')
        if date and date > timezone.now():
            raise ValidationError("Accident date cannot be in the future.")
        return date

    def clean(self):
        cleaned = super().clean()
        # Prevent 'Unknown' for categorical fields
        if cleaned.get('accident_type') == 'Unknown':
            self.add_error('accident_type', "Please select a valid accident type.")
        if cleaned.get('weather_conditions') == 'Unknown':
            self.add_error('weather_conditions', "Please select valid weather conditions.")
        return cleaned

# Author: Ahmed Mohamed
class VehicleForm(forms.ModelForm):
    """Form for vehicle details in a claim."""
    class Meta:
        model = Vehicle
        fields = ['vehicle_age', 'vehicle_type', 'number_of_passengers']
        widgets = {
            'vehicle_age': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100000', 'step': '1'}),
            'vehicle_type': forms.Select(choices=Vehicle._meta.get_field('vehicle_type').choices, attrs={'class': 'form-control'}),
            'number_of_passengers': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '100000', 'step': '1'}),
        }

    def clean_vehicle_age(self):
        age = self.cleaned_data.get('vehicle_age')
        if age is None or age < 0:
            raise ValidationError("Vehicle age cannot be negative.")
        if age > 100000:
            raise ValidationError("Vehicle age cannot exceed 100,000.")
        return age

    def clean_number_of_passengers(self):
        passengers = self.cleaned_data.get('number_of_passengers')
        if passengers is None or passengers < 1:
            raise ValidationError("Number of passengers must be at least 1.")
        if passengers > 100000:
            raise ValidationError("Number of passengers cannot exceed 100,000.")
        return passengers

    def clean(self):
        cleaned = super().clean()
        # No longer enforce vehicle_type == 'Car'
        if cleaned.get('number_of_passengers') in [None, 0]:
            self.add_error('number_of_passengers', "Number of passengers must be at least 1.")
        return cleaned

# Author: Ahmed Mohamed
class DriverForm(forms.ModelForm):
    """Form for driver details in a claim."""
    class Meta:
        model = Driver
        fields = ['driver_age', 'gender']
        widgets = {
            'driver_age': forms.NumberInput(attrs={'class': 'form-control', 'min': '16', 'max': '100', 'step': '1'}),
            'gender': forms.Select(choices=Driver._meta.get_field('gender').choices, attrs={'class': 'form-control'}),
        }

    def clean_driver_age(self):
        age = self.cleaned_data.get('driver_age')
        if age is None or age < 16 or age > 100:
            raise ValidationError("Driver age must be between 16 and 100.")
        return age

# Author: Ahmed Mohamed
class InjuryForm(forms.ModelForm):
    """Form for injury details in a claim."""
    class Meta:
        model = Injury
        fields = ['injury_prognosis', 'injury_description', 'dominant_injury',
                  'whiplash', 'minor_psychological_injury', 'exceptional_circumstances']
        widgets = {
            'injury_prognosis': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '60', 'step': '1'}),
            'injury_description': forms.Select(choices=Injury._meta.get_field('injury_description').choices, attrs={'class': 'form-control'}),
            'dominant_injury': forms.Select(choices=Injury._meta.get_field('dominant_injury').choices, attrs={'class': 'form-control'}),
            'whiplash': forms.Select(choices=[(True, 'Yes'), (False, 'No')], attrs={'class': 'form-control'}),
            'minor_psychological_injury': forms.Select(choices=[(True, 'Yes'), (False, 'No')], attrs={'class': 'form-control'}),
            'exceptional_circumstances': forms.Select(choices=[(True, 'Yes'), (False, 'No')], attrs={'class': 'form-control'}),
        }

    def clean_injury_prognosis(self):
        val = self.cleaned_data.get('injury_prognosis')
        if val is None or not isinstance(val, int) or val < 1 or val > 60:
            raise ValidationError("Prognosis must be a whole number of months between 1 and 60.")
        return val

    def clean(self):
        cleaned = super().clean()
        # Prevent 'Unknown' for categorical fields
        if cleaned.get('injury_description') == 'Unknown':
            self.add_error('injury_description', "Please select a valid injury description.")
        if cleaned.get('dominant_injury') == 'Unknown':
            self.add_error('dominant_injury', "Please select a valid dominant injury.")
        # Prevent zero or missing prognosis
        prognosis = cleaned.get('injury_prognosis')
        if prognosis in [None, 0]:
            self.add_error('injury_prognosis', "Prognosis must be at least 1 month.")
        return cleaned

# Author: Ahmed Mohamed
class ClaimSubmissionForm(forms.ModelForm):
    """Main form for claim submission that combines all related forms."""
    class Meta:
        model = Claim
        fields = [
            'special_health_expenses', 'special_reduction', 'special_overage',
            'general_rest', 'special_additional_injury', 'special_earnings_loss',
            'special_usage_loss', 'special_medications', 'special_asset_damage',
            'special_rehabilitation', 'special_fixes', 'general_fixed',
            'general_uplift', 'special_loaner_vehicle', 'special_trip_costs',
            'special_journey_expenses', 'special_therapy'
        ]
        widgets = {
            field: forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100000',
                'pattern': '^\\d+(\\.\\d{1,2})?$',
                'inputmode': 'decimal',
                'required': 'required',
            }) for field in fields
        }

    def __init__(self, *args, **kwargs):
        # Remove any outer prefix from kwargs to avoid conflicts with nested forms
        kwargs.pop('prefix', None)
        super().__init__(*args, **kwargs)
        # Initialize nested forms with explicit prefixes
        self.accident_form = AccidentForm(*args, prefix='accident', **kwargs)
        self.vehicle_form = VehicleForm(*args, prefix='vehicle', **kwargs)
        self.driver_form = DriverForm(*args, prefix='driver', **kwargs)
        self.injury_form = InjuryForm(*args, prefix='injury', **kwargs)
        # Make all fields required
        for field in self.fields.values():
            field.required = True

    def clean(self):
        cleaned = super().clean()
        # Enforce all numeric fields are >=0, <=100000, and max 2 decimal places
        for field_name, field in self.fields.items():
            val = cleaned.get(field_name)
            if val is None:
                self.add_error(field_name, "This field is required.")
            elif val < 0:
                self.add_error(field_name, "Value cannot be negative.")
            elif val > 100000:
                self.add_error(field_name, "Value cannot exceed 100,000.")
            elif hasattr(val, 'as_tuple'):
                # Decimal: check decimal places
                if abs(val.as_tuple().exponent) > 2:
                    self.add_error(field_name, "Max 2 decimal places allowed.")
        return cleaned

    def is_valid(self):
        """Validate all forms."""
        return all([
            super().is_valid(),
            self.accident_form.is_valid(),
            self.vehicle_form.is_valid(),
            self.driver_form.is_valid(),
            self.injury_form.is_valid()
        ])

    def save(self, commit=True):
        """Save all related forms and link them together."""
        if not self.is_valid():
            raise ValueError("Form is not valid")

        # Save accident first
        accident = self.accident_form.save(commit=commit)

        # Save related models and link to accident
        if commit:
            vehicle = self.vehicle_form.save(commit=False)
            vehicle.accident = accident
            vehicle.save()

            driver = self.driver_form.save(commit=False)
            driver.accident = accident
            driver.save()

            injury = self.injury_form.save(commit=False)
            injury.accident = accident
            injury.save()

        # Save main claim
        claim = super().save(commit=False)
        claim.accident = accident
        if commit:
            claim.save()

        return claim