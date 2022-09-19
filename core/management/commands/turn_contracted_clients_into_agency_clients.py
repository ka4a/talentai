from distutils.util import strtobool

from core.models import Agency, Client, ContractStatus
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Make clients controllable by agency to an extent and transfers'
        ' all jobs from client that assigned specified agency to a job'
    )

    def add_arguments(self, parser):
        """Add management command arguments."""
        parser.add_argument('agency_id', nargs=1, type=int)

    def handle(self, *args, **options):
        """Execute the command function."""
        agency = Agency.objects.get(pk=options['agency_id'][0])

        print(f'Transfering contracted clients control to {agency.name}')

        qs_clients = Client.objects.filter(
            contracts__agency=agency, contracts__status=ContractStatus.INITIATED.key
        ).order_by('id')

        for client in qs_clients:
            message = f'Do you want to transfer jobs from "{client.name}" to "{agency.name}" and to make "{client.name}" agency controlled client?'
            print(message)

            should_skip_client = None
            while should_skip_client is None:
                try:
                    should_skip_client = not strtobool(input("\n"))
                except ValueError:
                    print('Answer must be either y or n')

            if should_skip_client:
                print(f'Skipping "{client.name}"')
                continue

            print(f'Making "{client.name}" jobs manageable by "{agency.name}"')
            client.owner_agency = agency
            client.save()

            print(
                f'Moving existing jobs of "{client.name}" under "{agency.name}" control'
            )
            qs_jobs = agency.apply_guest_jobs_filter(client.jobs.all())

            for job in qs_jobs:
                job.organization = agency
                job.owner = agency.primary_contact
                job.save()
                job.withdraw_agency(agency)

            print(f'Now "{client.name}" jobs belong to "{agency.name}"')
