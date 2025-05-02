# claims/models.py
from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.core.validators import MinValueValidator

# Add choices constants (from models.py.new)
ACCIDENT_TYPE_CHOICES = [
    ('Rear end', 'Rear end'),
    ('Other side pulled out of side road', 'Other side pulled out of side road'),
    ('Other side pulled on to roundabout', 'Other side pulled on to roundabout'),
    ("Other side reversed into Clt's vehicle", "Other side reversed into Clt's vehicle"),
    ("Other side changed lanes and collided with clt's vehicle", "Other side changed lanes and collided with clt's vehicle"),
    ('Unknown', 'Unknown'),
]
ACCIDENT_DESCRIPTION_CHOICES = [
    ('Side collision at an intersection.','Side collision at an intersection.'),
    ('Rear-ended at a stoplight.', 'Rear-ended at a stoplight.'),
    ('Swerved to avoid another vehicle.', 'Swerved to avoid another vehicle.'),
    ('Hit a deer on the highway.', 'Hit a deer on the highway.'),
    ('Lost control on a snowy road.', 'Lost control on a snowy road.'),
    ('Unknown', 'Unknown'),
]
WEATHER_CONDITIONS_CHOICES = [
    ('Sunny', 'Sunny'),
    ('Rainy', 'Rainy'),
    ('Snowy', 'Snowy'),
    ('Unknown', 'Unknown'),
]
VEHICLE_TYPE_CHOICES = [
    ('Motorcycle', 'Motorcycle'),
    ('Car', 'Car'),
    ('Truck', 'Truck'),
    ('Unknown', 'Unknown'),
]
GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]
INJURY_DESCRIPTION_CHOICES = [
    ('Whiplash and minor bruises', 'Whiplash and minor bruises'),
    ('Concussion and bruised ribs', 'Concussion and bruised ribs'),
    ('Minor cuts and scrapes', 'Minor cuts and scrapes'),
    ('Fractured arm and leg', 'Fractured arm and leg'),
    ('Sprained ankle and wrist', 'Sprained ankle and wrist'),
    ('Unknown', 'Unknown'),
]
DOMINANT_INJURY_CHOICES = [
    ('Legs', 'Legs'),
    ('Arms', 'Arms'),
    ('Hips', 'Hips'),
    ('Multiple', 'Multiple'),
    ('Unknown', 'Unknown'),
]

class Accident(models.Model):
    """
    Represents an accident reported by a user, including key details
    such as date, type, and any police reports or witnesses.
    """
    reported_by = models.ForeignKey(
        # settings.AUTH_USER_MODEL,
        'authentication.CustomUser',
        on_delete=models.CASCADE,
        related_name='accidents',
        null=True,
        blank=True
    )
    accident_date = models.DateTimeField(default=now)
    accident_type = models.CharField(max_length=255, choices=ACCIDENT_TYPE_CHOICES, blank=False, null=False, default='Unknown')
    accident_description = models.TextField(blank=False, null=False, default='Unknown')
    police_report_filed = models.BooleanField(default=False)
    witness_present = models.BooleanField(default=False)
    weather_conditions = models.CharField(max_length=255, choices=WEATHER_CONDITIONS_CHOICES, blank=False, null=False, default='Unknown')

    def __str__(self):
        return f"Accident {self.id} - {self.accident_type} on {self.accident_date}"


class Claim(models.Model):
    """
    Represents an insurance claim linked to a particular accident.
    Stores financial details and, optionally, a prediction result
    from an external MLaaS service.
    """
    accident = models.ForeignKey(
        Accident,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    claim_date = models.DateTimeField(default=now)
    settlement_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_health_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_reduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_overage = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    general_rest = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_additional_injury = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_earnings_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_usage_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_medications = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_asset_damage = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_rehabilitation = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_fixes = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    general_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    general_uplift = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_loaner_vehicle = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_trip_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_journey_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_therapy = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Field added to store ML predictions from the external MLaaS service
    prediction_result = models.JSONField(
        null=True,
        blank=True,
        help_text="Stores ML prediction data (e.g. {'predicted_value': 1000.00})."
    )

    def __str__(self):
        return f"Claim {self.id} - Accident {self.accident_id if self.accident else 'N/A'}"


class Vehicle(models.Model):
    """
    Represents a vehicle involved in an accident, including its age,
    type, and the number of passengers onboard.
    """
    accident = models.ForeignKey(
        Accident,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    vehicle_age = models.IntegerField(default=0)
    vehicle_type = models.CharField(max_length=255, choices=VEHICLE_TYPE_CHOICES, blank=False, null=False, default='Unknown')
    number_of_passengers = models.IntegerField(default=1, blank=False, null=False, validators=[MinValueValidator(1)], help_text="Number of passengers must be at least 1")

    def __str__(self):
        return f"Vehicle {self.id} - {self.vehicle_type if self.vehicle_type else 'Unknown'}"


class Driver(models.Model):
    """
    Represents a driver involved in an accident, storing age and gender.
    """
    accident = models.ForeignKey(
        Accident,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    driver_age = models.IntegerField(default=18)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=False, null=False, default='Other')

    def __str__(self):
        return f"Driver {self.id} - Age {self.driver_age}"


class Injury(models.Model):
    """
    Represents injuries sustained in an accident. Each Injury entry
    captures the type, prognosis, and any special conditions.
    """
    accident = models.ForeignKey(
        Accident,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    injury_prognosis = models.IntegerField(
        blank=False, null=False, default=1,
        validators=[MinValueValidator(1)],
        help_text="Prognosis in months (whole number, must be at least 1)"
    )
    injury_description = models.CharField(max_length=255, choices=INJURY_DESCRIPTION_CHOICES, blank=False, null=False, default='Unknown')
    dominant_injury = models.CharField(max_length=255, choices=DOMINANT_INJURY_CHOICES, blank=False, null=False, default='Unknown')
    whiplash = models.BooleanField(default=False)
    minor_psychological_injury = models.BooleanField(default=False)
    exceptional_circumstances = models.BooleanField(default=False)

    def __str__(self):
        return f"Injury {self.id} - {self.dominant_injury if self.dominant_injury else 'Unknown'}"
