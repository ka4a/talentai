from distutils.util import strtobool
from datetime import datetime

import bleach
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction

from core.models import (
    Agency,
    SkillDomain,
    Function,
    Job,
    Client,
    JobWorkExperience,
    Language,
    JobStatus,
)
from core.zoho import ZohoRecruitClient, zoho_data_to_dict, ZohoData
from core.utils import map_data, get_country_code_by_name

JOB_FIELDS_MAPPING = {
    'zoho_id': 'JOBOPENINGID',
    'title': 'Posting Title',
    'tier_one_companies': 'Target Companies - Tier 1 (Most relevant)',
    'tier_two_companies': 'Target Companies - Tier 2 (Less relevant)',
    'openings_count': 'Number of Positions',
    'target_date': 'Target Date',
    'created_at': 'Date Opened',
    'work_location': 'City',
}


JOB_WORK_EXPERIENCE_MAP = {
    '-None-': JobWorkExperience.NONE.key,
    'Fresher': JobWorkExperience.FRESHER.key,
    '0-1 year': JobWorkExperience.ZERO_ONE_YEAR.key,
    '1-3 years': JobWorkExperience.ONE_THREE_YEARS.key,
    '4-5 years': JobWorkExperience.FOUR_FIVE_YEARS.key,
    '5+ years': JobWorkExperience.FIVE_MORE_YEARS.key,
}


JOB_STATUS_MAPPING = {
    'On - Hold': JobStatus.ON_HOLD.key,
    'Pitching - not yet secured': JobStatus.OPEN.key,
    'Cancelled': JobStatus.CLOSED.key,
    'In-progress': JobStatus.OPEN.key,
    'Filled': JobStatus.FILLED.key,
    'Inactive': JobStatus.ON_HOLD.key,
}


def get_agency_user_by_zoho_id(agency, zoho_id):
    return agency.members.filter(zoho_id=zoho_id).first()


def to_flat_zoho_jobs_data(zoho_jobs_data):
    return [job_data['FL'] for job_data in zoho_jobs_data]


def get_job_zoho_id_from_zoho_data(zoho_job_data):
    for field in zoho_job_data:
        if field['val'] == 'JOBOPENINGID':
            return field['content']


def get_file_zoho_id_from_file_record(file_record):
    for i in file_record:
        if i['val'] == 'id':
            return i['content']


def parse_salary_data(salary_data):
    if salary_data.isnumeric():
        return {
            'salary_from': salary_data,
            'salary_to': salary_data,
        }
    salary_data = salary_data.replace('JPY', '').strip()
    try:
        multiplier = 1
        if 'm' in salary_data or 'M' in salary_data:
            multiplier = 1_000_000

        salary = (
            salary_data.replace(' ', '').replace('m', '').replace('M', '').split('-')
        )
        if len(salary) == 1:
            return {
                'salary_from': int(salary[0]) * multiplier,
                'salary_to': int(salary[0]) * multiplier,
            }
        else:
            return {
                'salary_from': int(salary[0]) * multiplier,
                'salary_to': int(salary[1]) * multiplier,
            }
    except ValueError:
        return {'salary_from': None, 'salary_to': None}


def to_job_data(zoho_data, agency, default_user):
    job_data = {
        'zoho_data': zoho_data,
    }

    fields_data = zoho_data_to_dict(zoho_data)
    job_data.update(map_data(fields_data, JOB_FIELDS_MAPPING))

    job_data['org_id'] = agency.pk
    job_data['org_content_type'] = ContentType.objects.get_for_model(agency)

    job_data['status'] = JOB_STATUS_MAPPING[fields_data['Job Opening Status']]

    if 'Job Description' in fields_data:
        responsibilities = fields_data['Job Description']
        only_text = bleach.clean(responsibilities, tags=[], strip=True).strip()

        if not only_text:  # to remove empty <p></p>
            job_data['responsibilities'] = ''

        job_data['responsibilities'] = bleach.clean(
            responsibilities,
            tags=[
                'p',
                'ul',
                'li',
                'ol',
                'strong',
                'em',
                'u',
                'span',
                'div',
                'br',
                'font',
                'table',
                'td',
                'tr',
                'tbody',
                'b',
            ],
            attributes={},
        )

    if 'Industry' in fields_data:
        job_data['function'], created = Function.objects.get_or_create(
            title=fields_data['Industry']
        )

    if 'Country' in fields_data:
        job_data['country'] = (
            get_country_code_by_name(fields_data['Country'], 'en') or 'jp'
        )

    if 'Salary' in fields_data:
        job_data.update(parse_salary_data(fields_data['Salary']))

    if 'Work Experience' in fields_data:
        job_data['work_experience'] = JOB_WORK_EXPERIENCE_MAP[
            fields_data['Work Experience']
        ]

    if 'CLIENTID' in fields_data:
        client = Client.objects.filter(
            owner_agency=agency, zoho_id=fields_data['CLIENTID']
        ).first()

        if not client:
            print(f'Client with zoho id {fields_data["CLIENTID"]} does not exist')

        job_data['client'] = client

    if 'SMOWNERID' in fields_data:
        owner = get_agency_user_by_zoho_id(agency, fields_data['SMOWNERID'])
        job_data['owner'] = owner or default_user

    if 'CONTACTID' in fields_data:
        contact = get_agency_user_by_zoho_id(agency, fields_data['CONTACTID'])
        job_data['recruiter'] = contact

    recruiter = None
    if 'RECRUITERID' in fields_data:
        recruiter = get_agency_user_by_zoho_id(agency, fields_data['RECRUITERID'])

    try:
        Job(**job_data).clean_fields()
    except ValidationError as e:
        invalid_fields = e.message_dict.keys()

        for i in invalid_fields:
            job_data.pop(i, None)

    return job_data, recruiter


