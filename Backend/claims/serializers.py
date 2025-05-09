# claims/serializers.py
from rest_framework import serializers
from .models import Claim, Accident, Driver, Vehicle, Injury

class AccidentExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accident
        fields = '__all__'

class DriverExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = '__all__'

class VehicleExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class InjuryExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Injury
        fields = '__all__'

class ClaimExportSerializer(serializers.ModelSerializer):
    accident = AccidentExportSerializer()
    driver = serializers.SerializerMethodField()
    vehicle = serializers.SerializerMethodField()
    injury = serializers.SerializerMethodField()

    class Meta:
        model = Claim
        fields = '__all__'

    def get_driver(self, obj):
        if obj.accident and hasattr(obj.accident, 'driver'):
            driver = Driver.objects.filter(accident=obj.accident).first()
            return DriverExportSerializer(driver).data if driver else None
        return None

    def get_vehicle(self, obj):
        if obj.accident and hasattr(obj.accident, 'vehicle'):
            vehicle = Vehicle.objects.filter(accident=obj.accident).first()
            return VehicleExportSerializer(vehicle).data if vehicle else None
        return None

    def get_injury(self, obj):
        if obj.accident and hasattr(obj.accident, 'injury'):
            injury = Injury.objects.filter(accident=obj.accident).first()
            return InjuryExportSerializer(injury).data if injury else None
        return None 