import csv
from distutils.util import strtobool
from datetime import datetime

from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError

from core.models import (
    Agency,
    Candidate,
    Industry,
    SkillDomain,
    Language,
    Tag,
    CandidateTag,
)
from core.zoho import (
    zoho_data_to_dict,
    ZohoData,
)
from core.utils import (
    map_data,
    get_country_code_by_name,
    calculate_age,
)


def filter_out_empty_fields(candidate_data):
    result = dict()
    for key, value in candidate_data.items():
        if not value:
            continue
        result[key] = value

    return result


def csv_to_zoho_data(csv_data):
    return [{"val": key, "content": value} for key, value in csv_data.items()]


def get_candidate_zoho_id_from_csv_data(zoho_csv_candidate_data):
    return zoho_csv_candidate_data['Candidate Id'].split('_')[1]


def get_agency_user(agency, **kwargs):
    return agency.members.filter(**kwargs).first()


def parse_datetime(date_and_time):
    return datetime.strptime(date_and_time, '%d/%m/%Y %H:%M')


CANDIDATE_FIELDS_MAPPING = {
    'zoho_id': 'Candidate Id',
    'first_name': 'First Name',
    'first_name_kanji': '名',
    'last_name': 'Last Name',
    'last_name_kanji': '姓',
    'email': 'Email',
    'phone': ('Phone', 'Mobile'),
    'website_url': 'Website',
    'current_company': 'Current Employer',
    'current_position': 'Job Title',
    'potential_locations': 'Potential Locations',
    'twitter_url': 'Twitter',
    'linkedin_url': 'Linkedin',
    'source_details': 'Source',
    'current_salary': 'Current Salary',
    'salary': 'Expected Salary',
    'reason_for_job_changes': 'Salary Breakdown',
    'work_direct': 'Work Direct',
    'is_met': 'Candidate Met',
    'nationality': 'Nationality',
    'department': 'Department',
    'client_brief': 'Client Brief',
    'client_expertise': 'Client Expertise',
    'companies_applied_to': 'Companies Applied To',
    'companies_already_applied_to': 'Companies Already Applied To',
    'pull_factors': 'Pull Factors',
    'push_factors': 'Push Factors',
    'work_mobile': 'Work Mobile',
}


def to_candidate_data(zoho_csv_data, agency, default_user):
    zoho_data = csv_to_zoho_data(zoho_csv_data)
    candidate_data = {
        'zoho_data': zoho_data,
    }

    fields_data = filter_out_empty_fields(zoho_data_to_dict(zoho_data))
    candidate_data.update(map_data(fields_data, CANDIDATE_FIELDS_MAPPING))

    candidate_data['zoho_id'] = candidate_data['zoho_id'].split('_')[1]

    if candidate_data.get('source_details', None):
        candidate_data['source'] = 'Job Boards'

    if 'Country' in fields_data:
        candidate_data['current_country'] = get_country_code_by_name(
            fields_data['Country'], 'en'
        )

    if 'City' in fields_data:
        if fields_data.get('Country') and not candidate_data['current_country']:
            candidate_data[
                'current_city'
            ] = f'{fields_data["City"]} / {fields_data["Country"]}'
        else:
            candidate_data['current_city'] = fields_data["City"]

    if 'Industry' in fields_data:
        candidate_data['industry'] = Industry.get_key_by_value(fields_data['Industry'])

    if 'DOB' in fields_data:
        candidate_data['age'] = calculate_age(
            datetime.strptime(fields_data['DOB'], '%d/%m/%Y')
        )

    if 'Domain Expertise' in fields_data:
        candidate_data['skill_domain'] = SkillDomain.objects.filter(
            name=fields_data['Domain Expertise']
        ).first()

    if 'Referred By' in fields_data:
        candidate_data['referred_by'] = get_agency_user(
            agency, email=fields_data['Referred By']
        )

    if 'Created Time' in fields_data:
        candidate_data['created_at'] = parse_datetime(fields_data['Created Time'])

    if 'Created By' in fields_data:
        names = fields_data['Created By'].split(' ')
        if len(names) == 1:
            names.append('')
        candidate_data['created_by'] = get_agency_user(
            agency, first_name=names[0], last_name=names[1]
        )

    if 'Modified By' in fields_data:
        names = fields_data['Modified By'].split(' ')
        if len(names) == 1:
            names.append('')
        candidate_data['updated_by'] = get_agency_user(
            agency, first_name=names[0], last_name=names[1]
        )

    try:
        if 'Candidate Owner ID' in fields_data:
            names = fields_data['Candidate Owner ID'].split(' ')
            if len(names) == 1:
                names.append('')
            candidate_data['owner'] = (
                get_agency_user(agency, first_name=names[0], last_name=names[1])
                or default_user
            )
        else:
            candidate_data['owner'] = default_user
    except:
        candidate_data['owner'] = default_user

    if agency.enable_researcher_field_feature:
        if 'Name Collect.' in fields_data:
            candidate_data['name_collect'] = get_agency_user(
                agency, email=fields_data['Name Collect.']
            )

        if 'Mobile Collect.' in fields_data:
            candidate_data['mobile_collect'] = get_agency_user(
                agency, email=fields_data['Mobile Collect.']
            )

    try:
        for field in ('current_salary', 'salary'):
            if field in candidate_data:
                candidate_data[field] = int(float(candidate_data[field]))
    except:
        pass

    tags = []

    if 'SW Capabilities' in fields_data:
        data = fields_data['SW Capabilities'].split(';')
        tags.extend(data)

    if 'Engineering Tools / Software' in fields_data:
        data = fields_data['Engineering Tools / Software'].split(';')
        tags.extend(data)

    if 'Functional Expertise' in fields_data:
        data = fields_data['Functional Expertise'].split(';')
        tags.extend(data)

    if 'Technical Expertise' in fields_data:
        data = fields_data['Technical Expertise'].split(';')
        tags.extend(data)

    return candidate_data, tags


