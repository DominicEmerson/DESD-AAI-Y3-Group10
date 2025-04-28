# claims/models.py
from django.db import models
from django.conf import settings
from django.utils.timezone import now

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
    accident_type = models.CharField(max_length=255)
    accident_description = models.TextField(blank=True, null=True)
    police_report_filed = models.BooleanField(default=False)
    witness_present = models.BooleanField(default=False)
    weather_conditions = models.CharField(max_length=255, blank=True, null=True)

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
    vehicle_type = models.CharField(max_length=255, blank=True, null=True)
    number_of_passengers = models.IntegerField(default=0)

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
    gender = models.CharField(
        max_length=10,
        choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")],
        blank=True,
        null=True
    )

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
    injury_prognosis = models.CharField(max_length=255, blank=True, null=True)
    injury_description = models.TextField(blank=True, null=True)
    dominant_injury = models.CharField(max_length=255, blank=True, null=True)
    whiplash = models.BooleanField(default=False)
    minor_psychological_injury = models.BooleanField(default=False)
    exceptional_circumstances = models.BooleanField(default=False)

    def __str__(self):
        return f"Injury {self.id} - {self.dominant_injury if self.dominant_injury else 'Unknown'}"
