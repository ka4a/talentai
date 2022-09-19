import json
from distutils.util import strtobool

from django.core.management.base import BaseCommand

from core.models import User, Agency
from core.fixtures import create_agency
from core.management.commands.migrate_zoho_users import (
    migrate_zoho_users,
    create_agency_users,
)
from core.utils import gen_random_string


def create_agency(name):
    primary_contact = User.objects.create(
        first_name='Agency',
        last_name='Primary Contact',
        email=gen_random_string() + '@test.com',
        password=gen_random_string(),
        country='jp',
    )
    return Agency.objects.create(
        name=name, primary_contact=primary_contact, country='jp'
    )


class Command(BaseCommand):
    help = 'Emulate production state on the staging for Zoho users migration process'

    def add_arguments(self, parser):
        """Add management command arguments."""
        parser.add_argument('file', nargs='?', type=str)

    def handle(self, *args, **options):
        """Execute the command function."""
        input_file_path = options['file']

        with open(input_file_path) as file:
            users_data = json.load(file)

        # Creating test agency
        agency_name = input('Please enter an agency name that will emulate HCCR: ')
        agency = create_agency(agency_name)
        print(
            'Successfully created agency {} with id {}'.format(agency.name, agency.id)
        )

        # Create users that should be already existed in the agency
        print('Creating users that already exist in HCCR agency on the prod...')
        create_agency_users(agency, users_data['existing'])
        print('Successfully created users for {}:'.format(agency.name))

        # run migration process
        migrate_zoho_users(agency, users_data)

        while True:
            message = 'All created data will be removed. Check it and continue [y]: '
            if strtobool(input(message)):
                break

        # remove test data
        primary_contact_pk = agency.primary_contact.pk
        agency.primary_contact = None
        agency.save()
        User.objects.get(pk=primary_contact_pk).delete()
        agency.members.delete()
        agency.delete()
