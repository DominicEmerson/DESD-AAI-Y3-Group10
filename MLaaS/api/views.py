from django.shortcuts import render

# api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
import pickle

class MLInferenceView(APIView):
    def post(self, request):
        try:
            data = request.data
            with open('ml_models/model.pkl', 'rb') as f:
                model = pickle.load(f)
            prediction = model.predict([data['features']])
            return Response({'prediction': prediction.tolist()})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
