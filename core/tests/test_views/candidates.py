from datetime import date

from djangorestframework_camel_case.util import camelize, underscoreize
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from core import fixtures as f, models as m, serializers as s
from core.factories import (
    ClientFactory,
    UserFactory,
    ClientCandidateFactory,
    ClientJobFactory,
    ClientProposalFactory,
)


class CandidateTests(APITestCase):
    """Tests related to the Candidate viewset."""

    def setUp(self):
        """Create Agency during Candidate test class initialization."""
        super().setUp()
        self.user = f.create_user('test@test.com', 'password')
        self.agency = f.create_agency()
        self.client_org = f.create_client()
        self.agency.assign_recruiter(self.user)

        self.client.force_login(self.user)
        self.maxDiff = None

    def test_get_candidates_with_placement_approved_at(self):
        user = f.create_agency_administrator(self.agency)
        self.client.force_login(user)
        f.create_contract(self.agency, self.client_org)

        jobs = tuple(f.create_job(self.client_org, self.client_org) for i in range(3))
        for job in jobs:
            job.assign_agency(self.agency)

        candidate_no_placement = f.create_candidate(self.agency)
        for job in jobs:
            f.create_proposal(job, candidate_no_placement, user)

        candidate_no_approved = f.create_candidate(self.agency)
        f.create_fee(
            f.create_proposal(jobs[0], candidate_no_approved, user),
            user,
            self.agency,
            approved_at=date(2019, 2, 1),
        )
        f.create_fee(
            f.create_proposal(jobs[1], candidate_no_approved, user), user, self.agency,
        )
        f.create_proposal(jobs[2], candidate_no_approved, user)

        candidate_approved = f.create_candidate(self.agency)
        f.create_fee(
            f.create_proposal(jobs[2], candidate_approved, user),
            user,
            self.agency,
            approved_at=date(2019, 2, 3),
        )
        f.create_fee(
            f.create_proposal(jobs[0], candidate_approved, user),
            user,
            self.agency,
            approved_at=date(2019, 2, 2),
            status=m.FeeStatus.APPROVED.key,
        )
        f.create_fee(
            f.create_proposal(jobs[1], candidate_approved, user),
            user,
            self.agency,
            approved_at=date(2019, 2, 1),
            status=m.FeeStatus.APPROVED.key,
        )

        url = reverse('candidate-list')
        response = self.client.get(f'{url}?extra_fields=placement_approved_at')

        results = response.json()['results']

        self.assertEqual(len(results), 3)

        expected_value_pairs = [
            (candidate_no_placement, None),
            (candidate_no_approved, None),
            (candidate_approved, '2019-02-02'),
        ]

        for candidate, expected_value in expected_value_pairs:
            match = None
            for candidate_data in results:
                if candidate_data['id'] == candidate.id:
                    match = candidate_data
                    break
            self.assertIsNotNone(match, f'Candidate {candidate} not found')

            self.assertEqual(expected_value, match['placementApprovedAt'])

    def test_get_candidates_without_candidates(self):
        """Should return an empty list if no Candidates created."""
        url = reverse('candidate-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'], [])

    def test_get_candidate_without_candidate(self):
        """Should return 404 status code if not existing pk requested."""
        url = reverse('candidate-detail', kwargs={'pk': f.NOT_EXISTING_PK})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_archive_candidate(self):
        """Should archive candidate but not delete from db."""
        candidate = f.create_candidate(self.agency)
        aa = f.create_agency_administrator(self.agency)
        self.client.force_login(aa)

        url = reverse('candidate-archive-candidate', kwargs={'pk': candidate.pk})
        response = self.client.patch(url)
        candidate.refresh_from_db()

        self.assertEqual(response.status_code, 204)
        self.assertEqual(candidate.archived, True)

    def test_archive_candidate_not_owned_by_org(self):
        """Should returns 404 once user tries to delete candidate that is not
        owned by their organization"""
        candidate = f.create_candidate(self.agency)
        client = f.create_client()
        client_admin = f.create_client_administrator(client)
        self.client.force_login(client_admin)

        url = reverse('candidate-archive-candidate', kwargs={'pk': candidate.pk})
        response = self.client.patch(url)
        candidate.refresh_from_db()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(candidate.archived, False)

    def test_archive_proposed_candidate(self):
        """Archiving of proposed candidates is not allowed"""
        client = f.create_client()
        candidate = f.create_candidate(client)
        client_admin = f.create_client_administrator(client)
        job = f.create_job(client)
        f.create_proposal(job, candidate, client_admin)

        self.client.force_login(client_admin)

        url = reverse('candidate-archive-candidate', kwargs={'pk': candidate.pk})
        response = self.client.patch(url)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(underscoreize(response.json()), {"proposed_to_job": True})

    def test_restore_candidate(self):
        """Should restore archived candidate"""
        candidate = f.create_candidate(self.agency)
        candidate.archived = True
        candidate.save()

        recruiter = f.create_recruiter(self.agency)
        self.client.force_login(recruiter)

        url = reverse('candidate-restore-candidate', kwargs={'pk': candidate.pk})

        response = self.client.patch(url)

        candidate.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(candidate.archived, False)

    def test_delete_candidate(self):
        """Should delete archived candidate"""
        candidate = f.create_candidate(self.agency)
        candidate.archived = True
        candidate.save()

        recruiter = f.create_recruiter(self.agency)
        self.client.force_login(recruiter)

        url = f'/api/candidates/{candidate.pk}/'

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(m.Candidate.objects.filter(pk=candidate.pk).exists(), False)

    def test_delete_non_archived_candidate(self):
        """Only archived candidates can be deleted. Should return 400"""
        candidate = f.create_candidate(self.agency)

        recruiter = f.create_recruiter(self.agency)
        self.client.force_login(recruiter)

        url = f'/api/candidates/{candidate.pk}/'

        response = self.client.delete(url)

        candidate.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(candidate.archived, False)
        self.assertEqual(response.json(), {'detail': 'Candidate is not archived.'})

    def test_get_candidates_wuth_superuser(self):
        """Should return 403 once Admin request candidates"""
        admin = f.create_admin()
        self.client.force_login(admin)

        url = reverse('candidate-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {'detail': 'You do not have permission to perform this action.'},
        )

    def test_update_candidate_researcher_data_featured_agency(self):
        agency = f.create_agency()
        agency.enable_researcher_field_feature = True
        agency.save()
        agency_manager = f.create_agency_manager(agency)
        agency_admin = f.create_agency_administrator(agency)
        candidate = f.create_candidate(agency)

        data = {
            'email': 'test@localhost',
            'firstName': 'New',
            'last_name': 'Candidate',
            'resume': 'New resume',
            'owner': candidate.owner.pk,
            'name_collect': agency_manager.pk,
            'current_country': 'jp',
            'current_salary': 0,
        }

        self.client.force_login(agency_admin)
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.put(url, data, format='json')

        candidate.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(candidate.name_collect, agency_manager)
        self.assertIsNone(candidate.mobile_collect)

    def test_update_candidate_researcher_data_non_featured_org(self):
        client = f.create_client()
        client_admin = f.create_client_administrator(client)
        candidate = f.create_candidate(client)

        data = {
            'email': 'test@localhost',
            'firstName': 'New',
            'last_name': 'Candidate',
            'resume': 'New resume',
            'owner': candidate.owner.pk,
            'name_collect': client_admin.pk,
            'mobile_collect': client_admin.pk,
            'current_country': 'jp',
            'current_salary': 0,
        }

        self.client.force_login(client_admin)
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        for field in s.CANDIDATE_FEATURE_FIELDS['researcher_feature']:
            self.assertIsNone(getattr(candidate, field))

    def test_update_agency_only_candidate_fields_agency(self):
        """Agency may update Agency-only candidate fields"""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        candidate = f.create_candidate(agency)

        data = {
            'email': 'test@localhost',
            'firstName': 'New',
            'last_name': 'Candidate',
            'resume': 'New resume',
            'owner': candidate.owner.pk,
            'current_country': 'jp',
            'current_salary': 0,
            'lead_consultant': agency_admin.pk,
            'support_consultant': agency_admin.pk,
        }

        self.client.force_login(agency_admin)
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.patch(url, data, format='json')

        candidate.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(candidate.lead_consultant, agency_admin)
        self.assertEqual(candidate.support_consultant, agency_admin)
        self.assertEqual(candidate.skill_domain, None)


