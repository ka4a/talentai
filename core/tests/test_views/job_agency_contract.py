from rest_framework.test import APITestCase

from core import fixtures as f, models as m
from core.tests.generic_response_assertions import GenericResponseAssertionSet


class JobAgencyContractTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.assert_response = GenericResponseAssertionSet(self)

    def test_retrieve(self):
        client = f.create_client()
        agency = f.create_agency()
        job = f.create_job(client, client)
        job_agency_contract = m.JobAgencyContract.objects.create(
            job=job, agency=agency,
        )

        self.client.force_login(f.create_agency_administrator(agency))

        self.assert_response.ok(
            'get', 'job-agency-contract-detail', job_agency_contract.pk
        )

    def test_put(self):
        client = f.create_client()
        agency = f.create_agency()
        job = f.create_job(client, client)
        job_agency_contract = m.JobAgencyContract.objects.create(
            job=job, agency=agency,
        )

        self.client.force_login(f.create_agency_administrator(agency))

        self.assert_response.ok(
            'patch',
            'job-agency-contract-detail',
            job_agency_contract.pk,
            {
                'bill_description': m.BillDescription.INTERNAL.key,
                'contract_type': m.ContractType.MTS.key,
                'industry': m.Industry.ELECTRONIC_GOODS.key,
                'contact_person_name': 'Frank Klepatskovich',
            },
        )

        job_agency_contract.refresh_from_db()

        self.assertTrue(job_agency_contract.is_filled_in)

    def test_put_missing_field(self):
        client = f.create_client()
        agency = f.create_agency()
        job = f.create_job(client, client)
        job_agency_contract = m.JobAgencyContract.objects.create(
            job=job, agency=agency,
        )

        self.client.force_login(f.create_agency_administrator(agency))

        err_is_required = ['This field is required.']

        self.assert_response.bad_request(
            'put',
            'job-agency-contract-detail',
            job_agency_contract.pk,
            data={'industry': m.Industry.ELECTRONIC_GOODS.key},
            expected_data={
                key: err_is_required
                for key in ['signedAt', 'contractType', 'contactPersonName']
            },
        )
