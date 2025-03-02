from django.db import models
from django.utils.timezone import now  # Import 'now' for default timestamps


class Accident(models.Model):
    accident_date = models.DateTimeField(default=now)  # Default to current timestamp
    accident_type = models.CharField(max_length=255)
    accident_description = models.TextField(blank=True, null=True)
    police_report_filed = models.BooleanField(default=False)
    witness_present = models.BooleanField(default=False)
    weather_conditions = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Accident {self.id} - {self.accident_type} on {self.accident_date}"


class Claim(models.Model):
    accident = models.ForeignKey(Accident, on_delete=models.CASCADE, null=True, blank=True)
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

    def __str__(self):
        return f"Claim {self.id} - Accident {self.accident_id if self.accident else 'N/A'}"


class Vehicle(models.Model):
    accident = models.ForeignKey(Accident, on_delete=models.CASCADE, null=True, blank=True)
    vehicle_age = models.IntegerField(default=0)  # Default age is 0 if unknown
    vehicle_type = models.CharField(max_length=255, blank=True, null=True)
    number_of_passengers = models.IntegerField(default=0)  # Default to 0 for empty vehicles

    def __str__(self):
        return f"Vehicle {self.id} - {self.vehicle_type if self.vehicle_type else 'Unknown'}"


class Driver(models.Model):
    accident = models.ForeignKey(Accident, on_delete=models.CASCADE, null=True, blank=True)
    driver_age = models.IntegerField(default=18)  # Default to 18 assuming minimum age
    gender = models.CharField(
        max_length=10,
        choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")],
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Driver {self.id} - Age {self.driver_age}"


class Injury(models.Model):
    accident = models.ForeignKey(Accident, on_delete=models.CASCADE, null=True, blank=True)
    injury_prognosis = models.CharField(max_length=255, blank=True, null=True)
    injury_description = models.TextField(blank=True, null=True)
    dominant_injury = models.CharField(max_length=255, blank=True, null=True)
    whiplash = models.BooleanField(default=False)
    minor_psychological_injury = models.BooleanField(default=False)
    exceptional_circumstances = models.BooleanField(default=False)

    def __str__(self):
        return f"Injury {self.id} - {self.dominant_injury if self.dominant_injury else 'Unknown'}"
