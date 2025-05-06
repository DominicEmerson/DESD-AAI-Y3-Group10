# claims/models.py
from django.db import models  # Import models from Django ORM
from django.conf import settings  # Import settings for configuration
from django.utils.timezone import now  # Import now for current timestamp
from django.core.validators import MinValueValidator, MaxValueValidator  # Import validators for model fields

# Add choices constants (from models.py.new)
ACCIDENT_TYPE_CHOICES = [
    ('Rear end', 'Rear end'),  # Choice for rear-end accident type
    ('Other side pulled out of side road', 'Other side pulled out of side road'),  # Choice for other side pulled out
    ('Other side pulled on to roundabout', 'Other side pulled on to roundabout'),  # Choice for other side on roundabout
    ("Other side reversed into Clt's vehicle", "Other side reversed into Clt's vehicle"),  # Choice for reverse collision
    ("Other side changed lanes and collided with clt's vehicle", "Other side changed lanes and collided with clt's vehicle"),  # Choice for lane change collision
    ('Unknown', 'Unknown'),  # Choice for unknown accident type
]
ACCIDENT_DESCRIPTION_CHOICES = [
    ('Side collision at an intersection.','Side collision at an intersection.'),  # Description for side collision
    ('Rear-ended at a stoplight.', 'Rear-ended at a stoplight.'),  # Description for rear-ended accident
    ('Swerved to avoid another vehicle.', 'Swerved to avoid another vehicle.'),  # Description for swerving accident
    ('Hit a deer on the highway.', 'Hit a deer on the highway.'),  # Description for hitting a deer
    ('Lost control on a snowy road.', 'Lost control on a snowy road.'),  # Description for losing control
    ('Unknown', 'Unknown'),  # Description for unknown accident
]
WEATHER_CONDITIONS_CHOICES = [
    ('Sunny', 'Sunny'),  # Choice for sunny weather
    ('Rainy', 'Rainy'),  # Choice for rainy weather
    ('Snowy', 'Snowy'),  # Choice for snowy weather
    ('Unknown', 'Unknown'),  # Choice for unknown weather
]
VEHICLE_TYPE_CHOICES = [
    ('Motorcycle', 'Motorcycle'),  # Choice for motorcycle
    ('Car', 'Car'),  # Choice for car
    ('Truck', 'Truck'),  # Choice for truck
    ('Unknown', 'Unknown'),  # Choice for unknown vehicle type
]
GENDER_CHOICES = [
    ('Male', 'Male'),  # Choice for male gender
    ('Female', 'Female'),  # Choice for female gender
    ('Other', 'Other'),  # Choice for other gender
]
INJURY_DESCRIPTION_CHOICES = [
    ('Whiplash and minor bruises', 'Whiplash and minor bruises'),  # Description for whiplash
    ('Concussion and bruised ribs', 'Concussion and bruised ribs'),  # Description for concussion
    ('Minor cuts and scrapes', 'Minor cuts and scrapes'),  # Description for minor injuries
    ('Fractured arm and leg', 'Fractured arm and leg'),  # Description for fractures
    ('Sprained ankle and wrist', 'Sprained ankle and wrist'),  # Description for sprains
    ('Unknown', 'Unknown'),  # Description for unknown injuries
]
DOMINANT_INJURY_CHOICES = [
    ('Legs', 'Legs'),  # Choice for leg injuries
    ('Arms', 'Arms'),  # Choice for arm injuries
    ('Hips', 'Hips'),  # Choice for hip injuries
    ('Multiple', 'Multiple'),  # Choice for multiple injuries
    ('Unknown', 'Unknown'),  # Choice for unknown dominant injury
]

