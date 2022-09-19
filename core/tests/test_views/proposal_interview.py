from datetime import datetime
from unittest.mock import patch

import pytz
from django.utils.dateparse import parse_datetime
from django.utils.timezone import utc

from djangorestframework_camel_case.util import camelize
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from core import fixtures as f, serializers as s, models as m, factories as fa
from core.tests.generic_response_assertions import GenericResponseAssertionSet
from core.factories import UserFactory, ProposalInterviewFactory, ClientFactory


class TestProposalInterviewViewSet(APITestCase):
    def setUp(self):
        client = ClientFactory.create()
        self.client_org = client

        self.client_admin = self.client_org.primary_contact
        self.client_org.assign_administrator(self.client_admin)

        self.recruiter = UserFactory.create()
        client.assign_internal_recruiter(self.recruiter)

        self.user = UserFactory.create()
        client.assign_standard_user(self.user)

        self.interview = ProposalInterviewFactory.create(
            client=client, interviewer=self.user,
        )
        self.assert_response = GenericResponseAssertionSet(self)

        self.default_payload = {
            'status': m.ProposalInterviewSchedule.Status.SCHEDULED,
            'scheduling_type': m.ProposalInterviewSchedule.SchedulingType.SIMPLE_SCHEDULING,
            'start_at': f.DEFAULT_INTERVIEW.start_at,
            'end_at': f.DEFAULT_INTERVIEW.end_at,
            'interviewer': self.interview.interviewer.pk,
        }

    @patch('core.views.proposals.notify_proposal_interview_confirmed')
    def test_simple_scheduling_scheduled(self, notify_confirmed):
        payload = {
            **self.default_payload,
            'scheduling_type': m.ProposalInterviewSchedule.SchedulingType.SIMPLE_SCHEDULING,
        }
        self.client.force_login(self.client_admin)
        self.assert_response.ok(
            'patch', 'proposal_interviews-detail', self.interview.pk, payload
        )
        self.assertTrue(notify_confirmed.called)

    @patch('core.views.proposals.notify_proposal_interview_confirmed')
    def test_past_scheduling_scheduled(self, notify_confirmed):
        payload = {
            **self.default_payload,
            'scheduling_type': m.ProposalInterviewSchedule.SchedulingType.PAST_SCHEDULING,
            'start_at': datetime(2018, 1, 1, 12, 0, tzinfo=pytz.UTC),
            'end_at': datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
        }
        self.client.force_login(self.client_admin)
        self.assert_response.ok(
            'patch', 'proposal_interviews-detail', self.interview.pk, payload
        )
        self.assertFalse(notify_confirmed.called)
