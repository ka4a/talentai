import json
from django.conf import settings
from os import path

# Countries
with open(path.join(settings.BASE_DIR, 'core/datasets/countries.json')) as f:
    countries = json.load(f)
