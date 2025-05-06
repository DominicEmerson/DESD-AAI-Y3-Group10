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

    first_name = forms.CharField(max_length=30, required=True, label="First name")
    last_name  = forms.CharField(max_length=30, required=True, label="Last name")
    role       = forms.ChoiceField(choices=ROLE_CHOICES, required=True)
    password1  = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2  = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model  = CustomUser
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'password1',
            'password2',
        ]

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        # Assign the new fields
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.role       = self.cleaned_data['role']

        # Set staff/superuser flags per role
        if user.role == 'admin':
            user.is_staff     = True
            user.is_superuser = True
        elif user.role in ['engineer', 'finance']:
            user.is_staff     = True
            user.is_superuser = False
        else:  # 'enduser'
            user.is_staff     = False
            user.is_superuser = False

        if commit:
            user.save()
        return user