from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from core import fixtures as f, serializers as s, models as m

PENDING = m.FeeStatus.PENDING.key


def create_proposal_and_related_objects():
    client = f.create_client()
    agency = f.create_agency()
    f.create_contract(agency, client)

    m.AgencyClientInfo.objects.create(
        client=client,
        agency=agency,
        originator=f.create_agency_manager(agency),
        industry=m.Industry.ELECTRONIC_GOODS.key,
        type=m.ClientType.NEW_ACCOUNT.key,
    )

    user = f.create_recruiter(agency)

    job = f.create_job(org=client, client=client)
    job.assign_member(user)
    m.JobAgencyContract.objects.create(
        job=job,
        agency=agency,
        industry=m.Industry.ELECTRONIC_GOODS.key,
        contract_type=m.ContractType.MTS.key,
        contact_person_name='John Cryhton',
    )

    candidate = f.create_candidate(
        agency,
        created_by=user,
        owner=f.create_agency_manager(agency),
        name_collect=f.create_agency_manager(agency),
        mobile_collect=f.create_agency_manager(agency),
        activator=f.create_agency_manager(agency),
        lead_consultant=f.create_agency_manager(agency),
        support_consultant=f.create_agency_manager(agency),
        source='Job Boards',
    )

    proposal = f.create_proposal(job, candidate, user)

    return proposal


def get_default_split_allocation_data(fee):
    proposal = fee.placement.proposal
    agency = proposal.created_by.org
    lead_bd_consultant = f.create_agency_manager(agency)
    client_info = m.AgencyClientInfo.objects.filter(
        client=proposal.job.client, agency=agency,
    ).first()
    candidate = proposal.candidate
    return dict(
        fee=fee.id,
        client_originator=client_info.originator_id,
        candidate_owner=candidate.owner_id,
        activator=candidate.activator_id,
        lead_candidate_consultant=candidate.lead_consultant_id,
        lead_bd_consultant=lead_bd_consultant.id,
        support_consultant=candidate.support_consultant_id,
        candidate_source=candidate.source,
        client_originator_split=0.1,
        candidate_owner_split=0.2,
        activator_split=0.15,
        lead_candidate_consultant_split=0.3,
        lead_bd_consultant_split=0.15,
        support_consultant_split=0.1,
    )


