# authentication/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager  # Import user models
from django.db import models  # Import models from Django ORM

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
        if not email:  # Check if email is provided
            raise ValueError("The Email field must be set")  # Raise error if email is missing
        email = self.normalize_email(email)  # Normalize email address
        user = self.model(username=username, email=email, **extra_fields)  # Create user instance
        user.set_password(password)  # Set user password
        user.save(using=self._db)  # Save user to the database
        return user  # Return the created user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given username, email, and password.
        """
        extra_fields.setdefault('is_staff', True)  # Ensure superuser is staff
        extra_fields.setdefault('is_superuser', True)  # Ensure superuser has superuser privileges
        extra_fields.setdefault('role', 'admin')  # Ensure superusers are always 'admin'
        return self.create_user(username, email, password, **extra_fields)  # Create superuser

class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Includes a 'role' field to distinguish user roles.
    """
    ROLE_CHOICES = [
        ('enduser', 'End User'),  # Choice for end user role
        ('engineer', 'AI Engineer'),  # Choice for engineer role
        ('admin', 'Administrator'),  # Choice for admin role
        ('finance', 'Finance Team'),  # Choice for finance team role
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='enduser'  # Default role is end user
    )

    objects = CustomUserManager()  # Use custom user manager

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"  # String representation of the user

    class Meta:
        # Removed the hard-coded table name so Django uses its default
        # table name: authentication_customuser
        pass  # Placeholder for future model options