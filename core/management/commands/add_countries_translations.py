import json

from django.conf import settings
from django.core.management import BaseCommand

from os import path

COUNTRIES_OUTPUT_PATH = path.join(settings.BASE_DIR, 'core/datasets/countries.json')


class Command(BaseCommand):
    """
    We use country dataset from http://stefangabos.github.io/world_countries/
    Use this command to convert data.
    Source file format: [{"id": 392, "name": "Japan", "alpha2": "jp", "alpha3": "jpn"}, ...]
    Output file format: [{"code": "jp", "name_en": "Japan", "name_ja": "日本"}, ...]
    """

    help = 'Convert source country list to translatable format.'

    def add_arguments(self, parser):
        parser.add_argument('input_file_path', nargs=1, type=str)
        parser.add_argument('language', nargs=1, type=str)

    def handle(self, *args, **options):
        input_file_path = options['input_file_path'][0]
        language_key = 'name_' + options['language'][0]

        with open(input_file_path) as source_file:
            non_formatted_countries = json.load(source_file)

        with open(COUNTRIES_OUTPUT_PATH) as existing_file:
            countries = json.load(existing_file)

        country_code_names = dict()
        result = []

        for c in non_formatted_countries:
            country_code_names[c['alpha2']] = c['name']

        for country in countries:
            code = country['code']
            result.append({**country, language_key: country_code_names[code]})

        with open(COUNTRIES_OUTPUT_PATH, 'w') as output_file:
            json.dump(result, output_file, ensure_ascii=False, indent='\t')
