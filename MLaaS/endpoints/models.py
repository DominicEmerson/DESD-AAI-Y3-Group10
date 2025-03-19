from django.db import models

# endpoints/models.py
class Endpoint(models.Model):
    name = models.CharField(max_length=128)
    owner = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

class MLAlgorithm(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    version = models.CharField(max_length=128)
    code = models.TextField()  # For small model code
    model_file = models.FileField(upload_to='ml_models/')
    parent_endpoint = models.ForeignKey(Endpoint, on_delete=models.CASCADE)
