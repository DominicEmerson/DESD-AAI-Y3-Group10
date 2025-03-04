from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view

def home(request):
    return render(request, "index.html")

@api_view(["GET"])
def hello_world(request):
    return JsonResponse({"message": "Hello, world!"})
