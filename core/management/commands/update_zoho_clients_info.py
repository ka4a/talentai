from distutils.util import strtobool

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ValidationError

from core.models import Agency, Client, Industry, AgencyClientInfo
from core.zoho import ZohoRecruitClient, zoho_data_to_dict
from core.utils import map_data


AGENCY_CLIENT_FIELDS_MAPPING = {
    'info': 'About',
    'notes': 'Consultant Notes',
    'primary_contact_number': 'Contact Number',
    'portal_url': 'Portal URL',
    'website': 'Website',
    'billing_address': 'Client Address',
    'portal_password': 'Portal Login Details',
}


def get_client_zoho_id_from_zoho_data(zoho_data):
    for field in zoho_data:
        if field.get('val') == 'CLIENTID':
            return field['content']


def to_agency_client_data(zoho_data, agency):
    agency_client_data = {}
    client_zoho_id = get_client_zoho_id_from_zoho_data(zoho_data)

    fields_data = zoho_data_to_dict(zoho_data)
    agency_client_data.update(map_data(fields_data, AGENCY_CLIENT_FIELDS_MAPPING))

    if 'Account Manager' in fields_data:
        names = fields_data['Account Manager'].split(' ')
        if len(names) == 1:
            names.append('')

        agency_client_data['account_manager'] = agency.members.filter(
            first_name=names[0], last_name=names[1]
        ).first()

    if 'Industry' in fields_data:
        agency_client_data['industry'] = Industry.get_key_by_value(
            fields_data['Industry']
        )

    try:
        AgencyClientInfo(**agency_client_data).clean_fields()
    except ValidationError as e:
        fields = list(e.message_dict.keys())
        for field in fields:
            agency_client_data.pop(field, None)

    return client_zoho_id, agency_client_data


def update_client_info(zoho_auth_token, agency, existing_pks):
    zoho_client = ZohoRecruitClient(zoho_auth_token, 'Clients')
    clients = Client.objects.filter(Q(owner_agency=agency) & ~Q(zoho_id=''))
    count = 0
    with transaction.atomic():
        for zoho_data in zoho_client.get_all_records(index_range=200):
            client_zoho_id, agency_client_data = to_agency_client_data(
                zoho_data['FL'], agency
            )
            client = clients.filter(
                Q(zoho_id=client_zoho_id) & ~Q(pk__in=existing_pks)
            ).first()
            if client:
                AgencyClientInfo.objects.update_or_create(
                    client=client, agency=agency, defaults={**agency_client_data}
                )
                count += 1
    return count


class Command(BaseCommand):
    help = 'Update client info from by Zoho data'

    def add_arguments(self, parser):
        """Add management command arguments"""
        parser.add_argument('zoho_auth_token', nargs='?', type=str)
        parser.add_argument('agency_id', nargs=1, type=int)
        parser.add_argument('existing_clients', nargs=1, type=str)  # 1,2,3

    def handle(self, *args, **options):
        agency = Agency.objects.get(pk=options['agency_id'][0])
        zoho_auth_token = options['zoho_auth_token']
        existing_pks = options['existing_clients'][0].split(',')

        while True:
            try:
                message = (
                    'Update client info for "{}" Agency? '
                    'Make sure Users and Clients are already imported. [y/n] '.format(
                        agency.name
                    )
                )
                if not strtobool(input(message)):
                    print('Import canceled')
                    return

                break
            except ValueError:
                print('Answer must be either y or n')

        count = update_client_info(zoho_auth_token, agency, existing_pks)

        print(f'Successfully updated info for {count} clients')
