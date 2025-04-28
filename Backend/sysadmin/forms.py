# sysadmin/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from authentication.models import CustomUser

class CreateUserForm(UserCreationForm):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('engineer', 'Engineer'),
        ('finance', 'Finance'),
        ('enduser', 'End User'),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get('role')
        user.role = role
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role in ['engineer', 'finance']:
            user.is_staff = True
            user.is_superuser = False
        else:  # 'enduser'
            user.is_staff = False
            user.is_superuser = False

        if commit:
            user.save()

        return user