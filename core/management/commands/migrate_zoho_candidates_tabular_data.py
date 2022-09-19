import csv
from distutils.util import strtobool
from datetime import datetime

from django.core.management.base import BaseCommand

from core.models import Agency, ExperienceDetail, EducationDetail


EDUCATION_FIELDS_MAPPING = {
    'Institute / School': 'institute',
    'Major / Department': 'department',
    'Degree': 'degree',
    'Duration_From': 'date_start',
    'Duration_To': 'date_end',
    'Currently pursuing': 'currently_pursuing',
}

EXPERIENCE_FIELDS_MAPPING = {
    'Occupation / Title': 'occupation',
    'Company': 'company',
    'Summary': 'summary',
    'Work Duration_From': 'date_start',
    'Work Duration_To': 'date_end',
    'I currently work here': 'currently_pursuing',
}

TABULAR_TYPE_MAPPING = {
    'education': {'model': EducationDetail, 'mapping': EDUCATION_FIELDS_MAPPING,},
    'experience': {'model': ExperienceDetail, 'mapping': EXPERIENCE_FIELDS_MAPPING,},
}


def get_candidate_zoho_id(zoho_data):
    return zoho_data['Candidate Id'].split('_')[1]


def get_tabular_data_from_zoho_data(tabular_data, tabular_type):
    data = {}
    tabular = TABULAR_TYPE_MAPPING[tabular_type]
    for key, new_key in tabular['mapping'].items():
        data[new_key] = tabular_data[key]

    data['currently_pursuing'] = bool(data['currently_pursuing'])
    for field in ('date_start', 'date_end'):
        try:
            data[field] = datetime.strptime(data[field], '%b-%Y')
            continue
        except:
            data[field] = None
        data[field] = None

    return data


def migrate_candidates_tabular_data(input_file_path, agency, tabular_type):
    file = open(input_file_path, 'r')
    reader = csv.DictReader(file)

    created = 0
    non_created = 0
    not_found = 0

    for zoho_data in reader:
        candidate_zoho_id = get_candidate_zoho_id(zoho_data)
        tabular_data = get_tabular_data_from_zoho_data(zoho_data, tabular_type)

        Model = TABULAR_TYPE_MAPPING[tabular_type]['model']
        candidate = agency.candidates.filter(zoho_id=candidate_zoho_id).first()

        if not candidate:
            not_found += 1
            continue
        try:
            Model.objects.create(candidate=candidate, **tabular_data)
            created += 1
        except:
            non_created += 1

    file.close()

    return created, non_created, not_found


class Command(BaseCommand):
    help = 'Imports tabular candidate data from exported .csv file.'

    def add_arguments(self, parser):
        parser.add_argument('input_file_path', nargs='?', type=str)
        parser.add_argument('agency_id', nargs=1, type=int)
        parser.add_argument(
            'tabular_type', nargs='?', type=str
        )  # education or experience

    def handle(self, *args, **options):
        input_file_path = options['input_file_path']
        agency = Agency.objects.get(pk=options['agency_id'][0])
        tabular_type = options['tabular_type']

        while True:
            try:
                message = 'Import tabular data to "{}" Agency candidates? [y/n] '.format(
                    agency.name
                )
                if not strtobool(input(message)):
                    print('Import canceled')
                    return

                break
            except ValueError:
                print('Answer must be either y or n')

        created, non_created, not_found = migrate_candidates_tabular_data(
            input_file_path, agency, tabular_type
        )

        print(f'Created {created} {tabular_type}s')
        if non_created:
            print(f'Can not create {non_created} {tabular_type}s')

        if not_found:
            print(f'Can not find {not_found} candidates')
