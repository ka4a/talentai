"""
Django settings for talentai project.

Generated by 'django-admin startproject' using Django 2.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

from os import getenv, path

from django.utils.translation import gettext_lazy as _


# Build paths inside the project like this: path.join(BASE_DIR, ...)
BASE_DIR = path.dirname(path.dirname(__file__))

RELEASE = ''
ENVIRONMENT = ''

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

SECRET_KEY = 'e^w&mj&xcrk=h_nc$lrs-vw2soq!og#51o&ec+77v+a71%39%5'

DEBUG = False

DISABLE_SIGNUP = False

BASE_URL = ''
ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'reversion',
    'rest_framework',
    'drf_yasg',
    'storages',
    'phonenumber_field',
    'django_admin_listfilter_dropdown',
    'core',
    'django_cleanup',
    'djmoney',
    'djmoney.contrib.exchange',
    'drf_multiple_model',
    'ordered_model',
    'import_export',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'core.middlewares.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'core.middlewares.authentication_middleware',
]

ROOT_URLCONF = 'talentai.urls'

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

WSGI_APPLICATION = 'talentai.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
    {'NAME': 'core.validators.SpecialCharacterValidator',},
]

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en'

DEFAULT_USER_LANGUAGE = 'en'
LANGUAGES = [
    ('en', _('English')),
    ('ja', _('Japanese')),
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
    path.join(BASE_DIR, 'locale/'),
]

# Financial
CURRENCY_CHOICES = [
    ('JPY', '¥'),
    ('USD', '$'),
    ('EUR', '€'),
    ('CNY', '¥'),
    ('GBP', '£'),
    ('KRW', '₩'),
    ('INR', '₹'),
    ('CAD', 'C$'),
    ('HKD', 'HK$'),
    ('BRL', 'R$'),
]
DEFAULT_CURRENCY = 'JPY'
EXCHANGE_BACKEND = 'core.exchange_rates.ExchangeRateAPIBackend'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = path.join(BASE_DIR, 'media')

SWAGGER_SETTINGS = {'DEFAULT_INFO': 'talentai.urls.openapi_info'}

AUTH_USER_MODEL = 'core.User'


# Django Filters
# https://django-filter.readthedocs.io/en/master/

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'talentai.ordering_filters.CamelCaseOrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'JSON_UNDERSCOREIZE': {'no_underscore_before_number': True,},
    'DEFAULT_RENDERER_CLASSES': (
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',
    ),
    'PAGE_SIZE': 100,
}


DEFAULT_FROM_EMAIL = ''

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# For talentai.email_backends.WhiteListSMTPBackend
EMAIL_WHITELIST_DOMAINS = []

CELERY_BROKER_URL = 'amqp://guest:PASSWORD@127.0.0.1:5672/'

REMOVE_UNACTIVATED_ACCOUNTS_AFTER_HOURS = 7 * 24

# Parse text string (e.g. "[1, 5, 7]") and convert to array
CANDIDATE_RAW_DATA_AGENCY_IDS = (
    getenv('CANDIDATE_RAW_DATA_AGENCY_IDS', "").strip('][').split(', ')
)
CANDIDATE_RAW_DATA_CLIENT_IDS = (
    getenv('CANDIDATE_RAW_DATA_CLIENT_IDS', "").strip('][').split(', ')
)

SESSION_COOKIE_AGE = 60 * 60
SESSION_NON_ADMIN_COOKIE_AGE = 60 * 60 * 24
SESSION_SAVE_EXCLUDE_PATHS = ['/api/user/notifications_count/', '/api/notifications/']

# needed for extension to perform cross origin requests
SESSION_COOKIE_SAMESITE = None
CSRF_COOKIE_SAMESITE = None

EXT_ORIGIN = getenv('EXT_ORIGIN', '')

CLOUDCONVERT_API_KEY = getenv('CLOUDCONVERT_API_KEY', None)

PENDING_CONTRACT_EXPIRATION_TIME = 14  # days

ZENDESK_SSO_JWT_ENCODING = 'HS256'