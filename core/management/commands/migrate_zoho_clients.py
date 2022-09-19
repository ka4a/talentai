import json
from distutils.util import strtobool

from django.core.management.base import BaseCommand

from core.models import Agency, Client


def migrate_agency_clients(agency, clients_data):
    clients = []
    existing_clients = []

    for client_data in clients_data:
        zookeep_id = client_data['zookeep_id']
        if zookeep_id:
            client = Client.objects.filter(pk=zookeep_id).first()
            client.zoho_id = client_data['zoho_id']
            client.save()
            existing_clients.append(client)
        else:
            client = Client(
                owner_agency=agency,
                name=client_data['name'],
                zoho_id=client_data['zoho_id'],
            )
            clients.append(client)
    print('Successfully updated info for already existing clients:')
    for client in existing_clients:
        print(client)

    return Client.objects.bulk_create(clients)


class Command(BaseCommand):
    help = 'Creates new agency clients, link them with zoho ids.'

    def add_arguments(self, parser):
        """Add management command argumants."""
        parser.add_argument('agency_id', nargs=1, type=int)
        parser.add_argument('file', nargs='?', type=str)

    def handle(self, *args, **options):
        """Execute the command function."""
        input_file_path = options['file']
        agency = Agency.objects.get(pk=options['agency_id'][0])

        with open(input_file_path) as file:
            clients_data = json.load(file)

        while True:
            try:
                message = 'Import Users to "{}" Agency? [y/n] '.format(agency.name)
                if not strtobool(input(message)):
                    print('Import canceled')
                    return

                break
            except ValueError:
                print('Answer must be either y or n')

        migrate_agency_clients(agency, clients_data)
