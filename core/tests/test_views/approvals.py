from rest_framework.test import APITestCase

from core.tests.generic_response_assertions import GenericResponseAssertionSet
from core.models import (
    ContractType,
    BillDescription,
    FeeStatus,
    JobAgencyContract,
    ProposalStatusGroup,
)
import core.fixtures as f


class ApprovalGetTest(APITestCase):
    def setUp(self):
        self.assert_response = GenericResponseAssertionSet(self)

        self.agency = f.create_agency()
        self.contract = f.create_contract(self.agency, f.create_client(name='Client1'))

        self.users = {
            'recruiter': f.create_recruiter(self.agency),
        }

        hired_status = (
            self.agency.proposal_statuses.filter(
                status__group=ProposalStatusGroup.PENDING_START.key
            )
            .first()
            .status
        )
        new_status = (
            self.agency.proposal_statuses.filter(
                status__group=ProposalStatusGroup.ASSOCIATED_TO_JOB.key
            )
            .first()
            .status
        )

        self.job = f.create_contract_job(
            self.contract, title='Carpenter', openings_count=25
        )

        job_agency_contract = JobAgencyContract.objects.get(
            job=self.job, agency=self.agency,
        )
        job_agency_contract.contract_type = ContractType.MTS.key
        job_agency_contract.is_filled_in = True
        job_agency_contract.save()
        self.job_agency_contract = job_agency_contract

        def create_placement_fee(
            created_at,
            proposal,
            status=FeeStatus.PENDING.key,
            created_by=None,
            submitted_by=None,
            **kwargs,
        ):
            return f.create_fee(
                proposal,
                created_by=created_by or proposal.created_by,
                created_at=created_at,
                agency=proposal.candidate.organization,
                job=proposal.job,
                status=status,
                submitted_by=submitted_by,
                **kwargs,
            )

        def create_proposal(
            created_at,
            first_name,
            last_name='Agency1',
            is_hired=True,
            org=self.agency,
            created_by=self.agency.primary_contact,
        ):
            proposal = f.create_proposal(
                job=self.job,
                created_by=created_by,
                candidate=f.create_candidate(
                    organization=org,
                    created_by=created_by,
                    first_name=first_name,
                    last_name=last_name,
                ),
                status=hired_status if is_hired else new_status,
            )

            f.create_proposal_status_history(
                proposal,
                group='offer_accepted' if is_hired else 'new',
                changed_at=created_at,
            )

            return proposal

        self.hired_proposals = [
            create_proposal('2020-01-02', 'X Æ A-12'),
            create_proposal('2020-01-03', 'Placed1',),
            create_proposal('2020-01-04', 'Placed2'),
        ]

        create_proposal('2020-01-05', 'NotHired1', is_hired=False)

        self.fees = [
            create_placement_fee(
                '2020-01-06',
                self.hired_proposals[1],
                bill_description=BillDescription.INTERNAL.key,
            ),
            create_placement_fee(
                '2020-01-07',
                self.hired_proposals[2],
                submitted_by=self.users['recruiter'],
                bill_description=BillDescription.INTERNAL.key,
            ),
            f.create_fee(
                proposal=None,
                job=self.job,
                created_by=self.agency.primary_contact,
                bill_description=BillDescription.MONTHLY.key,
                created_at='2020-01-08',
            ),
            f.create_fee(
                proposal=None,
                job=self.job,
                created_by=self.users['recruiter'],
                submitted_by=self.users['recruiter'],
                bill_description=BillDescription.MONTHLY.key,
                created_at='2020-01-09',
            ),
        ]

        self.maxDiff = None

    def get_approvals(self, approval_type, is_recruiter=False):
        if approval_type == 'fee':
            yield {
                'jobContractId': self.job_agency_contract.id,
                'feeId': self.fees[3].id,
                'proposalId': None,
                'candidateName': None,
                'jobTitle': 'Carpenter',
                'clientName': 'Client1',
                'feeStatus': FeeStatus.DRAFT.key,
                'contractType': ContractType.MTS.key,
                'billDescription': BillDescription.MONTHLY.key,
                'submittedByName': (
                    "{} {}".format(
                        self.fees[3].submitted_by.first_name,
                        self.fees[3].submitted_by.last_name,
                    )
                    if self.fees[3].submitted_by
                    else " "
                ),
                'submittedAt': self.fees[3].submitted_at,
            }
            if not is_recruiter:
                yield {
                    'jobContractId': self.job_agency_contract.id,
                    'proposalId': None,
                    'feeId': self.fees[2].id,
                    'contractType': ContractType.MTS.key,
                    'billDescription': BillDescription.MONTHLY.key,
                    'candidateName': None,
                    'clientName': 'Client1',
                    'jobTitle': 'Carpenter',
                    'feeStatus': FeeStatus.DRAFT.key,
                    'submittedByName': (
                        "{} {}".format(
                            self.fees[2].submitted_by.first_name,
                            self.fees[2].submitted_by.last_name,
                        )
                        if self.fees[2].submitted_by
                        else " "
                    ),
                    'submittedAt': self.fees[2].submitted_at,
                }

        if approval_type == 'placement':
            yield {
                'jobContractId': self.job_agency_contract.id,
                'proposalId': self.hired_proposals[2].id,
                'feeId': self.fees[1].id,
                'contractType': ContractType.MTS.key,
                'billDescription': BillDescription.INTERNAL.key,
                'candidateName': 'Placed2 Agency1',
                'clientName': 'Client1',
                'jobTitle': 'Carpenter',
                'feeStatus': FeeStatus.PENDING.key,
            }
            if not is_recruiter:
                yield {
                    'jobContractId': self.job_agency_contract.id,
                    'proposalId': self.hired_proposals[1].id,
                    'feeId': self.fees[0].id,
                    'contractType': ContractType.MTS.key,
                    'billDescription': BillDescription.INTERNAL.key,
                    'candidateName': 'Placed1 Agency1',
                    'clientName': 'Client1',
                    'jobTitle': 'Carpenter',
                    'feeStatus': FeeStatus.PENDING.key,
                }

        if approval_type == 'proposal':
            yield {
                'jobContractId': self.job_agency_contract.id,
                'proposalId': self.hired_proposals[0].id,
                'feeId': None,
                'contractType': None,
                'billDescription': None,
                'candidateName': 'X Æ A-12 Agency1',
                'clientName': 'Client1',
                'jobTitle': 'Carpenter',
                'feeStatus': None,
            }

    def _test_list(self, user, approval_type, is_recruiter=False):
        self.client.force_login(user)
        response_data = self.assert_response.ok(
            'get', 'approval-list', params={'type': approval_type}
        ).json()['results']

        expected_data = list(self.get_approvals(approval_type, is_recruiter))

        self.assertCountEqual(expected_data, response_data, 'items are wrong')
        self.assertListEqual(expected_data, response_data, 'order is wrong')

    def test_list_agency_admin_fees(self):
        user = f.create_agency_administrator(self.agency)
        self._test_list(user, 'fee')

    def test_list_agency_manager_fees(self):
        user = f.create_agency_manager(self.agency)
        self._test_list(user, 'fee')

    def test_list_recruiter_fees(self):
        self._test_list(self.users['recruiter'], 'fee', True)

    def test_list_client_user(self):
        self.client.force_login(f.create_client_administrator(self.contract.client))
        self.assert_response.no_permission('get', 'approval-list')
