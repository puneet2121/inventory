import os

from system.base_settings import *

ROOT_URLCONF = 'system.development.urls'

WSGI_APPLICATION = 'system.development.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
#
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'postgres',
#         'USER': 'postgres.patucqkblstgphmpndrz',
#         'PASSWORD': '$Shivji21219319',
#         'HOST': 'aws-0-ap-southeast-1.pooler.supabase.com',
#         'PORT': '6543',
#     }
# }


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydatabase',
        'USER': 'puneet',
        'PASSWORD': 'puneet',
        'HOST': '159.89.162.82',
        'PORT': '5432',
    }
}