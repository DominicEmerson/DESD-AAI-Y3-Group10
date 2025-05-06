# authentication/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV3

User = get_user_model()

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    captcha = ReCaptchaField(
        widget=ReCaptchaV3(
            attrs={
                'required_score': 0.5,
                'action': 'signup'
            }
        ),
        label=''
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'captcha']

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Passwords do not match.")
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'enduser'
        if commit:
            user.save()
        return user
    
class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label='Enter your email', max_length=255)
    captcha = ReCaptchaField(
        widget=ReCaptchaV3(
            attrs={
                'required_score': 0.5,
                'action': 'forgot_password'
            }
        ),
        label=''
    )