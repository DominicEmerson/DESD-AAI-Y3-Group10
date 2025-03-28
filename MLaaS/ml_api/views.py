from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Endpoint, MLAlgorithm, MLRequest
from .serializers import (
    EndpointSerializer,
    MLAlgorithmSerializer,
    MLRequestSerializer,
    PredictionSerializer
)
import joblib
import numpy as np
from datetime import datetime
import time

class EndpointViewSet(viewsets.ModelViewSet):
    queryset = Endpoint.objects.all()
    serializer_class = EndpointSerializer

class MLAlgorithmViewSet(viewsets.ModelViewSet):
    queryset = MLAlgorithm.objects.all()
    serializer_class = MLAlgorithmSerializer

    @action(detail=True, methods=['post'])
    def predict(self, request, pk=None):
        algorithm = self.get_object()
        serializer = PredictionSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Load the model
                model = joblib.load(algorithm.model_file.path)
                
                # Record start time
                start_time = time.time()
                
                # Make prediction
                input_data = np.array(serializer.validated_data['input_data'])
                prediction = model.predict(input_data)
                
                # Calculate response time
                response_time = time.time() - start_time
                
                # Create ML request record
                ml_request = MLRequest.objects.create(
                    input_data=serializer.validated_data['input_data'],
                    prediction=prediction.tolist(),
                    algorithm=algorithm,
                    response_time=response_time
                )
                
                return Response(
                    {'prediction': prediction.tolist(), 'request_id': ml_request.id},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class MLRequestViewSet(viewsets.ModelViewSet):
    queryset = MLRequest.objects.all()
    serializer_class = MLRequestSerializer
