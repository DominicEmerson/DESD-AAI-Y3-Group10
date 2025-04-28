from django.contrib import admin
from claims.models import Accident, Claim, Vehicle, Driver, Injury

# Registering new models for claims
admin.site.register(Accident)
admin.site.register(Claim)
admin.site.register(Vehicle)
admin.site.register(Driver)
admin.site.register(Injury)