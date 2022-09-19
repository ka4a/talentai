import json
from distutils.util import strtobool

from django.core.management.base import BaseCommand

from core.management.commands.migrate_zoho_clients import migrate_agency_clients
from core.management.commands.test_migrate_zoho_users import create_agency
from core.models import User, Client


class Command(BaseCommand):
    help = 'Emulate production state on the staging for Zoho clients migration process'

    def add_arguments(self, parser):
        """Add management command argumants."""
        parser.add_argument('file', nargs='?', type=str)

    def handle(self, *args, **options):
        """Execute the command function."""
        input_file_path = options['file']

        with open(input_file_path) as file:
            clients_data = json.load(file)

        # Creating test agency
        agency_name = input('Please enter an agency name that will emulate HCCR: ')
        agency = create_agency(agency_name)
        print(
            'Successfully created agency {} with id {}'.format(agency.name, agency.id)
        )

        # Create agency client that already exists on the production
        new_clients_data = []  # replace source zookeep ids by generated ones
        for client_data in clients_data:
            if client_data['zookeep_id']:
                client = Client.objects.create(
                    owner_agency=agency, name=client_data['name']
                )
                new_clients_data.append(
                    {
                        'name': client.name,
                        'zoho_id': client_data['zoho_id'],
                        'zookeep_id': client.pk,
                    }
                )
            else:
                new_clients_data.append(client_data)

        # run migration process
        print('Creating agency clients...')
        migrate_agency_clients(agency, new_clients_data)
        print('Successfully created agency clients.')

        while True:
            message = 'All created data will be removed. Check it and continue [y]: '
            if strtobool(input(message)):
                break

        # remove test data
        primary_contact_pk = agency.primary_contact.pk
        agency.primary_contact = None
        agency.save()
        User.objects.get(pk=primary_contact_pk).delete()
        Client.objects.filter(owner_agency=agency).delete()
        agency.delete()