def get_zoho_jobs_data(auth_token, agency, default_user):
    zoho_client = ZohoRecruitClient(auth_token, 'JobOpenings')

    for zoho_job_data in zoho_client.get_all_records():
        zoho_job_data = zoho_job_data['FL']
        job_zoho_id = get_job_zoho_id_from_zoho_data(zoho_job_data)

        print(f'Processing job with id {job_zoho_id}...')

        job, recruiter = to_job_data(zoho_job_data, agency, default_user)

        yield {
            'job': job,
            'recruiter': recruiter,
        }


def migrate_jobs(auth_token, agency, default_user, existing_clients):
    non_created_jobs = []
    skipped_jobs = []
    count = 0
    with transaction.atomic():
        print('Fetching jobs from Zoho...')
        for job_data in get_zoho_jobs_data(auth_token, agency, default_user):
            if not job_data['job'].get('client', None):
                non_created_jobs.append(job_data['job'])
                continue

            if str(job_data['job']['client'].pk) in existing_clients:
                skipped_jobs.append(
                    f'{job_data["job"]["zoho_id"]}\t{job_data["job"]["title"]}'
                )
                continue

            job = Job.objects.create(**job_data['job'])
            count += 1
            recruiter = job_data['recruiter']

            if recruiter:
                job.assign_member(recruiter)

            # add languages
            zoho_data = ZohoData(job_data['job']['zoho_data'])
            for lang, level in zoho_data.language_iter():
                job.required_languages.add(
                    Language.objects.get(language=lang, level=level)
                )

    if non_created_jobs:
        print('Could not found clients for following jobs:')
        for job in non_created_jobs:
            print(job.get('zoho_id'), '\t', job.get('title'))

    if skipped_jobs:
        print(f'{len(skipped_jobs)} was skipped')
        for job in skipped_jobs:
            print(job)

    return count


class Command(BaseCommand):
    help = 'Creates new jobs, link them with zoho ids.'

    def add_arguments(self, parser):
        """Add management command argumants."""
        parser.add_argument('zoho_auth_token', nargs='?', type=str)
        parser.add_argument('agency_id', nargs=1, type=int)
        parser.add_argument('default_user_id', nargs='?', type=int)
        parser.add_argument('existing_clients', nargs=1, type=str)

    def handle(self, *args, **options):
        """Execute the command function."""
        agency = Agency.objects.get(pk=options['agency_id'][0])
        zoho_auth_token = options['zoho_auth_token']
        default_user = agency.members.filter(pk=options['default_user_id']).first()
        existing_clients = options['existing_clients'][0].split(',')

        while True:
            try:
                clients = Client.objects.filter(
                    pk__in=list(filter(lambda pk: int(pk), existing_clients))
                )
                print('Jobs which belong to following clients will be skipped:')
                for client in clients:
                    print(client.name)
                print()
                print(f'Default job owner is {default_user.full_name}')
                print()
                message = (
                    'Import Jobs to "{}" Agency? '
                    'Make sure you Clients and Users '
                    'are already imported. [y/n] '.format(agency.name)
                )
                if not strtobool(input(message)):
                    print('Import canceled')
                    return

                break
            except ValueError:
                print('Answer must be either y or n')

        start_time = datetime.now()

        jobs_count = migrate_jobs(
            zoho_auth_token, agency, default_user, existing_clients
        )

        end_time = datetime.now()
        td = end_time - start_time
        print(f'Successfully imported {jobs_count} jobs for {td.seconds} seconds.')
