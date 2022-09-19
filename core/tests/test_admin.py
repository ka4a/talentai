"""Tests related to admin page."""
from unittest.case import skip
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from core import models as m
from core import fixtures as f


@skip("ZOO-1243")
class RegistrationRequestApproveTests(APITestCase):
    """Approving registration request tests."""

    def setUp(self):
        """Create the required objects during initialization."""
        super().setUp()
        self.user = f.create_superuser()

        self.client.force_login(self.user)

    def test_agency_registration_request_approve(self):
        """Should create User and Agency."""

        user = f.create_user()

        registration_request = m.AgencyRegistrationRequest.objects.create(
            ip='127.0.0.1', headers={}, name='Agency Name', user=user
        )

        change_url = reverse('admin:core_agencyregistrationrequest_changelist')
        self.client.post(
            change_url,
            {
                'action': 'create_agency',
                '_selected_action': [str(registration_request.pk)],
            },
        )
        user.refresh_from_db()

        self.assertIsNotNone(user.profile)

        agency = m.Agency.objects.get(id=user.profile.agency_id)
        self.assertIsNotNone(agency)
        self.assertEqual(agency.name, 'Agency Name')

    def test_client_registration_request_approve(self):
        """Should create User and Client."""

        user = f.create_user()

        registration_request = m.ClientRegistrationRequest.objects.create(
            ip='127.0.0.1', headers={}, name='Client Name', user=user
        )

        change_url = reverse('admin:core_clientregistrationrequest_changelist')
        self.client.post(
            change_url,
            {
                'action': 'create_client',
                '_selected_action': [str(registration_request.pk)],
            },
        )
        user.refresh_from_db()

        self.assertIsNotNone(user.profile)

        client = m.Client.objects.get(id=user.profile.client_id)
        self.assertIsNotNone(client)
        self.assertEqual(client.name, 'Client Name')
