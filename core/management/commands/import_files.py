import os
import csv
from distutils.util import strtobool

from django.core.management.base import BaseCommand
from django.core.files import File
from django.db import transaction

from core.models import Agency, Job, JobFile, Candidate, CandidateFile
from core.utils import org_filter


def create_candidate_file(agency, candidate, file):
    CandidateFile.objects.create(
        candidate=candidate, file=file, organization=agency,
    )


def create_job_file(agency, job, file):
    JobFile.objects.create(job=job, file=file)


CREATE_FUNCTIONS_MAP = {
    'candidate': create_candidate_file,
    'job': create_job_file,
}

MODEL_MAP = {
    'candidate': Candidate,
    'job': Job,
}


def import_files(agency, directory, attachments, entity):
    create_file_function = CREATE_FUNCTIONS_MAP[entity]
    Model = MODEL_MAP[entity]

    queryset = Model.objects.filter(org_filter(agency))
    file_map = {}

    created = 0
    not_found = 0

    with open(attachments) as attachments_file:
        for line in csv.DictReader(attachments_file):
            file_name = line['File Name']
            instance_zoho_id = line['Parent ID'].split('_')[1]

            file_map[file_name] = instance_zoho_id

    with transaction.atomic():
        for name in os.listdir(directory):
            full_file_path = os.path.join(directory, name)

            with open(full_file_path, 'rb') as content:
                file = File(content, name)

                instance_zoho_id = file_map.get(name)
                if not instance_zoho_id:
                    not_found += 1
                    continue

                instance = queryset.filter(zoho_id=instance_zoho_id).first()
                if not instance:
                    not_found += 1
                    continue

                create_file_function(agency, instance, file)
                created += 1

    return created, not_found


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('agency_id', nargs=1, type=int)
        parser.add_argument('directory', nargs='?', type=str)
        parser.add_argument('attachments', nargs='?', type=str)
        parser.add_argument('entity', nargs='?', type=str)

    def handle(self, *args, **options):
        directory = options['directory']
        agency = Agency.objects.get(pk=options['agency_id'][0])
        attachments = options['attachments']
        entity = options['entity']  # 'candidate' or 'job'

        while True:
            try:
                message = 'Import {} files that belong to {} agency? [y/n]: '.format(
                    entity, agency.name
                )
                if not strtobool(input(message)):
                    print('Import canceled')
                    return

                break
            except ValueError:
                print('Answer must be either y or n')

        created, not_found = import_files(agency, directory, attachments, entity)

        print(f'Successfully imported {created} {entity} files.')
        if not_found:
            print(f'Can not find {not_found} {entity}s.')
