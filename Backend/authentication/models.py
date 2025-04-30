# authentication/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    """
    Custom manager for handling user creation.
    Ensures that email is required and that superusers have
    the necessary privileges and admin role by default.
    """

    def create_user(self, username, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given username, email, and password.
        """
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given username, email, and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')  # Ensure superusers are always 'admin'
        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Includes a 'role' field to distinguish user roles.
    """
    ROLE_CHOICES = [
        ('enduser', 'End User'),
        ('engineer', 'AI Engineer'),
        ('admin', 'Administrator'),
        ('finance', 'Finance Team'),
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='enduser'
    )

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        # Removed the hard-coded table name so Django uses its default
        # table name: authentication_customuser
        pass
