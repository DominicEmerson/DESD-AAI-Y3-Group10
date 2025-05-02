from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.db import transaction, IntegrityError
from claims.models import Accident, Claim, Vehicle, Driver, Injury
import csv
import os
import time
from decimal import Decimal

class Command(BaseCommand):
    help = "Imports insurance claims data from CSV into database models"

    def handle(self, *args, **kwargs):
        csv_path = os.path.join(os.path.dirname(__file__), 'clean_df.csv')
        
        with open(csv_path, 'r') as file, transaction.atomic():
            reader = csv.DictReader(file)
            
            for row_idx, row in enumerate(reader, 1):
                try:
                    with transaction.atomic():
                        # Create Accident
                        accident = Accident.objects.create(
                            accident_date=parse_datetime(row['accidentdate'].replace('/', '-')),
                            accident_type=row['accidenttype'],
                            accident_description=row['accidentdescription'],
                            police_report_filed=bool(float(row['policereportfiled'])),
                            witness_present=bool(float(row['witnesspresent'])),
                            weather_conditions=row['weatherconditions']
                        )
                        accident.save()

                        # Create Claim
                        claim = Claim.objects.create(
                            accident=accident,
                            claim_date=parse_datetime(row['claimdate'].replace('/', '-')),
                            settlement_value=Decimal(row['settlementvalue']),
                            special_health_expenses=Decimal(row['specialhealthexpenses']),
                            special_reduction=Decimal(row['specialreduction']),
                            special_overage=Decimal(row['specialoverage']), 
                            general_rest=Decimal(row['generalrest']),
                            special_additional_injury=Decimal(row['specialadditionalinjury']),
                            special_earnings_loss=Decimal(row['specialearningsloss']),
                            special_usage_loss=Decimal(row['specialusageloss']),
                            special_medications=Decimal(row['specialmedications']),
                            special_asset_damage=Decimal(row['specialassetdamage']),
                            special_rehabilitation=Decimal(row['specialrehabilitation']),
                            special_fixes=Decimal(row['specialfixes']),
                            general_fixed=Decimal(row['generalfixed']),
                            general_uplift=Decimal(row['generaluplift']),
                            special_loaner_vehicle=Decimal(row['specialloanervehicle']),
                        )
                        claim.save()

                        # Create Vehicle
                        vehicle = Vehicle.objects.create(
                            accident=accident,
                            vehicle_age=int(float(row['vehicleage'])),
                            vehicle_type=row['vehicletype'],
                            number_of_passengers=int(float(row['numberofpassengers']))
                        )
                        vehicle.save()

                        # Create Driver
                        driver = Driver.objects.create(
                            accident=accident,
                            driver_age=int(float(row['driverage'])),
                            gender=row['gender']
                        )
                        driver.save()

                        # Create Injury
                        injury = Injury.objects.create(
                            accident=accident,
                            injury_prognosis=row['injuryprognosis'],
                            injury_description=row['injurydescription'],
                            dominant_injury=row['dominantinjury'],
                            whiplash=bool(float(row['whiplash'])),
                            minor_psychological_injury=bool(float(row['minorpsychologicalinjury'])),
                            exceptional_circumstances=bool(float(row['exceptionalcircumstances']))
                        )
                        injury.save()

                        time.sleep(0.1)  # Pause for 0.1 seconds between each row processing

                except IntegrityError as e:
                    
                    self.stdout.write(self.style.ERROR(
                        f"Error processing row {row_idx}: {str(e)}. "
                        f"Row data: {dict(row.items())}"
                    ))
                    continue

            self.stdout.write(self.style.SUCCESS(
                f"Successfully imported {row_idx} records"
            ))
