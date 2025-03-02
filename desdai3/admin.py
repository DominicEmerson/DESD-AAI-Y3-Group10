from django.contrib import admin
from .models import Accident, Claim, Driver, Vehicle, Injury

admin.site.register(Accident)
admin.site.register(Claim)
admin.site.register(Driver)
admin.site.register(Vehicle)
admin.site.register(Injury)
