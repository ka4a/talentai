from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from core import (
    models as m,
    fixtures as f,
)


class InputSideEffect:
    def __init__(self, mock, answers):
        self.mock = mock
        self.answers = answers

    def __call__(self, *args, **kwargs):
        return self.answers[self.mock.call_count - 1]


def create_jobs_for_clients(clients, count, agency=None):
    jobs = []
    for client in clients:
        for i in range(count):
            job = f.create_job(client)
            jobs.append(job)
            if agency:
                job.assign_agency(agency)

    return jobs


def create_clients(
    name,
    count,
    agency=None,
    contract_status=m.ContractStatus.INITIATED.key,
    should_create_contract=True,
    should_create_job=True,
    should_assign_job=True,
):
    clients = []
    for i in range(count):
        client = f.create_client(name=name.format(i))
        clients.append(client)

        if should_create_contract and agency is not None:
            f.create_contract(agency, client, status=contract_status)

        if should_create_job:
            job = f.create_job(client)
            if agency is not None and should_assign_job:
                job.assign_agency(agency)
    return clients


class TestTurnContractedClientsIntoAgencyClients(TestCase):
    def assert_agency_assigned_to_job(self, job, agency, expected=True, msg=None):
        self.assertEqual(
            m.JobAgencyContract.objects.filter(agency=agency, job=job).exists(),
            expected,
            msg=msg,
        )

    def assert_job_owned_by_client(self, job, msg=None):
        self.assertEqual(type(job.organization), m.Client, msg=msg)
        self.assertEqual(type(job.owner.profile.org), m.Client, msg=msg)

    def assert_jobs_owned_by_agency(self, jobs, agency):
        i = 0
        for job in jobs:
            job.refresh_from_db()
            self.assertEqual(job.organization, agency, msg=i)
            self.assertEqual(job.owner, agency.primary_contact, msg=i)
            self.assert_agency_assigned_to_job(job, agency, False, i)
            i += 1

    def assert_jobs_owned_by_client(self, jobs, was_assigned_to_agency=True):
        i = 0
        for job in jobs:
            job.refresh_from_db()
            if was_assigned_to_agency:
                self.assert_job_owned_by_client(job, i)
                i += 1

    def assert_clients_owned_by_agency(self, clients, agency):
        i = 0
        for client in clients:
            client.refresh_from_db()
            self.assertEqual(client.owner_agency, agency, msg=i)
            i += 1

    def assert_clients_not_owned_by_agency(self, clients):
        i = 0
        for client in clients:
            client.refresh_from_db()
            self.assertIsNone(client.owner_agency, msg=i)
            i += 1

    @patch('builtins.input')
    def test_skip_client(self, input_mock):
        agency = f.create_agency(name='Agency')

        clients = sorted(
            [f.create_client(name='Skip'), f.create_client(name='Client')],
            key=lambda item: item.id,
        )

        agency_clients = []
        skipped_clients = []
        client_answers = []
        for client in clients:
            f.create_contract(agency, client)

            answer = 'y'
            if client.name == 'Skip':
                answer = 'n'
                skipped_clients.append(client)
            else:
                agency_clients.append(client)

            client_answers.append(answer)

        jobs = create_jobs_for_clients(agency_clients, 2, agency)
        skipped_jobs = create_jobs_for_clients(skipped_clients, 2, agency)

        input_mock.side_effect = InputSideEffect(input_mock, client_answers)

        call_command('turn_contracted_clients_into_agency_clients', agency.id)

        self.assert_clients_owned_by_agency(agency_clients, agency)
        self.assert_clients_not_owned_by_agency(skipped_clients)

        self.assert_jobs_owned_by_agency(jobs, agency)
        self.assert_jobs_owned_by_client(skipped_jobs)

    @patch('builtins.input', return_value='y')
    def test_exists(self, input_mock):
        agency = f.create_agency()

        clients = create_clients('Client {}', 3, agency, should_create_job=False)
        for i in range(3):
            client = f.create_client(name=f'Client {i}')
            clients.append(client)

            f.create_contract(agency, client)

        uncontracted_clients = create_clients(
            'Uncontracted Client {}', 2, agency, should_create_contract=False
        )

        clients_with_noninit_contracts = create_clients(
            'Client With Expired Contract {}',
            2,
            contract_status=m.ContractStatus.EXPIRED.key,
        )

        jobs = create_jobs_for_clients(clients, 2, agency)

        unassigned_jobs = create_jobs_for_clients(clients, 2)

        expired_contract_jobs = []
        for i in range(5):
            job = f.create_job(clients_with_noninit_contracts[0])
            expired_contract_jobs.append(job)

            job.assign_agency(agency)

        call_command('turn_contracted_clients_into_agency_clients', agency.id)

        self.assert_clients_owned_by_agency(clients, agency)
        self.assert_clients_not_owned_by_agency(clients_with_noninit_contracts)

        self.assert_jobs_owned_by_agency(jobs, agency)
        self.assert_jobs_owned_by_client(unassigned_jobs)
        self.assert_jobs_owned_by_client(expired_contract_jobs)
        self.assert_jobs_owned_by_client(
            uncontracted_clients, was_assigned_to_agency=False
        )
