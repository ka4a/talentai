"""Tests related to Admin user permissions."""
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from core import fixtures as f


class AdminTests(APITestCase):
    """Tests related to the Admin role."""

    def setUp(self):
        """Create the required objects during initialization."""
        super().setUp()
        self.client.force_login(f.create_admin())

    def test_get_candidates(self):
        """Admin can't get the Candidates list."""
        f.create_candidate(f.create_agency())

        url = reverse('candidate-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_get_candidate_own_agency(self):
        """Admin can't get the Candidate detail."""
        candidate = f.create_candidate(f.create_agency())

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)
