from .base import *
import os
from decouple import config

DEBUG = False

ADMINS = [
    ('arsham', 'arsham202@gmail.com')
]

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE':  'django.db.backends.postgresql',
        'NAME':  config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': 'db',
        'PORT': 5432,
    }
}

# security
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True