class FeeSplitAllocationSerializerTests(TestCase):
    api_factory = APIRequestFactory()

    def get_serializer_kwargs(self, fee):
        request = self.api_factory.post('/')
        request.user = fee.created_by

        return {
            'data': get_default_split_allocation_data(fee),
            'context': {'request': request},
        }

    def test_valid(self):
        proposal = create_proposal_and_related_objects()

        fee = f.create_fee(proposal, proposal.created_by)

        request = self.api_factory.post('/')
        request.user = fee.created_by

        serializer = s.FeeSplitAllocationSerializer(**self.get_serializer_kwargs(fee))

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

    def test_invalid_sum(self):
        proposal = create_proposal_and_related_objects()

        fee = f.create_fee(proposal, proposal.created_by)

        request = self.api_factory.post('/')
        request.user = fee.created_by

        serializer_kwargs = self.get_serializer_kwargs(fee)
        serializer_kwargs['data']['candidate_owner_split'] = 0.12

        serializer = s.FeeSplitAllocationSerializer(**serializer_kwargs)

        self.assertFalse(serializer.is_valid())
        expected_errors = {
            field: ['Splits must add up to 100%']
            for field in (
                'candidate_owner_split',
                'lead_candidate_consultant_split',
                'support_consultant_split',
                'client_originator_split',
                'lead_bd_consultant_split',
                'activator_split',
            )
        }
        self.assertDictEqual(expected_errors, serializer.errors)

    def create_fee(self):
        proposal = create_proposal_and_related_objects()

        return f.create_fee(proposal, proposal.created_by)

    def assert_fee_has_status(self, fee, status):
        fee.refresh_from_db()

        self.assertEqual(status, fee.status)

    def save_serializer(self, **kwargs):
        serializer = s.FeeSplitAllocationSerializer(**kwargs)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        return serializer.save()

    @patch('core.utils.model.notify_fee_status_change')
    def test_notification_create(self, notify):
        fee = self.create_fee()

        serializer_kwargs = self.get_serializer_kwargs(fee)

        serializer_kwargs['data']['fee_status'] = PENDING

        fee = self.save_serializer(**serializer_kwargs).fee

        notify.assert_called_once_with(fee, fee.created_by, PENDING)

    @patch('core.utils.model.notify_fee_status_change')
    def check_notification_update(self, notify, old_status, new_status, is_called=True):
        proposal = create_proposal_and_related_objects()

        agency = proposal.created_by.org

        split_allocation = f.create_split_allocation(
            proposal=proposal,
            created_by=f.create_agency_administrator(agency),
            agency=agency,
            status=old_status,
        )

        serializer_kwargs = self.get_serializer_kwargs(split_allocation.fee)

        serializer_kwargs['instance'] = split_allocation
        serializer_kwargs['data']['fee_status'] = new_status
        serializer_kwargs['data']['fee'] = split_allocation.fee_id

        fee = self.save_serializer(**serializer_kwargs).fee

        if is_called:
            notify.assert_called_once_with(fee, fee.created_by, new_status)
        else:
            notify.assert_not_called()

        return split_allocation

    def test_notification_update_different_statuses_approved(self):
        split_allocation = self.check_notification_update(
            old_status=m.FeeStatus.PENDING.key, new_status=m.FeeStatus.APPROVED.key,
        )

        proposal = split_allocation.fee.placement.proposal

        self.assertEqual(
            m.ProposalComment.objects.filter(
                proposal=proposal, text='The candidate has been placed'
            ).count(),
            1,
        )

    def test_notification_update_different_statuses(self):
        split_allocation = self.check_notification_update(
            old_status=m.FeeStatus.PENDING.key,
            new_status=m.FeeStatus.NEEDS_REVISION.key,
        )

        proposal = split_allocation.fee.proposal

        self.assertEqual(
            m.ProposalComment.objects.filter(
                proposal=proposal, text='The candidate has been placed'
            ).count(),
            0,
        )

    def test_notification_update_same_status(self):
        same_status = m.FeeStatus.DRAFT.key
        self.check_notification_update(
            old_status=same_status, new_status=same_status, is_called=False,
        )

    def test_create_set_status(self):
        fee = self.create_fee()
        serializer_kwargs = self.get_serializer_kwargs(fee)

        serializer_kwargs['data']['fee_status'] = PENDING

        self.save_serializer(**serializer_kwargs)

        self.assert_fee_has_status(fee, PENDING)

    def test_update_set_status(self):
        proposal = create_proposal_and_related_objects()

        agency = proposal.created_by.org

        split_allocation = f.create_split_allocation(
            proposal=proposal,
            created_by=f.create_agency_administrator(agency),
            agency=agency,
        )

        serializer_kwargs = self.get_serializer_kwargs(split_allocation.fee)
        serializer_kwargs['instance'] = split_allocation
        serializer_kwargs['data']['fee'] = split_allocation.fee_id
        serializer_kwargs['data']['fee_status'] = PENDING

        self.save_serializer(**serializer_kwargs)

        self.assert_fee_has_status(split_allocation.fee, PENDING)

    def test_other_org_fee(self):
        other_org_proposal = create_proposal_and_related_objects()

        other_org_fee = f.create_fee(other_org_proposal, other_org_proposal.created_by)

        request = self.api_factory.post('/')
        request.user = f.create_agency_manager(f.create_agency())

        data = get_default_split_allocation_data(other_org_fee)

        serializer = s.FeeSplitAllocationSerializer(
            data=data, context={'request': request},
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            {'fee': [f'Invalid pk "{data["fee"]}" - object does not exist.']},
            serializer.errors,
        )
