# noinspection PyUnresolvedReferences
from .settings import *


DEBUG = False

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

CELERY_TASK_ALWAYS_EAGER = True
