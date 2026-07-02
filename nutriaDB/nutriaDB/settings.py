"""
Django settings for nutriaDB project.

Updated for Django 6.0.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/6.0/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('NUTRIA_SECRET_KEY', 'django-insecure-dev-only-_8@=tgd$&8x%818&@_d1s-lo)afmx18nl')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('NUTRIA_DEBUG_MODE', 'True') == 'True'

ALLOWED_HOSTS = [h for h in os.getenv('NUTRIA_ALLOWED_HOSTS', '').split(',') if h]


# Application definition

INSTALLED_APPS = [
    'backend.apps.BackendConfig',
    'jsonAPI.apps.JsonapiConfig',
    'binaryAPI.apps.BinaryapiConfig',
    'openfoodfacts.apps.OpenfoodfactsConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'nutriaDB.middleware.CorsHeaderMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nutriaDB.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'nutriaDB.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
#
# Defaults to SQLite for zero-configuration local development.
# Production (see docker-compose.yml) sets NUTRIA_DB_ENGINE to
# 'django.db.backends.postgresql'.

DATABASES = {
    'default': {
        'ENGINE': os.getenv('NUTRIA_DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('NUTRIA_DB_NAME', str(BASE_DIR / 'db.sqlite3')),
    }
}
for _setting, _env_var in [('USER', 'NUTRIA_DB_USER'), ('PASSWORD', 'NUTRIA_DB_PASSWORD'),
                           ('HOST', 'NUTRIA_DB_HOST'), ('PORT', 'NUTRIA_DB_PORT')]:
    _value = os.getenv(_env_var)
    if _value:
        DATABASES['default'][_setting] = _value


# Default primary key field type
# https://docs.djangoproject.com/en/6.0/ref/settings/#default-auto-field
#
# Kept at AutoField (not BigAutoField) to match the primary keys in the
# existing migrations and avoid a needless schema migration.

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = os.getenv('NUTRIA_LANGUAGE_CODE', 'de-de')

TIME_ZONE = os.getenv('NUTRIA_TIME_ZONE', 'Europe/Berlin')

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

STATIC_ROOT = os.getenv('NUTRIA_STATIC_ROOT', '/var/www/static')


# Secret used to sign the JWT tokens issued by the jsonAPI app.
JWT_SECRET = os.getenv('NUTRIA_JWT_SECRET', 'dev-only-SrFbE63DV7xy0R01')
