"""
Django settings for centuryAuto project.

Generated by 'django-admin startproject' using Django 4.2.9.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
from pathlib import Path
import boto3
from storages.backends.s3boto3 import S3Boto3Storage
from app.core.storage_backends import MediaStorage



SITE_ID = 1

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-&29r(3ieuqhf0fba_#5pdwr&e!2ntx%8k)ny=^)0h1^9c#ih8x')

if os.getenv('DJANGO_DEBUG', 'True') == 'True':
    DEBUG = True
else:
    DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'app.inventory.apps.InventoryConfig',
    'app.core.apps.CoreConfig',
    'app.authentication.apps.AuthenticationConfig',
    'app.point_of_sale.apps.PointOfSaleConfig',
    'app.employee.apps.EmployeeConfig',
    'app.purchase.apps.PurchaseConfig',
    'app.dashboard.apps.DashboardConfig',
    'app.customers.apps.CustomersConfig',
]
INSTALLED_APPS += [
    'crispy_forms',
    'crispy_bootstrap5',
    # 'storages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = os.getenv('DJANGO_STATIC_URL', '/static/')

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # Your source static files (dev)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')    # Collected static files (production)

# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
# AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCE SS_KEY")
# AWS_STORAGE_BUCKET_NAME = "century-auto"
# AWS_S3_REGION_NAME = "us-east-1"
# AWS_S3_ENDPOINT_URL = 'https://nyc3.digitaloceanspaces.com'
#
# AWS_S3_OBJECT_PARAMETERS = {
#     'CacheControl': 'max-age=86400',
# }
#
# AWS_LOCATION = 'https://century-auto.nyc3.digitaloceanspaces.com'
#
# AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.nyc3.digitaloceanspaces.com'
# AWS_DEFAULT_ACL = 'public-read'
# MEDIA_LOCATION = 'media'
# MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIA_LOCATION}/'

# DEFAULT_FILE_STORAGE = 'app.core.storage_backends.MediaStorage'

#
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = os.getenv('EMAIL_HOST')
# EMAIL_PORT = 587
# EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
# EMAIL_USE_TLS = True
#
# RECAPTCHA_SITE_KEY = os.getenv('RECAPTCHA_SITE_KEY')
# RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY')
#
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