class ClientCandidateTests(APITestCase):
    def setUp(self):
        self.client_org = ClientFactory.create()
        self.user = UserFactory.create()
        self.client_org.assign_administrator(self.user)

        self.client.force_login(self.user)
        self.maxDiff = None

    def test_retrieve(self):
        """Should return Candidate details."""
        candidate = ClientCandidateFactory.create(client=self.client_org)

        response = self.client.get(
            reverse('candidate-detail', kwargs={'pk': candidate.pk})
        )

        candidate_json = s.RetrieveCandidateSerializer(
            candidate, context={'request': response.wsgi_request}
        ).data
        candidate_json['proposed_to_job'] = False
        candidate_json['placement_approved_at'] = None

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), camelize(candidate_json))

    def test_list(self):
        """Should return a list of all Candidates."""
        candidates = ClientCandidateFactory.create_batch(size=2, client=self.client_org)

        response = self.client.get(reverse('candidate-list'))

        candidates_json = s.CandidateSerializer(
            candidates, context={'request': response.wsgi_request}, many=True,
        ).data

        for candidate_data in candidates_json:
            candidate_data.update(placement_approved_at=None,)

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.json()['results'],
            [dict(item) for item in camelize(candidates_json)],
        )

    def test_retrieve_archived(self):
        """Should return archived candidate"""

        candidate = ClientCandidateFactory.create(client=self.client_org, archived=True)

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.get(url)

        candidate_json = s.RetrieveCandidateSerializer(
            candidate, context={'request': response.wsgi_request}
        ).data
        candidate_json['proposed_to_job'] = False
        candidate_json['placement_approved_at'] = None

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(underscoreize(response.json()), candidate_json)
        self.assertEqual(underscoreize(response.json()), candidate_json)


