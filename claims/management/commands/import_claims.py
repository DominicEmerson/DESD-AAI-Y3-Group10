import csv
from django.core.management.base import BaseCommand
from claims.models import Accident, Claim, Vehicle, Driver, Injury
from django.utils.timezone import make_aware
from datetime import datetime

class Command(BaseCommand):
    help = 'Import claims data from CSV'

    def handle(self, *args, **kwargs):
        file_path = 'claims/management/commands/Synthetic_Data_For_Students.csv'  # Adjust if needed

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                try:
                    # Handles Date Parsing with Fallbacks
                    try:
                        accident_date = make_aware(datetime.strptime(row['Accident Date'], "%Y-%m-%d %H:%M:%S.%f"))
                    except ValueError:
                        accident_date = make_aware(datetime.strptime(row['Accident Date'], "%Y-%m-%d %H:%M:%S"))

                    try:
                        claim_date = make_aware(datetime.strptime(row['Claim Date'], "%Y-%m-%d %H:%M:%S.%f"))
                    except ValueError:
                        claim_date = make_aware(datetime.strptime(row['Claim Date'], "%Y-%m-%d %H:%M:%S"))

                    # Create or Get Accident
                    accident, _ = Accident.objects.get_or_create(
                        accident_date=accident_date,
                        accident_type=row.get('AccidentType', 'Unknown'),
                        accident_description=row.get('Accident Description', 'No Description'),
                        police_report_filed=row.get('Police Report Filed', 'no').strip().lower() == 'yes',
                        witness_present=row.get('Witness Present', 'no').strip().lower() == 'yes',
                        weather_conditions=row.get('Weather Conditions', 'Unknown')
                    )

                    # Create Claim
                    Claim.objects.create(
                        accident=accident,
                        claim_date=claim_date,
                        settlement_value=float(row.get('SettlementValue', 0) or 0.00),
                        special_health_expenses=float(row.get('SpecialHealthExpenses', 0) or 0.00),
                        special_reduction=float(row.get('SpecialReduction', 0) or 0.00),
                        special_overage=float(row.get('SpecialOverage', 0) or 0.00),
                        general_rest=float(row.get('GeneralRest', 0) or 0.00),
                        special_additional_injury=float(row.get('SpecialAdditionalInjury', 0) or 0.00),
                        special_earnings_loss=float(row.get('SpecialEarningsLoss', 0) or 0.00),
                        special_usage_loss=float(row.get('SpecialUsageLoss', 0) or 0.00),
                        special_medications=float(row.get('SpecialMedications', 0) or 0.00),
                        special_asset_damage=float(row.get('SpecialAssetDamage', 0) or 0.00),
                        special_rehabilitation=float(row.get('SpecialRehabilitation', 0) or 0.00),
                        special_fixes=float(row.get('SpecialFixes', 0) or 0.00),
                        general_fixed=float(row.get('GeneralFixed', 0) or 0.00),
                        general_uplift=float(row.get('GeneralUplift', 0) or 0.00),
                        special_loaner_vehicle=float(row.get('SpecialLoanerVehicle', 0) or 0.00),
                        special_trip_costs=float(row.get('SpecialTripCosts', 0) or 0.00),
                        special_journey_expenses=float(row.get('SpecialJourneyExpenses', 0) or 0.00),
                        special_therapy=float(row.get('SpecialTherapy', 0) or 0.00)
                    )

                    # Create Vehicle
                    Vehicle.objects.create(
                        accident=accident,
                        vehicle_age=int(float(row.get('Vehicle Age', 0) or 0)),
                        vehicle_type=row.get('Vehicle Type', 'Unknown'),
                        number_of_passengers=int(float(row.get('Number of Passengers', 0) or 0))
                    )

                    # Create Driver
                    Driver.objects.create(
                        accident=accident,
                        driver_age=int(float(row.get('Driver Age', 18) or 18)),
                        gender=row.get('Gender', 'Unknown')
                    )

                    # Create Injury
                    Injury.objects.create(
                        accident=accident,
                        injury_prognosis=row.get('Injury_Prognosis', 'Unknown'),
                        injury_description=row.get('Injury Description', 'No Description'),
                        dominant_injury=row.get('Dominant injury', 'Unknown'),
                        whiplash=row.get('Whiplash', 'no').strip().lower() == 'yes',
                        minor_psychological_injury=row.get('Minor_Psychological_Injury', 'no').strip().lower() == 'yes',
                        exceptional_circumstances=row.get('Exceptional_Circumstances', 'no').strip().lower() == 'yes'
                    )

                    self.stdout.write(self.style.SUCCESS(f"✔ Successfully added claim for accident on {accident_date}"))

                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"❌ Error processing row: {row}\n{e}"))