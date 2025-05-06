#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os  # Import os for environment variable handling
import sys  # Import sys for command line arguments

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'insurance_ai.settings')  # Set the default settings module
    try:
        from django.core.management import execute_from_command_line  # Import management command execution
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc  # Raise error if Django is not installed
    execute_from_command_line(sys.argv)  # Execute command line arguments

if __name__ == '__main__':
    main()  # Run the main function