def get_zoho_candidate_data(input_file_path, agency, default_user):
    file = open(input_file_path, 'r')
    count = 0
    for zoho_csv_candidate_data in csv.DictReader(file):
        candidate, tags = to_candidate_data(
            zoho_csv_candidate_data, agency, default_user
        )
        count += 1
        yield {'candidate': candidate, 'tags': set(tags)}

    file.close()


def create_candidate(*args, **kwargs):
    candidate = Candidate(*args, **kwargs)
    candidate.clean_fields(check_zoho_and_linkedin=False)
    candidate.save(turn_on_clean_fields=False)
    return candidate


def migrate_candidates(auth_token, agency, default_user):

    print('Exporting candidates from csv...')
    created = 0
    duplicated = 0
    non_created = []

    org_content_type = ContentType.objects.get_for_model(agency)

    for zoho_candidate_data in get_zoho_candidate_data(
        auth_token, agency, default_user
    ):
        candidate_data = zoho_candidate_data['candidate']
        tags_data = zoho_candidate_data['tags']

        if not candidate_data.get('email'):
            candidate_data['email'] = ''

        zoho_data = ZohoData(candidate_data['zoho_data'])
        try:
            candidate = create_candidate(
                organization=agency, employment_status='fulltime', **candidate_data,
            )
        except ValidationError as e:
            fields = list(e.message_dict.keys())

            if 'email' in fields or 'secondary_email' in fields:
                duplicated += 1
                continue

            # remove invalid fields
            for field in fields:
                candidate_data.pop(field, None)

            try:
                candidate = create_candidate(
                    organization=agency, employment_status='fulltime', **candidate_data,
                )
            except IntegrityError:
                duplicated += 1
                continue
            except:
                non_created.append(candidate_data.get('zoho_id'))
                continue
        except IntegrityError:
            duplicated += 1
            continue
        except:
            non_created.append(candidate_data.get('zoho_id'))
            continue

        created += 1

        note = zoho_data['Consultant Notes']
        if note:
            candidate.set_note(agency, note)

        for lang, level in zoho_data.language_iter():
            candidate.languages.add(Language.objects.get(language=lang, level=level))

        # creating tags
        actor = candidate.owner or default_user
        if tags_data:
            for candidate_tag in tags_data:
                tag, _created = Tag.objects.get_or_create(
                    name=candidate_tag.lower(),
                    type='candidate',
                    org_content_type=org_content_type,
                    org_id=agency.id,
                    defaults={
                        'organization': agency,
                        'created_by': candidate.owner or default_user,
                    },
                )
                try:
                    CandidateTag.objects.create(
                        tag=tag, candidate=candidate, attached_by=actor
                    )
                except IntegrityError:
                    # skip already attached tag
                    pass

    if non_created:
        print(f'{len(non_created)} candidates were not created.')
        for candidate in non_created:
            print(candidate)

    return created, duplicated


class Command(BaseCommand):
    help = 'Imports zoho candidates.'

    def add_arguments(self, parser):
        """Add management command arguments."""
        parser.add_argument('input_file_path', nargs='?', type=str)
        parser.add_argument('agency_id', nargs='?', type=int)
        parser.add_argument('default_user_id', nargs='?', type=int)

    def handle(self, *args, **options):
        """Execute a command function."""
        input_file_path = options['input_file_path']
        agency = Agency.objects.filter(pk=options['agency_id']).first()
        default_user = agency.members.filter(pk=options['default_user_id']).first()

        while True:
            try:
                message = (
                    'Import Candidates to "{}" Agency? '
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

        created, existing = migrate_candidates(input_file_path, agency, default_user)

        end_time = datetime.now()
        td = end_time - start_time
        print(f'Successfully imported {created} candidates for {td.seconds} seconds.')
        print(f'{existing} candidates are duplicated')
