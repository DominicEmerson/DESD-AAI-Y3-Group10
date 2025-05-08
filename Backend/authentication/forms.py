# authentication/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone


User = get_user_model()
class SignupForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.CharField(
        max_length=254,
        required=True, 
    )
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'password_confirm',
        ]

    def clean_password_confirm(self):
        pw = self.cleaned_data.get('password')
        pwc = self.cleaned_data.get('password_confirm')
        if pw and pwc and pw != pwc:
            raise ValidationError("Passwords do not match.")
        return pwc

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'enduser'
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user
class ForgotPasswordForm(forms.Form):
    email = forms.CharField(label='Enter your email', max_length=255)