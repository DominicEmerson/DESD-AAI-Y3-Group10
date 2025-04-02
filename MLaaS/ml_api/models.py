from django.db import models

class Endpoint(models.Model):
    name = models.CharField(max_length=128)
    owner = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.owner}"

class MLAlgorithm(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    version = models.CharField(max_length=128)
    code = models.TextField()  # For small model code
    model_file = models.FileField(upload_to='ml_models/')
    parent_endpoint = models.ForeignKey(Endpoint, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} v{self.version}"

class MLRequest(models.Model):
    input_data = models.JSONField()
    prediction = models.JSONField(null=True)
    algorithm = models.ForeignKey(MLAlgorithm, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    response_time = models.FloatField(null=True)  # in seconds

    def __str__(self):
        return f"Request for {self.algorithm.name} at {self.created_at}"
