from djangorestframework_camel_case.util import camelize
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from core import fixtures as f, models as m, serializers as s
from core.annotations import annotate_job_proposal_pipeline, annotate_job_hired_count
from core.tests.generic_response_assertions import GenericResponseAssertionSet


class JobTests(APITestCase):
    """Tests related to the Job viewset."""

    def setUp(self):
        """Create Client during Job test class initialization."""
        super().setUp()
        self.client_obj = f.create_client()

        self.user = f.create_client_administrator(self.client_obj)
        self.login(self.user)
        self.assert_response = GenericResponseAssertionSet(self)

    def login(self, user=None):
        if user is None:
            user = self.user

        self.client.force_login(user)

    def test_get_jobs(self):
        """Should return a list of all Jobs."""
        job_1 = f.create_job(org=self.client_obj, title='Test Job 1')
        job_2 = f.create_job(org=self.client_obj, title='Test Job 2')

        jobs = (
            annotate_job_proposal_pipeline(m.Job.objects, self.user)
            .filter(id__in=[job_1.id, job_2.id])
            .order_by('-created_at')
        )

        url = reverse('job-list')
        response = self.client.get(f'{url}?show_pipeline=true')

        results = response.json()['results']
        expected_results = camelize(
            s.JobListSerializer(
                jobs, context={'request': response.wsgi_request}, many=True
            ).data
        )

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(expected_results[0], results[0])
        self.assertCountEqual(expected_results[1], results[1])
        self.assertEqual(results, expected_results)

    def test_get_agency_jobs(self):
        agency = f.create_agency()
        other_agency = f.create_agency()
        client = f.create_client(owner_agency=agency)

        user = f.create_agency_administrator(agency)

        job = f.create_job(agency, client)
        job_agency_contract = m.JobAgencyContract.objects.get(agency=agency, job=job,)
        job.assign_agency(other_agency)

        self.client.force_login(user)

        response_data = self.assert_response.ok('get', 'job-list').json()
        self.assertEqual(len(response_data['results'][0]['agencyContracts']), 1)
        self.assertEqual(
            response_data['results'][0]['agencyContracts'][0]['id'],
            job_agency_contract.id,
        )

    def test_get_jobs_without_jobs(self):
        """Should return an empty list if no Jobs created."""
        url = reverse('job-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'], [])

    def test_get_job(self):
        """Should return Job details."""
        job = f.create_job(org=self.client_obj)
        job_qs = annotate_job_hired_count(m.Job.objects.filter(id=job.id))
        job = job_qs[0]

        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        context = {'request': response.wsgi_request}
        self.assertEqual(
            response.json(), camelize(s.JobSerializer(job, context=context).data)
        )

    def check_get_job_recruiters_assigned(self, user, agency=None):
        self.login(user)
        hired_status = m.ProposalStatus.objects.get(
            group=m.ProposalStatusGroup.PENDING_START.key
        )
        job = f.create_job(org=self.client_obj)
        if agency is None:
            agency = f.create_agency()

        f.create_contract(agency, self.client_obj)
        job.assign_agency(agency)

        for i in range(2):
            job.assign_member(f.create_recruiter(agency))

        hired_count = 3
        for i in range(hired_count):
            f.create_proposal(
                stage='shortlist',
                job=job,
                status=hired_status,
                candidate=f.create_candidate(agency),
                created_by=agency.primary_contact,
            )

        for i in range(4):
            f.create_proposal(
                stage='longlist',
                job=job,
                candidate=f.create_candidate(agency),
                created_by=agency.primary_contact,
            )

        job_qs = annotate_job_hired_count(m.Job.objects.filter(id=job.id))
        job = job_qs[0]

        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        context = {'request': response.wsgi_request}

        expected = camelize(s.JobSerializer(job, context=context).data)
        response_data = response.json()

        self.assertEqual(hired_count, response_data['hiredCount'])

        self.assertEqual(expected, response_data)

        self.login()

    def test_get_job_recruiters_assigned_client(self):
        """Should return Job details."""
        self.check_get_job_recruiters_assigned(self.user)

    def test_get_job_recruiters_assigned_agency(self):
        agency = f.create_agency()
        self.check_get_job_recruiters_assigned(agency.primary_contact, agency)

    def test_get_job_without_job(self):
        """Should return 404 status code if not existing pk requested."""
        url = reverse('job-detail', kwargs={'pk': f.NOT_EXISTING_PK})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_get_public_job(self):
        """Should return Job details."""
        job = f.create_job(self.client_obj, public=True)

        url = reverse(
            'private-job-posting-public-detail', kwargs={'uuid': job.public_uuid}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            camelize(s.PrivateJobPostingPublicSerializer(job.private_posting).data),
        )

    def test_get_public_job_unpublished(self):
        """Should return 200."""
        job = f.create_job(self.client_obj, published=False, public=True)

        url = reverse(
            'private-job-posting-public-detail', kwargs={'uuid': job.public_uuid}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_create_public_link(self):
        """Job public_uuid shouldn't be None when link created."""
        job = f.create_job(self.client_obj)
        job_data = s.BaseJobSerializer(instance=job).data
        job_data['is_enabled'] = True
        url = reverse('private-job-posting-list')
        response = self.client.post(url, job_data, format='json')

        self.assertEqual(response.status_code, 201)
        job.refresh_from_db()
        self.assertIsNotNone(job.public_uuid)

    def test_create_public_link_already_created(self):
        """Resets the public job details but with same uuid."""
        job = f.create_job(self.client_obj, public=True)
        self.assertIsNotNone(job.public_uuid)
        old_uuid = job.public_uuid
        job_data = s.BaseJobSerializer(instance=job).data
        job_data['is_enabled'] = True
        url = reverse('private-job-posting-list')
        response = self.client.post(url, job_data, format='json')

        self.assertEqual(response.status_code, 400)
        job.refresh_from_db()
        self.assertEqual(job.public_uuid, old_uuid)

    def test_remove_public_link(self):
        """Job public_uuid should be None when link removed."""
        job = f.create_job(self.client_obj, public=True)

        url = reverse('private-job-posting-detail', kwargs={'job_id': job.id})
        response = self.client.patch(url, {'is_enabled': False}, format='json')

        self.assertEqual(response.status_code, 200)
        job.refresh_from_db()
        self.assertIsNone(job.public_uuid)

    def test_update_job_managers_empty(self):
        """Should remove all Job managers if empty list provided."""
        job = f.create_job(self.client_obj)
        job.assign_manager(f.create_hiring_manager(self.client_obj))

        data = {
            'function': m.Function.objects.first().pk,
            'title': 'New title',
            'responsibilities': 'New Responsibilities',
            'requirements': 'New Requirements',
            'work_location': 'New location',
            'required_languages': [],
            'questions': [],
            'agencies': [],
            'assignees': [],
            'managers': [],
            'recruiters': [],
            'country': 'jp',
            'interview_templates': [],
        }
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 200, msg=response.data)
        self.assertEqual(response.json()['managers'], [])

    def test_partial_update_keep_managers(self):
        """Should keep Job managers if no managers passed when patching."""
        job = f.create_job(self.client_obj)
        job.assign_manager(f.create_hiring_manager(self.client_obj))

        data = {'title': 'New title'}
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        job.refresh_from_db()
        self.assertTrue(len(job.managers) != 0)

    def test_partial_update_keep_assignees(self):
        """Should keep Job assignees if no assignees passed when patching."""
        job = f.create_job(self.client_obj)
        job.assign_member(f.create_recruiter(f.create_agency()))

        data = {'title': 'New title'}
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        job.refresh_from_db()
        self.assertTrue(job.assignees.all().exists())

    def test_get_jobs_with_superuser(self):
        """Should return 403 once Admin request jobs"""
        admin = f.create_admin()
        self.client.force_login(admin)

        url = reverse('job-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {'detail': 'You do not have permission to perform this action.'},
        )

    def test_import_longlist(self):
        """Should import a longlist from one job to another one"""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)

        job_1 = f.create_job(agency)
        job_2 = f.create_job(agency)

        candidate_1 = f.create_candidate(agency)
        candidate_2 = f.create_candidate(agency)
        candidate_3 = f.create_candidate(agency)

        f.create_proposal(job_1, candidate_1, agency_admin, stage='longlist')
        f.create_proposal(job_1, candidate_2, agency_admin, stage='longlist')
        f.create_proposal(job_1, candidate_3, agency_admin, stage='longlist')

        candidates = [candidate_1.pk, candidate_2.pk]

        self.client.force_login(agency_admin)
        self.assert_response.ok(
            'post',
            'job-import-longlist',
            job_2.pk,
            {'from_job': job_1.pk, 'candidates': candidates},
        )
        job_2_proposals = m.Proposal.longlist.filter(job=job_2)
        self.assertEqual(job_2_proposals.count(), 2)
        self.assertEqual(
            list(job_2_proposals.values_list('candidate', flat=True)), candidates
        )

    def test_import_longlist_unavailable_job(self):
        """Longlist can be imported only to available job"""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        client = f.create_client()

        job_1 = f.create_job(agency)
        client_job = f.create_job(client)

        candidate_1 = f.create_candidate(client)
        candidate_2 = f.create_candidate(client)
        candidate_3 = f.create_candidate(client)

        f.create_proposal(client_job, candidate_1, agency_admin, stage='longlist')
        f.create_proposal(client_job, candidate_2, agency_admin, stage='longlist')
        f.create_proposal(client_job, candidate_3, agency_admin, stage='longlist')

        candidates = [candidate_1.pk]

        self.client.force_login(agency_admin)
        self.assert_response.bad_request(
            'post',
            'job-import-longlist',
            job_1.pk,
            {'from_job': client_job.pk, 'candidates': candidates},
        )
