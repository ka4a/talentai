import json
from distutils.util import strtobool

from django.core.management.base import BaseCommand

from core.models import Agency, Candidate


class Command(BaseCommand):
    """Management command to import ProfileData data from li-tool."""

    help = 'Import ProfileData, create Candidates'

    def add_arguments(self, parser):
        """Add management command arguments."""
        parser.add_argument('agency_id', nargs=1, type=int)
        parser.add_argument('file', nargs='?', type=str, default='profile_data.json')

    def handle(self, *args, **options):
        """Execute the command function."""
        agency = Agency.objects.get(pk=options['agency_id'][0])

        while True:
            try:
                message = 'Import Candidates to "{}" Agency? [y/n] '.format(agency.name)
                if not strtobool(input(message)):
                    print('Import canceled')
                    return

                break
            except ValueError:
                print('Answer must be either y or n')

        with open(options['file'], 'r') as file:
            Candidate.objects.bulk_create(
                [
                    Candidate(
                        agency=agency,
                        first_name=pd['first_name'],
                        last_name=pd['last_name'],
                        summary='\n\n'.join(
                            i for i in [pd['headline'], pd['summary']] if i
                        ),
                        current_city=', '.join(
                            i for i in [pd['city'], pd['country']] if i
                        ),
                        li_data=pd,
                    )
                    for pd in json.load(file)
                ]
            )
            print('Candidates created!')
