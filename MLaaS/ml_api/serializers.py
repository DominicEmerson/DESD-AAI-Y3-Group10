from rest_framework import serializers
from claims.models import Endpoint, MLAlgorithm, MLRequest

class EndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endpoint
        fields = '__all__'

class MLAlgorithmSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLAlgorithm
        fields = '__all__'

class MLRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLRequest
        fields = '__all__'

class PredictionSerializer(serializers.Serializer):
    input_data = serializers.JSONField()
    algorithm_name = serializers.CharField(max_length=128)
