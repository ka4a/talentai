from datetime import datetime
from django.utils.timezone import utc
from unittest.mock import patch
from djangorestframework_camel_case.util import camelize
from rest_framework.test import APITestCase
from core.tests.generic_response_assertions import GenericResponseAssertionSet

from core import serializers as s, fixtures as f, models as m


APPROVED = m.FeeStatus.APPROVED.key
PENDING = m.FeeStatus.PENDING.key


def get_default_data(proposal):
    result = dict(f.DEFAULT_FEE)

    result['placement'] = {**f.DEFAULT_PLACEMENT, 'proposal': proposal.id}

    return result


def create_contract():
    client = f.create_client()
    agency = f.create_agency()
    return f.create_contract(agency, client)


def create_proposal(contract, created_by, is_agency_job=False):
    org = contract.agency if is_agency_job else contract.client

    job = f.create_job(org=org, client=contract.client)

    candidate = f.create_candidate(created_by.org, created_by=created_by)

    proposal = f.create_proposal(job, candidate, created_by)

    return proposal


def get_proposal_not_found_error(proposal):
    return {'proposal': [f'Invalid pk "{proposal.id}" - object does not exist.']}


class CandidatePlacement(APITestCase):
    def setUp(self):
        self.assert_response = GenericResponseAssertionSet(self)

    def assert_post_proposal_not_available(self, proposal):
        data = get_default_data(proposal)
        self.assert_response.bad_request(
            'post',
            'fee-list',
            data=data,
            expected_data=get_proposal_not_found_error(proposal),
        )

    def test_post_anonymous(self):
        contract = create_contract()
        user = f.create_agency_administrator(contract.agency)

        proposal = create_proposal(contract, user)

        data = get_default_data(proposal)

        self.assert_response.not_authenticated('post', 'fee-list', data=data)

    def check_post_agency_user(self, create_user, assertion):
        contract = create_contract()
        user = create_user(contract.agency)

        self.client.force_login(user)

        proposal = create_proposal(contract, user)
        proposal.job.assign_member(user)

        data = get_default_data(proposal)
        assertion('post', 'fee-list', data=data)

    def test_post_recruiter(self):
        self.check_post_agency_user(f.create_recruiter, self.assert_response.created)

    def test_post_doesnt_create_placement(self):
        contract = create_contract()
        user = f.create_recruiter(contract.agency)

        self.client.force_login(user)

        proposal = create_proposal(contract, user)
        proposal.job.assign_member(user)

        data = get_default_data(proposal)
        data['ios_ioa'] = None
        unique_salary = 2379
        data['placement']['target_salary'] = unique_salary
        self.assert_response.bad_request('post', 'fee-list', data=data)

        self.assertFalse(
            m.Placement.objects.filter(target_salary=unique_salary).exists(),
        )

    def test_post_client_proposal(self):
        contract = create_contract()
        user = f.create_recruiter(contract.agency)

        talent_associate = f.create_client_administrator(contract.client)

        proposal = create_proposal(contract, talent_associate)
        proposal.job.assign_member(user)

        self.client.force_login(user)

        self.assert_post_proposal_not_available(proposal)

    @patch('core.views.views.notify_fee_status_change')
    def test_post_notification(self, notify):
        contract = create_contract()
        user = f.create_recruiter(contract.agency)

        proposal = create_proposal(contract, user)
        proposal.job.assign_member(user)

        data = get_default_data(proposal)
        data['status'] = m.FeeStatus.PENDING.key
        self.client.force_login(user)

        placement_id = self.assert_response.created(
            'post', 'fee-list', data=data,
        ).json()['id']

        notify.assert_called_once_with(
            m.Fee.objects.get(id=placement_id), user,
        )

    @patch('core.views.views.notify_fee_status_change')
    def test_post_notification_draft(self, notify):
        contract = create_contract()
        user = f.create_recruiter(contract.agency)

        proposal = create_proposal(contract, user)
        proposal.job.assign_member(user)

        data = get_default_data(proposal)
        data['status'] = m.FeeStatus.DRAFT.key
        self.client.force_login(user)

        self.assert_response.created('post', 'fee-list', data=data,).json()['id']

        notify.assert_not_called()

    def test_post_agency_admin(self):
        self.check_post_agency_user(
            f.create_agency_administrator, self.assert_response.created
        )

    def test_post_agency_manager(self):
        self.check_post_agency_user(
            f.create_agency_manager, self.assert_response.created
        )

    def check_post_client_user(self, create_user, assertion):
        contract = create_contract()
        user = create_user(contract.client)

        self.client.force_login(user)

        proposal = create_proposal(contract, user)

        data = get_default_data(proposal)
        assertion('post', 'fee-list', data=data)

    def test_post_talent_associate(self):
        self.check_post_client_user(
            f.create_client_administrator, self.assert_response.no_permission
        )

    def test_post_hiring_manager(self):
        self.check_post_client_user(
            f.create_hiring_manager, self.assert_response.no_permission
        )

    def test_patch_anonymous(self):
        contract = create_contract()
        user = f.create_agency_administrator(contract.agency)

        proposal = create_proposal(contract, user)

        data = get_default_data(proposal)

        placement = f.create_fee(proposal, user)

        self.assert_response.not_authenticated(
            'patch', 'fee-detail', placement.id, data=data
        )

    def assert_patch_ok(self, proposal, placement):
        data = get_default_data(proposal)
        self.assert_response.ok('patch', 'fee-detail', placement.id, data=data)

    def init_patch_by_agency_user_check(
        self, create_user, is_creator=False, is_submitter=False, status=None
    ):

        contract = create_contract()
        user = create_user(contract.agency)

        proposal = create_proposal(contract, user)
        proposal.job.assign_member(user)

        creator = user if is_creator else f.create_recruiter(contract.agency)

        placement = f.create_fee(proposal, creator)

        if is_submitter:
            placement.submitted_by = user

        if status:
            placement.status = status

        placement.save()

        self.client.force_login(user)

        return placement

    def test_patch_approved_at(self):
        placement = self.init_patch_by_agency_user_check(f.create_agency_administrator)

        data = get_default_data(placement.proposal)
        data['status'] = APPROVED

        self.assertIsNone(placement.approved_at)
        self.assert_response.ok('patch', 'fee-detail', placement.id, data)

        placement.refresh_from_db()
        self.assertIsNotNone(placement.approved_at)

    def test_patch_approved_at_before(self):
        placement = self.init_patch_by_agency_user_check(f.create_agency_administrator)
        expected_approved_at = datetime(2019, 2, 4, tzinfo=utc)
        placement.approved_at = expected_approved_at

        data = get_default_data(placement.proposal)
        data['status'] = APPROVED

        self.assert_response.ok('patch', 'fee-detail', placement.id, data)

        placement.refresh_from_db()
        self.assertNotEqual(expected_approved_at, placement.approved_at)

    def check_patch_agency_user(
        self, create_user, assertion, is_creator=False, is_submitter=False, status=None
    ):
        placement = self.init_patch_by_agency_user_check(
            create_user, is_creator, is_submitter, status
        )

        data = get_default_data(placement.proposal)

        assertion('patch', 'fee-detail', placement.id, data=data)

    def check_patch_recruiter(self, *args, **kwargs):
        self.check_patch_agency_user(f.create_recruiter, *args, **kwargs)

    @patch('core.views.views.notify_fee_status_change')
    def check_patch_notification(self, notify, old_status, new_status):
        contract = create_contract()
        user = f.create_agency_administrator(contract.agency)

        self.client.force_login(user)

        proposal = create_proposal(contract, user)
        proposal.job.assign_member(user)

        creator = user

        placement = f.create_fee(proposal, creator)

        placement.submitted_by = user

        placement.status = old_status

        placement.save()

        data = get_default_data(proposal)
        data['status'] = new_status

        self.assert_response.ok('patch', 'fee-detail', placement.id, data=data)

        notify.assert_called_once_with(placement, user)

    def test_patch_status_change_to_pending(self):
        self.check_patch_notification(
            old_status=m.FeeStatus.DRAFT.key, new_status=m.FeeStatus.PENDING.key,
        )

    def test_patch_status_change_to_draft(self):
        self.check_patch_notification(
            old_status=m.FeeStatus.PENDING.key, new_status=m.FeeStatus.DRAFT.key,
        )

    def test_patch_recruiter_unrelated(self):
        self.check_patch_recruiter(self.assert_response.not_found)

    def test_patch_recruiter_unrelated_approved(self):
        self.check_patch_recruiter(self.assert_response.not_found, status=APPROVED)

    def test_patch_recruiter_unrelated_pending(self):
        self.check_patch_recruiter(self.assert_response.not_found, status=PENDING)

    def test_patch_recruiter_submitter(self):
        self.check_patch_recruiter(self.assert_response.ok, is_submitter=True)

    def test_patch_recruiter_creator(self):
        self.check_patch_recruiter(self.assert_response.ok, is_creator=True)

    def test_patch_recruiter_submitter_approved(self):
        self.check_patch_recruiter(
            self.assert_response.no_permission, is_submitter=True, status=APPROVED
        )

    def test_patch_recruiter_creator_approved(self):
        self.check_patch_recruiter(
            self.assert_response.no_permission, is_creator=True, status=APPROVED
        )

    def test_patch_recruiter_submitter_pending(self):
        self.check_patch_recruiter(
            self.assert_response.no_permission, is_submitter=True, status=PENDING
        )

    def test_patch_recruiter_creator_pending(self):
        self.check_patch_recruiter(
            self.assert_response.no_permission, is_creator=True, status=PENDING
        )

    def test_patch_client_proposal(self):
        contract = create_contract()
        user = f.create_agency_manager(contract.agency)

        talent_associate = f.create_client_administrator(contract.client)

        proposal = create_proposal(contract, talent_associate)

        proposal.job.assign_member(user)

        self.client.force_login(user)

        data = get_default_data(proposal)

        placement = f.create_fee(create_proposal(contract, user), user)

        self.assert_response.bad_request(
            'patch',
            'fee-detail',
            placement.id,
            data,
            expected_data=get_proposal_not_found_error(proposal),
        )

    def check_patch_agency_admin(self, *args, **kwargs):
        self.check_patch_agency_user(f.create_agency_administrator, *args, **kwargs)

    def test_patch_agency_admin_unrelated(self):
        self.check_patch_agency_admin(self.assert_response.ok)

    def test_patch_agency_admin_submitter(self):
        self.check_patch_agency_admin(self.assert_response.ok, is_submitter=True)

    def test_patch_agency_admin_creator(self):
        self.check_patch_agency_admin(self.assert_response.ok, is_creator=True)

    def test_patch_agency_admin_submitter_approved(self):
        self.check_patch_agency_admin(
            self.assert_response.ok, is_submitter=True, status=APPROVED
        )

    def test_patch_agency_admin_creator_approved(self):
        self.check_patch_agency_admin(
            self.assert_response.ok, is_creator=True, status=APPROVED
        )

    def test_patch_agency_admin_submitter_pending(self):
        self.check_patch_agency_admin(
            self.assert_response.ok, is_submitter=True, status=PENDING
        )

    def test_patch_agency_admin_creator_pending(self):
        self.check_patch_agency_admin(
            self.assert_response.ok, is_creator=True, status=PENDING
        )

    def test_patch_other_agency(self):
        contract = create_contract()
        user = f.create_agency_administrator(contract.agency)

        another_agency = f.create_agency()
        another_agency_user = f.create_agency_administrator(another_agency)

        f.create_contract(another_agency, contract.client)

        self.client.force_login(user)

        proposal = create_proposal(contract, another_agency_user)

        placement = f.create_fee(proposal, another_agency_user)

        data = get_default_data(proposal)
        self.assert_response.not_found(
            'patch', 'fee-detail', placement.id, data,
        )

    def check_patch_agency_manager(self, *args, **kwargs):
        self.check_patch_agency_user(f.create_agency_manager, *args, **kwargs)

    def test_patch_agency_manager_unrelated(self):
        self.check_patch_agency_manager(self.assert_response.ok)

    def test_patch_agency_manager_submitter(self):
        self.check_patch_agency_manager(self.assert_response.ok, is_submitter=True)

    def test_patch_agency_manager_creator(self):
        self.check_patch_agency_manager(self.assert_response.ok, is_creator=True)

    def test_patch_agency_manager_submitter_approved(self):
        self.check_patch_agency_manager(
            self.assert_response.ok, is_submitter=True, status=APPROVED
        )

    def test_patch_agency_manager_creator_approved(self):
        self.check_patch_agency_manager(
            self.assert_response.ok, is_creator=True, status=APPROVED
        )

    def test_patch_agency_manager_submitter_pending(self):
        self.check_patch_agency_manager(
            self.assert_response.ok, is_submitter=True, status=PENDING
        )

    def test_patch_agency_manager_creator_pending(self):
        self.check_patch_agency_manager(
            self.assert_response.ok, is_creator=True, status=PENDING
        )

    def check_patch_client_user(self, create_user, assertion):
        contract = create_contract()
        user = create_user(contract.client)

        self.client.force_login(user)

        proposal = create_proposal(contract, user)

        placement = f.create_fee(proposal, user, agency=contract.agency)

        data = get_default_data(proposal)

        assertion('patch', 'fee-detail', placement.id, data=data)

    def test_patch_talent_associate(self):
        self.check_patch_client_user(
            f.create_client_administrator, self.assert_response.no_permission
        )

    def test_patch_hiring_manager(self):
        self.check_patch_client_user(
            f.create_hiring_manager, self.assert_response.no_permission
        )

    def check_get_agency_user(
        self,
        create_user,
        assertion,
        is_creator=False,
        is_submitter=False,
        status=None,
        is_editable=None,
    ):
        contract = create_contract()
        user = create_user(contract.agency)

        self.client.force_login(user)

        proposal = create_proposal(contract, user)
        proposal.job.assign_member(user)

        creator = user if is_creator else f.create_recruiter(contract.agency)

        placement = f.create_fee(proposal, creator)

        if is_submitter:
            placement.submitted_by = user

        if status:
            placement.status = status

        placement.save()

        kwargs = dict(
            method='get',
            view_name='fee-detail',
            pk=placement.id,
            data=get_default_data(proposal),
        )
        if assertion == 'ok':
            response_data = self.assert_response.ok(**kwargs).json()
            response_is_editable = response_data.pop('isEditable')

            self.assertDictEqual(
                response_data, camelize(s.FeeSerializer(placement).data)
            )

            if is_editable is not None:
                self.assertEqual(is_editable, response_is_editable)
        else:
            assertion(**kwargs)

    # recruiter

    def check_get_recruiter(self, *args, **kwargs):
        self.check_get_agency_user(f.create_recruiter, *args, **kwargs)

    def test_get_recruiter_unrelated(self):
        self.check_get_recruiter(self.assert_response.not_found)

    def test_get_recruiter_submitter(self):
        self.check_get_recruiter('ok', is_submitter=True, is_editable=True)

    def test_get_recruiter_creator(self):
        self.check_get_recruiter('ok', is_creator=True, is_editable=True)

    def test_get_recruiter_unrelated_approved(self):
        self.check_get_recruiter(self.assert_response.not_found, status=APPROVED)

    def test_get_recruiter_submitter_approved(self):
        self.check_get_recruiter(
            'ok', is_submitter=True, status=APPROVED, is_editable=False
        )

    def test_get_recruiter_creator_approved(self):
        self.check_get_recruiter(
            'ok', is_creator=True, status=APPROVED, is_editable=False
        )

    def test_get_recruiter_unrelated_pending(self):
        self.check_get_recruiter(self.assert_response.not_found, status=PENDING)

    def test_get_recruiter_submitter_pending(self):
        self.check_get_recruiter(
            'ok', is_submitter=True, status=PENDING, is_editable=False
        )

    def test_get_recruiter_creator_pending(self):
        self.check_get_recruiter(
            'ok', is_creator=True, status=PENDING, is_editable=False
        )

    # Agency Administrator
    def check_get_agency_admin(self, *args, **kwargs):
        self.check_get_agency_user(f.create_agency_administrator, *args, **kwargs)

    def test_get_agency_admin_unrelated(self):
        self.check_get_agency_admin('ok', is_editable=True)

    def test_get_agency_admin_submitter(self):
        self.check_get_agency_admin('ok', is_submitter=True, is_editable=True)

    def test_get_agency_admin_creator(self):
        self.check_get_agency_admin('ok', is_creator=True, is_editable=True)

    def test_get_agency_admin_unrelated_approved(self):
        self.check_get_agency_admin('ok', status=APPROVED, is_editable=True)

    def test_get_agency_admin_submitter_approved(self):
        self.check_get_agency_admin(
            'ok', is_submitter=True, status=APPROVED, is_editable=True
        )

    def test_get_agency_admin_creator_approved(self):
        self.check_get_agency_admin(
            'ok', is_creator=True, status=APPROVED, is_editable=True
        )

    def test_get_agency_admin_unrelated_pending(self):
        self.check_get_agency_admin('ok', status=PENDING, is_editable=True)

    def test_get_agency_admin_submitter_pending(self):
        self.check_get_agency_admin(
            'ok', is_submitter=True, status=PENDING, is_editable=True
        )

    def test_get_agency_admin_creator_pending(self):
        self.check_get_agency_admin(
            'ok', is_creator=True, status=PENDING, is_editable=True
        )

    # Agency Manager
    def check_get_agency_manager(self, *args, **kwargs):
        self.check_get_agency_user(f.create_agency_manager, *args, **kwargs)

    def test_get_agency_manager_unrelated(self):
        self.check_get_agency_manager('ok', is_editable=True)

    def test_get_agency_manager_submitter(self):
        self.check_get_agency_manager('ok', is_submitter=True, is_editable=True)

    def test_get_agency_manager_creator(self):
        self.check_get_agency_manager('ok', is_creator=True, is_editable=True)

    def test_get_agency_manager_unrelated_approved(self):
        self.check_get_agency_manager('ok', status=APPROVED, is_editable=True)

    def test_get_agency_manager_submitter_approved(self):
        self.check_get_agency_manager(
            'ok', is_submitter=True, status=APPROVED, is_editable=True
        )

    def test_get_agency_manager_creator_approved(self):
        self.check_get_agency_manager(
            'ok', is_creator=True, status=APPROVED, is_editable=True
        )

    def test_get_agency_manager_unrelated_pending(self):
        self.check_get_agency_manager('ok', status=PENDING, is_editable=True)

    def test_get_agency_manager_submitter_pending(self):
        self.check_get_agency_manager(
            'ok', is_submitter=True, status=PENDING, is_editable=True
        )

    def test_get_agency_manager_creator_pending(self):
        self.check_get_agency_manager(
            'ok', is_creator=True, status=PENDING, is_editable=True
        )

    def check_get_client_user(self, create_user, assertion):
        contract = create_contract()
        user = create_user(contract.client)
        created_by = f.create_agency_administrator(contract.agency)

        self.client.force_login(user)

        proposal = create_proposal(contract, user)

        placement = f.create_fee(proposal, created_by)

        assertion('get', 'fee-detail', placement.id)

    def test_get_talent_associate(self):
        self.check_get_client_user(
            f.create_client_administrator, self.assert_response.no_permission
        )

    def test_get_hiring_manager(self):
        self.check_get_client_user(
            f.create_hiring_manager, self.assert_response.no_permission
        )
