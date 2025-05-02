# backend/engineer/apps.py
from django.apps import AppConfig


class EngineerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'engineer'
    
    def ready(self):
        import authentication.signals