class Accident(models.Model):
    """
    Represents an accident reported by a user, including key details
    such as date, type, and any police reports or witnesses.
    """
    reported_by = models.ForeignKey(
        'authentication.CustomUser',  # Reference to the user who reported the accident
        on_delete=models.CASCADE,
        related_name='accidents',  # Related name for accessing accidents from user
        null=True,
        blank=True
    )
    accident_date = models.DateTimeField(default=now)  # Date of the accident
    accident_type = models.CharField(max_length=255, choices=ACCIDENT_TYPE_CHOICES, blank=False, null=False, default='Unknown')  # Type of accident
    accident_description = models.TextField(blank=False, null=False, default='Unknown')  # Description of the accident
    police_report_filed = models.BooleanField(default=False)  # Indicates if a police report was filed
    witness_present = models.BooleanField(default=False)  # Indicates if witnesses were present
    weather_conditions = models.CharField(max_length=255, choices=WEATHER_CONDITIONS_CHOICES, blank=False, null=False, default='Unknown')  # Weather conditions during the accident

    def __str__(self):
        return f"Accident {self.id} - {self.accident_type} on {self.accident_date}"  # String representation of the accident

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
    claim_date = models.DateTimeField(default=now)  # Date of the claim submission
    settlement_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Settlement value of the claim
    special_health_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Special health expenses
    special_reduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Special reduction
    special_overage = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Special overage
    general_rest = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # General rest
    special_additional_injury = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Special additional injury
    special_earnings_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Special earnings loss
    special_usage_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Special usage loss
    special_medications = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Special medications
    special_asset_damage = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Special asset damage
    special_rehabilitation = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Special rehabilitation
    special_fixes = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Special fixes
    general_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # General fixed
    general_uplift = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # General uplift
    special_loaner_vehicle = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Special loaner vehicle
    special_trip_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Special trip costs
    special_journey_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Special journey expenses
    special_therapy = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False, null=False, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Special therapy

    # Field added to store ML predictions from the external MLaaS service
    prediction_result = models.JSONField(
        null=True,
        blank=True,
        help_text="Stores ML prediction data (e.g. {'predicted_value': 1000.00})."  # Help text for prediction result
    )

    def __str__(self):
        return f"Claim {self.id} - Accident {self.accident_id if self.accident else 'N/A'}"  # String representation of the claim

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
    vehicle_age = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100000)])  # Age of the vehicle
    vehicle_type = models.CharField(max_length=255, choices=VEHICLE_TYPE_CHOICES, blank=False, null=False, default='Unknown')  # Type of vehicle
    number_of_passengers = models.IntegerField(default=1, blank=False, null=False, validators=[MinValueValidator(1), MaxValueValidator(100000)])  # Number of passengers in the vehicle

    def __str__(self):
        return f"Vehicle {self.id} - {self.vehicle_type if self.vehicle_type else 'Unknown'}"  # String representation of the vehicle

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
    driver_age = models.IntegerField(default=18)  # Age of the driver
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=False, null=False, default='Other')  # Gender of the driver

    def __str__(self):
        return f"Driver {self.id} - Age {self.driver_age}"  # String representation of the driver

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
        validators=[MinValueValidator(1)],  # Ensure prognosis is at least 1 month
        help_text="Prognosis in months (whole number, must be at least 1)"  # Help text for prognosis
    )
    injury_description = models.CharField(max_length=255, choices=INJURY_DESCRIPTION_CHOICES, blank=False, null=False, default='Unknown')  # Description of the injury
    dominant_injury = models.CharField(max_length=255, choices=DOMINANT_INJURY_CHOICES, blank=False, null=False, default='Unknown')  # Dominant injury type
    whiplash = models.BooleanField(default=False)  # Indicates if whiplash is present
    minor_psychological_injury = models.BooleanField(default=False)  # Indicates if there is a minor psychological injury
    exceptional_circumstances = models.BooleanField(default=False)  # Indicates if there are exceptional circumstances

    def __str__(self):
        return f"Injury {self.id} - {self.dominant_injury if self.dominant_injury else 'Unknown'}"  # String representation of the injury