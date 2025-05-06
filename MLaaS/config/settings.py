# config/settings.py

from pathlib import Path  # Import Path for handling file paths
import os  # Import os for environment variable handling
from dotenv import load_dotenv  # Import load_dotenv for loading environment variables from a .env file

load_dotenv()  # Load environment variables from a .env file

BASE_DIR = Path(__file__).resolve().parent.parent  # Define the base directory for the project

# Security settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-your-secret-key-here')  # Get secret key from environment
DEBUG = os.environ.get('DEBUG', 'True') == 'True'  # Set debug mode based on environment variable
ALLOWED_HOSTS = ['*', 'mlaas-service', '172.18.0.3']  # Allow all hosts for development

# Installed applications
INSTALLED_APPS = [
    'django.contrib.admin',  # Django admin application
    'django.contrib.auth',  # Django authentication application
    'django.contrib.contenttypes',  # Content types framework
    'django.contrib.sessions',  # Session framework
    'django.contrib.messages',  # Messaging framework
    'django.contrib.staticfiles',  # Static files framework
    'rest_framework',  # Django REST framework
    'corsheaders',  # CORS headers for cross-origin requests
    'ml_api',  # Custom ML API application
]

# Middleware settings
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',  # Security middleware
    'django.contrib.sessions.middleware.SessionMiddleware',  # Session middleware
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware
    'django.middleware.common.CommonMiddleware',  # Common middleware
    'django.middleware.csrf.CsrfViewMiddleware',  # CSRF protection middleware
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Authentication middleware
    'django.contrib.messages.middleware.MessageMiddleware',  # Messaging middleware
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Clickjacking protection middleware
]

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True  # Allow all origins for CORS
CORS_ALLOW_CREDENTIALS = True  # Allow credentials for CORS

ROOT_URLCONF = 'config.urls'  # Root URL configuration

# Template settings
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  # Template backend
        'DIRS': [],  # Directories for templates
        'APP_DIRS': True,  # Enable app directories for templates
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',  # Debug context processor
                'django.template.context_processors.request',  # Request context processor
                'django.contrib.auth.context_processors.auth',  # Authentication context processor
                'django.contrib.messages.context_processors.messages',  # Messages context processor
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'  # WSGI application configuration

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # Database engine
        'NAME': os.environ.get('DATABASE_NAME', 'insurance_ai'),  # Database name
        'USER': os.environ.get('DATABASE_USER', 'user'),  # Database user
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'password'),  # Database password
        'HOST': os.environ.get('DATABASE_HOST', 'postgres_db'),  # Database host
        'PORT': os.environ.get('DATABASE_PORT', '5432'),  # Database port
    }
}

# Check for SQLite configuration
if os.environ.get('USE_SQLITE', 'False') == 'True':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',  # Use SQLite database
            'NAME': BASE_DIR / 'db.sqlite3',  # Database file path
        }
    }

# Password validation settings
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',  # Similarity validator
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',  # Minimum length validator
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',  # Common password validator
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',  # Numeric password validator
    },
]

# Internationalization settings
LANGUAGE_CODE = 'en-us'  # Language code for the project
TIME_ZONE = 'UTC'  # Time zone for the project
USE_I18N = True  # Enable internationalization
USE_TZ = True  # Enable timezone support

# Static files settings
STATIC_URL = 'static/'  # URL for serving static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Directory for collected static files

MEDIA_URL = '/media/'  # URL for serving media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # Directory for uploaded media files

MODEL_ROOT = os.path.join(BASE_DIR, 'ml_models')  # Directory for ML models

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'  # Default primary key field type

# REST framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        # Re-enable this if you want the global default to be IsAuthenticated:
        # 'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.AllowAny',  # Allow any user for now
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',  # Session authentication
        'rest_framework.authentication.BasicAuthentication',  # Basic authentication
    ],
}

# -------------------------------------------------------------------------
# MLaaS settings for calling MLaaS from this main app
# -------------------------------------------------------------------------
MLAAS_SERVICE_URL = os.environ.get('MLAAS_SERVICE_URL', 'http://mlaas-service:8009/api/')  # MLaaS service URL