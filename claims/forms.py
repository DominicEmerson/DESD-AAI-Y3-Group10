# claims/forms.py

from re import A
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Accident, Claim, Vehicle, Driver, Injury
from .models import CustomUser



User = get_user_model()

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Passwords do not match.")
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'enduser'
        if commit:
            user.save()
        return user
    

class CreateUserForm(UserCreationForm):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('engineer', 'Engineer'),
        ('finance', 'Finance'),
        ('enduser', 'End User'),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get('role')
        user.role = role
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role in ['engineer', 'finance']:
            user.is_staff = True
            user.is_superuser = False
        else:  # 'enduser'
            user.is_staff = False
            user.is_superuser = False

        if commit:
            user.save()

        return user

# Author: Ahmed Mohamed
class AccidentForm(forms.ModelForm):
    """Form for accident details in a claim."""
    class Meta:
        model = Accident
        fields = ['accident_date', 'accident_type', 'accident_description',
                  'police_report_filed', 'witness_present', 'weather_conditions']
        widgets = {
            'accident_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'accident_type': forms.TextInput(attrs={'class': 'form-control'}),
            'accident_description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'weather_conditions': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_accident_date(self):
        date = self.cleaned_data.get('accident_date')
        if date and date > timezone.now():
            raise ValidationError("Accident date cannot be in the future.")
        return date

# Author: Ahmed Mohamed
class VehicleForm(forms.ModelForm):
    """Form for vehicle details in a claim."""
    class Meta:
        model = Vehicle
        fields = ['vehicle_age', 'vehicle_type', 'number_of_passengers']
        widgets = {
            'vehicle_age': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'vehicle_type': forms.TextInput(attrs={'class': 'form-control'}),
            'number_of_passengers': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def clean_vehicle_age(self):
        age = self.cleaned_data.get('vehicle_age')
        if age and age < 0:
            raise ValidationError("Vehicle age cannot be negative.")
        return age

    def clean_number_of_passengers(self):
        passengers = self.cleaned_data.get('number_of_passengers')
        if passengers and passengers < 0:
            raise ValidationError("Number of passengers cannot be negative.")
        return passengers

# Author: Ahmed Mohamed
class DriverForm(forms.ModelForm):
    """Form for driver details in a claim."""
    class Meta:
        model = Driver
        fields = ['driver_age', 'gender']
        widgets = {
            'driver_age': forms.NumberInput(attrs={'class': 'form-control', 'min': '16'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_driver_age(self):
        age = self.cleaned_data.get('driver_age')
        if age and age < 16:
            raise ValidationError("Driver must be at least 16 years old.")
        elif age and age > 100:
            raise ValidationError("Please verify the driver's age.")
        return age

# Author: Ahmed Mohamed
class InjuryForm(forms.ModelForm):
    """Form for injury details in a claim."""
    class Meta:
        model = Injury
        fields = ['injury_prognosis', 'injury_description', 'dominant_injury',
                  'whiplash', 'minor_psychological_injury', 'exceptional_circumstances']
        widgets = {
            'injury_prognosis': forms.TextInput(attrs={'class': 'form-control'}),
            'injury_description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'dominant_injury': forms.TextInput(attrs={'class': 'form-control'}),
        }

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
                'min': '0'
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


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label='Enter your email', max_length=255)