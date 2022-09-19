# noinspection PyUnresolvedReferences
from .settings_base import *
from os import path

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ci_test',
        'USER': 'root',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

CELERY_TASK_ALWAYS_EAGER = True

STATICFILES_DIRS = [path.join(BASE_DIR, './dashboard/build/static/')]
STATIC_ROOT = path.join(BASE_DIR, 'django_static')
ZENDESK_SSO_SECRET = 'fake key'
HCAPTCHA_SECRET_KEY = '0x0000000000000000000000000000000000000000'
