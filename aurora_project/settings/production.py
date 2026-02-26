from .base import *
from decouple import config

DEBUG = False

SECRET_KEY = config('SECRET_KEY')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.postgresql',
        'NAME'    : config('DB_NAME'),
        'USER'    : config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST'    : config('DB_HOST'),
        'PORT'    : config('DB_PORT'),
    }
}

STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT  = BASE_DIR / 'media'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + MIDDLEWARE[1:]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'