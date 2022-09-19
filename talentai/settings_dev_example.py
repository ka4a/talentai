# noinspection PyUnresolvedReferences
from .settings_base import *


DEBUG = True
AUTH_PASSWORD_VALIDATORS = []

BASE_URL = 'http://127.0.0.1:9009'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'talentai_dev',
        'USER': 'user',
        'PASSWORD': 'pass',
        'HOST': '127.0.0.1',
        'PORT': '45432',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CELERY_BROKER_URL = 'amqp://guest:guest@127.0.0.1:45672/'
