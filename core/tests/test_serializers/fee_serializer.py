from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from core import fixtures as f, serializers as s, models as m


def get_default_data(placement):
    return {
        **f.DEFAULT_FEE,
        'proposal': placement.proposal.id,
        'placement': {**f.DEFAULT_PLACEMENT, 'proposal': placement.proposal.id,},
    }


class FeeSerializerTests(TestCase):
    api_factory = APIRequestFactory()

    def create_proposal(self):
        client = f.create_client()
        agency = f.create_agency()
        f.create_contract(agency, client)

        user = f.create_recruiter(agency)

        job = f.create_job(org=user.profile.org, client=client)
        job.assign_member(user)

        candidate = f.create_candidate(agency, created_by=user)

        proposal = f.create_proposal(job, candidate, user)

        return proposal

    def create_fee(self):
        proposal = self.create_proposal()
        return f.create_fee(proposal, proposal.created_by)

    def get_serializer(self, data, placement, fee=None):
        request = self.api_factory.post('/')
        request.user = placement.proposal.created_by

        kwargs = dict()
        if fee:
            kwargs['instance'] = fee

        return s.FeeSerializer(context={'request': request}, data=data, **kwargs,)

    def test_valid(self):
        placement = self.create_fee()

        serializer = self.get_serializer(get_default_data(placement), placement)

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

    def test_percentage_fee_type_invalid(self):
        placement = self.create_fee()

        data = get_default_data(placement)
        data['consulting_fee_type'] = m.ConsultingFeeType.PERCENTILE.key

        serializer = self.get_serializer(data, placement)

        self.assertFalse(serializer.is_valid())

        self.assertIn('consulting_fee_percentile', serializer.errors)
        self.assertEqual(
            serializer.errors['consulting_fee_percentile'], ['This field is required'],
        )

    def test_fixed_fee_type_invalid(self):
        placement = self.create_fee()

        data = get_default_data(placement)
        del data['consulting_fee']
        data['consulting_fee_type'] = m.ConsultingFeeType.FIXED.key
        data['consulting_fee_percentile'] = 0.1

        serializer = self.get_serializer(data, placement)

        self.assertFalse(serializer.is_valid())

        self.assertIn('consulting_fee', serializer.errors)
        self.assertEqual(
            serializer.errors['consulting_fee'], ['This field is required'],
        )

    def test_serialization(self):
        self.maxDiff = None
        proposal = self.create_proposal()
        fee = f.create_fee(proposal, proposal.created_by)
        expected_data = get_default_data(fee.placement)

        request = self.api_factory.post('/')
        request.user = fee.proposal.created_by
        context = {'request': request}

        expected_data.update(
            id=fee.id,
            proposal=s.ProposalSerializer(fee.proposal, context=context).data,
            proposal_id=fee.proposal_id,
            split_allocation_id=None,
            consulting_fee_percentile=None,
            submitted_by=None,
            contract_type=fee.contract_type,
            invoice_due_date=None,
            invoice_status=m.InvoiceStatus.NOT_SENT.key,
            invoice_paid_at=None,
            client_id=fee.client.id,
        )
        expected_data['placement']['id'] = fee.placement_id
        expected_data['job_contract'] = fee.job_contract_id

        data = s.FeeSerializer(fee, context=context).data

        self.assertCountEqual(expected_data, data)
        self.assertDictEqual(expected_data, data)
