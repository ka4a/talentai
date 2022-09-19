from rest_framework.test import APITestCase

from core import fixtures as f, serializers as s
from core.factories import ClientInternalRecruiterFactory, ClientFactory
from core.tests.test_serializers import factory


class UpdateStaffTests(APITestCase):
    """Tests for the UpdateStaff serializer."""

    def setUp(self):
        super().setUp()
        self.client_org = ClientFactory.create()
        self.recruiter = ClientInternalRecruiterFactory.create(
            client=self.client_org
        ).user

        self.request = factory.put('/')
        self.request.user = self.recruiter

    def test_valid(self):

        data = {
            'first_name': 'Frank',
            'last_name': 'Herbert',
            'email': 'frank.herbert@example.com',
            'country': 'us',
            'locale': 'en',
        }

        serializer = s.UpdateStaffSerializer(
            self.recruiter, data=data, context={'request': self.request}
        )

        self.assertTrue(serializer.is_valid())

    def test_invalid(self):

        data = {
            'first_name': '',
            'last_name': '',
            'email': 'sashdash',
            'country': 'sasa',
            'locale': 'sasaj',
        }

        serializer = s.UpdateStaffSerializer(
            self.recruiter, data=data, context={'request': self.request}
        )

        self.assertFalse(serializer.is_valid())

        for field in data:
            self.assertTrue(field in serializer.errors, msg=field)
