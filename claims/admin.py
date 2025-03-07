from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Accident, Claim, Vehicle, Driver, Injury

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('role',)}),
    )

# Register CustomUser model with custom admin
admin.site.register(CustomUser, CustomUserAdmin)

# Registering new models for claims
admin.site.register(Accident)
admin.site.register(Claim)
admin.site.register(Vehicle)
admin.site.register(Driver)
admin.site.register(Injury)
