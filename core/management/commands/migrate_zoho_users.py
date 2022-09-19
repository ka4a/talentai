import json
from distutils.util import strtobool

from django.core.management.base import BaseCommand

from core.models import Agency, User

# input file should be .json file in next format:
# {
#     "existing": [
#         {
#             "email": "",
#             "first_name": "",
#             "last_name": "",
#             "zoho_id": ""
#         }, ...{}
#     ],
#     "activated": [],
#     "deactivated": [],
# }
from core.utils import gen_random_string


def create_agency_users(agency, users_data, is_active=True):
    created_users = []
    for data in users_data:
        user = User.objects.filter(email=data['email']).first()
        if not user:
            user = User.objects.create(
                **data, is_active=is_active, password=gen_random_string(), country='jp',
            )
        else:
            message = (
                'User with email {} is already exists.'
                'Do you want to set Zoho ID to it? [y/n]: '.format(user.email)
            )
            if strtobool(input(message)):
                user.zoho_id = data['zoho_id']
                user.save()

        created_users.append(user)
        agency.assign_recruiter(user)

    return created_users


def add_zoho_id_to_agency_users(agency, users_data):
    users = agency.members
    updated_users = []
    nonfound_users = []

    for user_data in users_data:
        user = users.filter(email=user_data['email']).first()
        if not user:
            nonfound_users.append(user_data)
            continue

        user.zoho_id = user_data['zoho_id']
        user.save()
        updated_users.append(user)

    if nonfound_users:
        print('Some users are not found:')
        for user in nonfound_users:
            print(user)

    return updated_users


def migrate_zoho_users(agency, users_data):
    # add Zoho ID to existing users
    print('Adding Zoho ID to already existing users...')
    add_zoho_id_to_agency_users(agency, users_data['existing'])
    print('Successfully added Zoho ID to already existing users.')

    # create new active users
    print('Creating new active users...')
    create_agency_users(agency, users_data['activated'])
    print('Successfully created new active users.')

    # create new deactivated users
    print('Creating new deactivated users...')
    create_agency_users(agency, users_data['deactivated'], is_active=False)
    print('Successfully created new deactivated users')


class Command(BaseCommand):
    help = 'Creates new users, link them with zoho ids.'

    def add_arguments(self, parser):
        """Add management command arguments."""
        parser.add_argument('agency_id', nargs=1, type=int)
        parser.add_argument('file', nargs='?', type=str)

    def handle(self, *args, **options):
        """Execute the command function."""
        agency = Agency.objects.get(pk=options['agency_id'][0])
        with open(options['file']) as f:
            users_data = json.load(f)

        while True:
            try:
                message = 'Import Users to "{}" Agency? [y/n] '.format(agency.name)
                if not strtobool(input(message)):
                    print('Import canceled')
                    return

                break
            except ValueError:
                print('Answer must be either y or n')

        migrate_zoho_users(agency, users_data)
