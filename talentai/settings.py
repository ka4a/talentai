from os import getenv, path

import sentry_sdk

from celery.schedules import crontab
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

# noinspection PyUnresolvedReferences
from .settings_base import *

# set dynamically upon deployment instead of `.env`
RELEASE = getenv('RELEASE')
ENVIRONMENT = getenv('ENVIRONMENT')

DEBUG = True

LANGUAGE_COOKIE_NAME = 'lang'

PREFIX = 'LOCAL_'
if ENVIRONMENT == 'dev':
    PREFIX = 'DEV_'
    DEBUG = False
elif ENVIRONMENT == 'test':
    PREFIX = 'test_'
elif ENVIRONMENT == 'production':
    PREFIX = 'PROD_'
    DEBUG = False
elif ENVIRONMENT == 'staging':
    PREFIX = 'STG_'
    DEBUG = False

DISABLE_SIGNUP = getenv(PREFIX + 'DISABLE_SIGNUP') == "true"

if ENVIRONMENT in ['dev', 'staging', 'production']:
    sentry_sdk.init(
        dsn=getenv('REACT_APP_SENTRY_PUBLIC_DSN'),
        integrations=[DjangoIntegration(), CeleryIntegration()],
        release=f'zookeep@{RELEASE}',
        environment=ENVIRONMENT,
        send_default_pii=True,  # track users
    )

BASE_URL = getenv(PREFIX + 'BASE_URL')

# $ python3 -c "import secrets; print(secrets.token_urlsafe())"
SECRET_KEY = getenv(PREFIX + 'SECRET_KEY')
ALLOWED_HOSTS = getenv(PREFIX + 'ALLOWED_HOSTS', '').split(',')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if ENVIRONMENT in ['dev', 'staging', 'production']:
    CSRF_COOKIE_SECURE = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': getenv(PREFIX + 'DB_NAME'),
        'USER': getenv(PREFIX + 'DB_USER'),
        'PASSWORD': getenv(PREFIX + 'DB_PASSWORD'),
        'HOST': getenv(PREFIX + 'DB_HOST'),
        'PORT': getenv(PREFIX + 'DB_PORT'),
    }
}

STATICFILES_DIRS = [path.join(BASE_DIR, './dashboard/build/static/')]
STATIC_ROOT = path.join(BASE_DIR, 'django_static')

# Never use default `guest` password
CELERY_BROKER_URL = getenv(PREFIX + 'CELERY_BROKER_URL')

if getenv(PREFIX + 'EMAIL_BACKEND', ''):
    EMAIL_BACKEND = getenv(PREFIX + 'EMAIL_BACKEND')
    EMAIL_HOST = getenv(PREFIX + 'EMAIL_HOST')
    EMAIL_HOST_USER = 'apikey'  # don't change
    EMAIL_HOST_PASSWORD = getenv(PREFIX + 'EMAIL_HOST_PASSWORD')
    EMAIL_PORT = getenv(PREFIX + 'EMAIL_PORT')
    EMAIL_USE_TLS = getenv(PREFIX + 'EMAIL_USE_TLS')
    EMAIL_WHITELIST_DOMAINS = getenv(PREFIX + 'EMAIL_WHITELIST_DOMAINS').split(',')

DEFAULT_FROM_EMAIL = 'ZooKeep <no-reply@zookeep.com>'

CELERY_BEAT_SCHEDULE = {
    'remove_unactivated_accounts': {
        'task': 'core.tasks.remove_unactivated_accounts',
        'schedule': crontab(hour='*/1'),
    },
    'mark_expired_contracts': {
        'task': 'core.tasks.mark_expired_contracts',
        'schedule': crontab(minute=0, hour=0),
    },
    # TODO(ZOO-1157): wait for updated API key
    # 'update_currency_rates': {
    #     'task': 'core.tasks.update_currency_rates',
    #     'schedule': crontab(minute=0, hour=0),
    # },
}

DEFAULT_FILE_STORAGE = getenv(
    PREFIX + 'DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage'
)

AWS_STORAGE_BUCKET_NAME = getenv(PREFIX + 'AWS_STORAGE_BUCKET_NAME', None)
AWS_S3_REGION_NAME = getenv(PREFIX + 'AWS_S3_REGION_NAME', None)
AWS_ACCESS_KEY_ID = getenv(PREFIX + 'AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY = getenv(PREFIX + 'AWS_SECRET_ACCESS_KEY', None)
AWS_DEFAULT_ACL = 'private'
AWS_AUTO_CREATE_BUCKET = True

# Tell django-storages the domain to use to refer to static files.
# AWS_S3_CUSTOM_DOMAIN = '{}.s3.amazonaws.com'.format(AWS_STORAGE_BUCKET_NAME)

AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400, public, private',
}

ZENDESK_SSO_SECRET = getenv(PREFIX + 'ZENDESK_SSO_SECRET')

# https://docs.hcaptcha.com/#test-key-set-publisher-account
HCAPTCHA_SECRET_KEY = getenv(PREFIX + 'HCAPTCHA_SECRET_KEY')
