from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from authentication.models import CustomUser

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