class CandidateFieldAccessTests(APITestCase):
    ADVANCED_FIELDS = {
        'email',
        'secondaryEmail',
        'phone',
        'secondaryPhone',
        'address',
        'taxEqualization',
        'salaryCurrency',
        'salary',
        'currentSalaryVariable',
        'currentSalaryCurrency',
        'currentSalary',
        'currentSalaryBreakdown',
        'totalAnnualSalary',
        'potentialLocations',
        'otherDesiredBenefits',
        'otherDesiredBenefitsOthersDetail',
        'expectationsDetails',
        'noticePeriod',
        'jobChangeUrgency',
        'source',
        'sourceDetails',
        'platform',
        'platformOtherDetails',
        'owner',
        'note',
    }

    def setUp(self):
        self.client_org = ClientFactory.create()
        self.user = UserFactory.create()
        self.client.force_login(self.user)
        self.candidate = ClientCandidateFactory.create(client=self.client_org)

    @staticmethod
    def get_url(pk=None):
        if not pk:
            return reverse('candidate-list')
        return reverse('candidate-detail', kwargs={'pk': pk})

    def send_get_request(self, pk=None):
        return self.client.get(self.get_url(pk), format='json').json()

    def assert_has_advanced_fields(self, data, has_fields=True):
        expected_set = set() if has_fields else self.ADVANCED_FIELDS
        self.assertSetEqual(self.ADVANCED_FIELDS - data.keys(), expected_set)

    def test_retrieve_recruiter(self):
        self.client_org.assign_internal_recruiter(self.user)

        data = self.send_get_request(self.candidate.pk)

        self.assert_has_advanced_fields(data)

    def test_list_recruiter(self):
        self.client_org.assign_internal_recruiter(self.user)

        data = self.send_get_request()

        self.assert_has_advanced_fields(data['results'][0])

    def test_retrieve_client_admin(self):
        self.client_org.assign_administrator(self.user)

        data = self.send_get_request(self.candidate.pk)

        self.assert_has_advanced_fields(data)

    def test_list_client_admin(self):
        self.client_org.assign_administrator(self.user)

        data = self.send_get_request()

        self.assert_has_advanced_fields(data['results'][0])

    def setup_standard_user(self):
        self.client_org.assign_standard_user(self.user)

        job = ClientJobFactory.create(client=self.client_org)
        job.assign_manager(self.user)

        ClientProposalFactory.create(job=job, candidate=self.candidate)

    def test_retrieve_standard_user(self):
        self.setup_standard_user()

        data = self.send_get_request(self.candidate.pk)

        self.assert_has_advanced_fields(data, False)

    def test_list_standard_user(self):
        self.setup_standard_user()

        data = self.send_get_request()

        self.assert_has_advanced_fields(data['results'][0], False)
