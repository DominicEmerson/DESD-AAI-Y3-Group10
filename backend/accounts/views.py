# backend/accounts/views.py
from django.http import JsonResponse
from rest_framework.decorators import api_view

@api_view(["GET"])
def hello_user(request):
    return JsonResponse({"message": "Hello, User!"})
