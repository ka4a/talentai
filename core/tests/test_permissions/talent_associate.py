"""Tests related to Talent Associate user permissions."""
import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from djangorestframework_camel_case.util import underscoreize
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from core import fixtures as f
from core import models as m
from core.tests.generic_response_assertions import GenericResponseAssertionSet


class TalentAssociateTests(APITestCase):
    """Tests related to the Talent Associate role."""

    def setUp(self):
        """Create required object during initialization."""
        super().setUp()
        self.user = f.create_user()
        self.client_obj = f.create_client(primary_contact=self.user)
        self.client_obj.assign_administrator(self.user)

        self.agency_admin = f.create_user('admin@agency.net', '123456')
        self.agency = f.create_agency(primary_contact=self.agency_admin)
        self.agency.assign_agency_administrator(self.agency_admin)
        self.assert_response = GenericResponseAssertionSet(self)

        self.recruiter = f.create_recruiter(self.agency)

        self.client.force_login(self.user)

    # Manager
    def test_get_managers(self):
        """Talent Associate can get a list of own Hiring Managers."""
        hm = f.create_hiring_manager(self.client_obj)
        f.create_hiring_manager(f.create_client())

        url = reverse('manager-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual({el['id'] for el in response.json()['results']}, {hm.pk})

    def test_assign_manager_own_job_and_manager(self):
        """Talent Associate can assign own Client Manager for the Job."""
        job = f.create_job(self.client_obj)
        hm = f.create_hiring_manager(self.client_obj)

        url = reverse('manager-assign')
        response = self.client.post(
            url, data={'job': job.pk, 'user': hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'User assigned as a Job Manager.'})

    def test_assign_manager_already_assigned(self):
        """Talent associate can't assign already assigned Manager."""
        job = f.create_job(self.client_obj)
        hm = f.create_hiring_manager(self.client_obj)
        job.assign_manager(hm)

        url = reverse('manager-assign')
        response = self.client.post(
            url, data={'job': job.pk, 'user': hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {'detail': 'User is already assigned as a Job Manager.'}
        )

    def test_assign_manager_other_client_job_and_manager(self):
        """Talent Associate can't assign Manager for other Client Job, User."""
        client = f.create_client()
        job = f.create_job(client)
        hm = f.create_hiring_manager(client)

        url = reverse('manager-assign')
        response = self.client.post(
            url, data={'job': job.pk, 'user': hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 403)

    def test_assign_manager_own_job_other_client_manager(self):
        """Talent Associate can't assign other Client Manager for the Job."""
        client = f.create_client()
        job = f.create_job(self.client_obj)
        hm = f.create_hiring_manager(client)

        url = reverse('manager-assign')
        response = self.client.post(
            url, data={'job': job.pk, 'user': hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 403)

    def test_assign_manager_other_client_job_own_manager(self):
        """Talent Associate can't assign Manager for other Client Job."""
        client = f.create_client()
        job = f.create_job(client)
        hm = f.create_hiring_manager(self.client_obj)

        url = reverse('manager-assign')
        response = self.client.post(
            url, data={'job': job.pk, 'user': hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 403)

    def test_remove_from_job_manager_own_job_and_manager(self):
        """Talent Associate can remove own Client User from Job Managers."""
        job = f.create_job(self.client_obj)
        hm = f.create_hiring_manager(self.client_obj)
        job.assign_manager(hm)

        url = reverse('manager-remove-from-job')
        response = self.client.post(
            url, data={'job': job.pk, 'user': hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'User removed from Job Managers.'})

    def test_remove_from_job_manager_not_assigned(self):
        """Talent Associate can't remove not a Job Manager from the Job."""
        job = f.create_job(self.client_obj)
        hm = f.create_hiring_manager(self.client_obj)

        url = reverse('manager-remove-from-job')
        response = self.client.post(
            url, data={'job': job.pk, 'user': hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {'detail': 'User is not a Manager of this Job.'}
        )

    def test_remove_from_job_manager_other_job_and_manager(self):
        """Talent Associate can't remove Manager from other Client's Job."""
        client = f.create_client()
        job = f.create_job(client)
        hm = f.create_hiring_manager(client)

        url = reverse('manager-remove-from-job')
        response = self.client.post(
            url, data={'job': job.pk, 'user': hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 403)

    def test_remove_from_job_manager_own_job_other_manager(self):
        """Talent Associate can't remove Manager from other Client's Job."""
        client = f.create_client()
        job = f.create_job(self.client_obj)
        hm = f.create_hiring_manager(client)

        url = reverse('manager-remove-from-job')
        response = self.client.post(
            url, data={'job': job.pk, 'user': hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 403)

    def test_remove_from_job_manager_other_job_own_manager(self):
        """Talent Associate can't remove other Client's User from Managers."""
        client = f.create_client()
        job = f.create_job(client)
        hm = f.create_hiring_manager(self.client_obj)

        url = reverse('manager-remove-from-job')
        response = self.client.post(
            url, data={'job': job.pk, 'user': hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 403)

    def test_invite_manager(self):
        """Talent Associate can invite Hiring Manager."""
        url = reverse('manager-invite')
        response = self.client.post(
            url,
            data={
                'first_name': 'Test',
                'last_name': 'Name',
                'email': 'testname@localhost',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'Invite link sent.'})

    # Client
    def test_get_clients(self):
        """Talent Associate can get the list of Clients."""
        f.create_client()

        url = reverse('client-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {el['id'] for el in response.json()['results']}, {self.client_obj.pk}
        )

    def test_create_client(self):
        """Talent Associate can't create a Client."""
        data = {'name': 'Test client'}
        url = reverse('client-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_get_client_own(self):
        """Talent Associate can get his own Client details."""
        url = reverse('client-detail', kwargs={'pk': self.client_obj.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.client_obj.pk)

    def test_get_client_other(self):
        """Talent Associate can't get other Client details."""
        client = f.create_client()

        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_update_client_own(self):
        """Talent Associate can update his own Client."""
        data = {'name': 'New name'}
        url = reverse('client-detail', kwargs={'pk': self.client_obj.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.client_obj.pk)

    def test_update_client_other(self):
        """Talent Associate can't update other Client."""
        client = f.create_client(name='Test client')

        data = {'name': 'New name'}
        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_partial_update_client_own(self):
        """Talent Associate can partially update his own Client."""
        data = {'name': 'New name'}
        url = reverse('client-detail', kwargs={'pk': self.client_obj.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.client_obj.pk)

    def test_partial_update_client_other(self):
        """Talent Associate can't partially update other Client."""
        client = f.create_client(name='Test client')

        data = {'name': 'New name'}
        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_delete_client_own(self):
        """Talent Associate can't delete his own Client."""
        url = reverse('client-detail', kwargs={'pk': self.client_obj.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_delete_client_other(self):
        """Talent Associate can't delete other Client."""
        client = f.create_client(name='Test client')

        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    # Client registration request
    def test_create_client_registration_request(self):
        """Talent Associate can create a Client registration request."""
        data = {
            'name': 'Test client',
            'user': {
                'firstName': 'John',
                'lastName': 'Smith',
                'email': 'john.smith@test.com',
                'password': '7*&^&zkd',
            },
            'termsOfService': True,
        }
        url = reverse('clientregistrationrequest-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)

    # Agency registration request
    def test_create_agency_registration_request(self):
        """Talent Associate can create an Agency registration request."""
        data = {
            'name': 'Test agency',
            'user': {
                'firstName': 'John',
                'lastName': 'Smith',
                'email': 'john.smith@test.com',
                'password': '7*&^&zkd',
                'country': 'jp',
            },
            'termsOfService': True,
        }
        url = reverse('agencyregistrationrequest-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)

    # Job
    def test_get_jobs(self):
        """Talent Associate can get Jobs only from his own Client."""
        job = f.create_job(self.client_obj)
        f.create_job(f.create_agency())

        contracted_agency = f.create_agency()
        f.create_contract(contracted_agency, self.client_obj)
        f.create_job(contracted_agency)

        f.create_job(f.create_client())

        results = self.assert_response.ok('get', 'job-list').json()['results']

        self.assertEqual({el['id'] for el in results}, {job.pk})

    def test_create_job(self):
        """Talent Associate can create a Job."""
        owner = f.create_hiring_manager(self.client_obj)

        data = {
            'function': m.Function.objects.first().pk,
            'title': 'Test job',
            'responsibilities': 'Test responsibilities',
            'work_location': 'Test location',
            'required_languages': [],
            'questions': [],
            'agencies': [],
            'managers': [],
            'country': 'jp',
            'interview_templates': [],
        }
        url = reverse('job-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)
        response_data = underscoreize(response.json())
        data['interview_templates'] = [
            {
                'interview_type': 'general',
                'description': '',
                'id': 1,
                'interviewer': None,
                'order': 10,
            },
            {
                'interview_type': 'technical_fit',
                'description': '',
                'id': 2,
                'interviewer': None,
                'order': 20,
            },
            {
                'interview_type': 'cultural_fit',
                'description': '',
                'id': 3,
                'interviewer': None,
                'order': 30,
            },
        ]
        self.assertEqual(
            len(data.pop('interview_templates')),
            len(response_data.pop('interview_templates')),
        )
        for key in data:
            self.assertEqual(data[key], response_data[key], msg=key)

    def test_get_public_job_own_client(self):
        """Talent Associate User can get public Job details for own Client."""
        job = f.create_job(self.client_obj, public=True)

        url = reverse(
            'private-job-posting-public-detail', kwargs={'uuid': job.public_uuid}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_public_job_other_client(self):
        """Talent Associate User can get public Job details other Client."""
        job = f.create_job(f.create_client(), public=True)

        url = reverse(
            'private-job-posting-public-detail', kwargs={'uuid': job.public_uuid}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_public_job_agency(self):
        """Talent Associate User can get public Job details Agency."""
        job = f.create_job(f.create_agency(), public=True)

        url = reverse(
            'private-job-posting-public-detail', kwargs={'uuid': job.public_uuid}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_job_own_client(self):
        """Talent Associate can get his own Job details."""
        job = f.create_job(self.client_obj)

        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], job.pk)

    def test_get_job_unpublished(self):
        """Talent Associate can get unpublished Job."""
        job = f.create_job(self.client_obj, published=False)

        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], job.pk)

    def test_get_job_other_client(self):
        """Talent Associate can't get other Client's Job details."""
        job = f.create_job(f.create_client())

        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    @staticmethod
    def get_job_put_request_payload(job, manager_ids=None, owner_id=None):
        return {
            'function': m.Function.objects.first().pk,
            'title': 'New title',
            'responsibilities': 'New responsibilities',
            'work_location': 'New location',
            'required_languages': [],
            'questions': [],
            'agencies': [],
            'managers': manager_ids if manager_ids else [],
            'owner': owner_id if owner_id else job.owner.id,
            'country': 'jp',
            'interview_templates': [],
        }

    def test_update_job_own_client(self):
        """Talent Associate can update own Job."""
        job = f.create_job(self.client_obj)

        data = self.get_job_put_request_payload(job)

        response = self.assert_response.ok('put', 'job-detail', job.pk, data)

        self.assertTrue(data.items() <= underscoreize(response.json()).items())

    def test_update_job_other_client(self):
        """Talent Associate can't update other Client's Job."""
        job = f.create_job(f.create_client())

        data = {
            'title': 'New title',
            'responsibilities': 'New responsibilities',
            'work_location': 'New location',
            'required_languages': [],
            'questions': [],
            'agencies': [],
            'assignees': [],
            'managers': [],
        }
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.put(url, data, format='json')
        data = self.get_job_put_request_payload(job)
        self.assert_response.not_found('put', 'job-detail', job.pk, data)

    def test_update_job_agency(self):
        """Talent Associate can't update Agency's Job."""
        job = f.create_job(f.create_agency())

        data = self.get_job_put_request_payload(job)
        self.assert_response.not_found('put', 'job-detail', job.pk, data)

    def test_update_job_managers(self):
        """Talent Associate can update Job managers."""
        job = f.create_job(self.client_obj)

        manager = f.create_hiring_manager(self.client_obj)
        managers_to_assign = [manager.pk]

        data = self.get_job_put_request_payload(job, managers_to_assign, manager.pk)

        assigned_managers = self.assert_response.ok(
            'put', 'job-detail', job.pk, data
        ).json()['managers']

        self.assertEqual(assigned_managers, managers_to_assign)

    def test_partial_update_job_own_client(self):
        """Talent Associate can partially update own Job."""
        job = f.create_job(self.client_obj)

        data = {'title': 'New title'}
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data.items() <= response.json().items())

    def test_partial_update_job_other_client(self):
        """Talent Associate can't partially update other Client's Job."""
        job = f.create_job(f.create_client())

        data = {'title': 'New title'}
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_partial_update_job_managers(self):
        """Talent Associate can patch Job managers."""
        job = f.create_job(self.client_obj)

        manager = f.create_hiring_manager(self.client_obj)

        data = {'managers': [manager.pk]}
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['managers'], [manager.pk])

    def test_delete_job_own_client(self):
        """Talent Associate can't delete own Job."""
        job = f.create_job(self.client_obj)

        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, 403)

    def test_delete_job_other_client(self):
        """Talent Associate can't delete other Client's Job."""
        job = f.create_job(f.create_client())

        data = {'title': 'New title'}
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_create_public_link_own_client(self):
        """Talent Associate can create Job public link for own Client."""
        job = f.create_job(self.client_obj)

        url = reverse('private-job-posting-list', kwargs={'job_id': job.pk})
        response = self.client.post(url, {'is_enabled': True}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'Job public link created.'})

    def test_create_public_link_other_client(self):
        """Talent Associate can't create Job public link for other Client."""
        job = f.create_job(f.create_client())

        url = reverse('private-job-posting-list', kwargs={'job_id': job.pk})
        response = self.client.post(url, {'is_enabled': True}, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_remove_public_link_own_client(self):
        """Talent Associate can remove Job public link for own Client."""
        job = f.create_job(self.client_obj, public=True)

        url = reverse('private-job-posting-detail', kwargs={'job_id': job.pk})
        response = self.client.patch(url, {'is_enabled': False}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'PrivateJobPosting disabled.'})

    def test_remove_public_link_other_client(self):
        """Talent Associate can't remove Job public link for other Client."""
        job = f.create_job(f.create_client(), public=True)

        url = reverse('private-job-posting-detail', kwargs={'job_id': job.pk})
        response = self.client.patch(url, {'is_enabled': False}, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_assign_member_agency_job(self):
        job = f.create_job(f.create_agency())
        data = {'assignee': self.user.pk}

        self.assert_response.not_found('patch', 'job-assign-member', job.pk, data)

    def test_withdraw_member_agency_job(self):
        agency = f.create_agency()
        job = f.create_job(agency)

        assignee = f.create_recruiter(agency)
        job.assign_member(assignee)

        data = {'assignee': assignee.pk}

        self.assert_response.not_found('patch', 'job-withdraw-member', job.pk, data)

    # Job file
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_create_job_file_own_job(self):
        """Talent Associate can create Job file for own Job."""
        job = f.create_job(self.client_obj)

        url = reverse('job-file-list')
        response = self.client.post(
            url,
            data={
                'file': SimpleUploadedFile('file.txt', b'i am not empty anymore'),
                'job': job.pk,
            },
        )

        self.assertEqual(response.status_code, 201)

    def test_create_job_file_other_job(self):
        """Talent Associate can't create Job file for other Client's Job."""
        job = f.create_job(f.create_client())

        url = reverse('job-file-list')
        response = self.client.post(
            url,
            data={
                'file': SimpleUploadedFile('file.txt', b'i am not empty anymore'),
                'job': job.pk,
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_get_job_file_own_job(self):
        """Talent Associate can get Job file for own Job."""
        job = f.create_job(self.client_obj)

        job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=job
        )

        url = reverse('job-file-detail', kwargs={'pk': job_file.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_get_job_file_other_job(self):
        """Talent Associate can't get Job file of other Client's Job."""
        job = f.create_job(f.create_client())

        job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=job
        )

        url = reverse('job-file-detail', kwargs={'pk': job_file.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_delete_job_file_own_job(self):
        """Talent Associate can delete Job file of own Job."""
        job = f.create_job(self.client_obj)

        job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=job
        )

        url = reverse('job-file-detail', kwargs={'pk': job_file.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_delete_job_file_other_job(self):
        """Talent Associate can't delete Job file of other Client's Job."""
        job = f.create_job(f.create_client())

        job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=job
        )

        url = reverse('job-file-detail', kwargs={'pk': job_file.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    # Agency
    def test_get_agencies(self):
        """Talent Associate can get the list of Agencies."""
        agency_1 = self.agency
        agency_2 = f.create_agency()
        f.create_contract(agency_2, self.client_obj)

        url = reverse('agency-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {el['id'] for el in response.json()['results']}, {agency_1.pk, agency_2.pk}
        )

    def test_create_agency(self):
        """Talent Associate can't create an Agency."""
        data = {'name': 'Test agency'}
        url = reverse('agency-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_get_agency_with_contract(self):
        """Talent Associate can get Agency with Contract details."""
        f.create_contract(self.agency, self.client_obj)

        url = reverse('agency-detail', kwargs={'pk': self.agency.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.agency.pk)

    def test_get_agency_without_contract(self):
        """Talent Associate can get Agency without Contract details."""
        url = reverse('agency-detail', kwargs={'pk': self.agency.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.agency.pk)

    def test_update_agency_with_contract(self):
        """Talent Associate can't update Agency with Contract."""

        f.create_contract(self.agency, self.client_obj)

        data = {'name': 'New agency'}
        url = reverse('agency-detail', kwargs={'pk': self.agency.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_update_agency_without_contract(self):
        """Talent Associate can't update Agency without Contract."""
        data = {'name': 'New agency'}
        url = reverse('agency-detail', kwargs={'pk': self.agency.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_partial_update_agency_with_contract(self):
        """Talent Associate can't patch own Agency with Contract."""

        f.create_contract(self.agency, self.client_obj)

        data = {'name': 'New agency'}
        url = reverse('agency-detail', kwargs={'pk': self.agency.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_partial_update_agency_without_contract(self):
        """Talent Associate can't patch Agency without Contract."""
        data = {'name': 'New agency'}
        url = reverse('agency-detail', kwargs={'pk': self.agency.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_delete_agency_with_contract(self):
        """Talent Associate can't delete Agency with Contract."""

        f.create_contract(self.agency, self.client_obj)

        url = reverse('agency-detail', kwargs={'pk': self.agency.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_delete_agency_without_contract(self):
        """Talent Associate can't delete Agency without Contract."""
        url = reverse('agency-detail', kwargs={'pk': self.agency.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    # Staff
    def test_get_agency_staff_list(self):
        """Talent Associate can't get Staff."""
        url = reverse('staff-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_agency_staff(self):
        """Talent Associate can't access the Staff detail."""
        url = reverse('staff-detail', kwargs={'pk': self.recruiter.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_update_agency_staff(self):
        """Talent Associate can't update the Staff."""
        data = {'is_active': False, 'teams': []}
        url = reverse('staff-detail', kwargs={'pk': self.recruiter.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 404)

    def test_patch_agency_staff(self):
        """Talent Associate can't patch the Staff."""
        data = {'is_active': False, 'teams': []}
        url = reverse('staff-detail', kwargs={'pk': self.recruiter.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)

    # Team
    def test_get_agency_teams(self):
        """Talent Associate can't get the list of Teams."""
        f.create_team(self.agency)

        url = reverse('team-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    # Candidate
    def test_get_candidates(self):
        """Talent Associate can get only Candidates linked to his Client."""
        candidate = f.create_candidate(self.client_obj)
        f.create_candidate(self.agency)
        f.create_proposal(
            f.create_job(self.client_obj),
            f.create_candidate(self.agency),
            self.recruiter,
        )
        f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(self.agency),
            self.recruiter,
        )

        url = reverse('candidate-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual({i['id'] for i in response.json()['results']}, {candidate.pk})

    def test_create_candidate(self):
        """Talent Associate can create a Candidate."""
        data = {
            'email': 'testcandidate@localhost',
            'first_name': 'Test',
            'last_name': 'Candidate',
            'summary': 'Test resume',
            'files': [],
            'owner': self.user.pk,
            'current_salary': 0,
            'current_country': 'jp',
        }
        url = reverse('candidate-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)

    def test_get_candidate_own(self):
        """Talent Associate can get own Candidate."""
        candidate = f.create_candidate(self.client_obj)

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], candidate.pk)

    def test_get_candidate_linked_via_proposal(self):
        """Talent Associate can get Candidate linked via Proposal."""
        candidate = f.create_candidate(self.agency)
        f.create_proposal(f.create_job(self.client_obj), candidate, self.recruiter)

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_get_candidate_not_linked_via_proposal(self):
        """Talent Associate can't get Candidate not linked via Porposal."""
        candidate = f.create_candidate(self.agency)

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_get_candidate_linked_to_other_client(self):
        """Talent Associate can't get Candidate linked to other Client."""
        candidate = f.create_candidate(self.agency)
        f.create_proposal(f.create_job(f.create_client()), candidate, self.recruiter)

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_update_candidate_own(self):
        """Talent Associate can update own Candidate."""
        candidate = f.create_candidate(self.client_obj)

        data = {
            'email': 'test@localhost',
            'firstName': 'New',
            'last_name': 'Candidate',
            'resume': 'New resume',
            'owner': self.user.pk,
            'current_salary': 0,
            'current_country': 'jp',
        }
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 200)

    def test_update_candidate_linked_via_proposal(self):
        """Talent Associate can't update the Candidate with Proposal."""
        candidate = f.create_candidate(self.agency)
        f.create_proposal(f.create_job(self.client_obj), candidate, self.recruiter)

        data = {'name': 'New name', 'resume': 'New resume'}
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_update_candidate_not_linked_via_proposal(self):
        """Talent Associate can't update the Candidate without Proposal."""
        candidate = f.create_candidate(self.agency)

        data = {'name': 'New name', 'resume': 'New resume'}
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_update_candidate_linked_to_other_client(self):
        """Talent Associate can't update the Candidate other Client."""
        candidate = f.create_candidate(self.agency)
        f.create_proposal(f.create_job(f.create_client()), candidate, self.recruiter)

        data = {'name': 'New name', 'resume': 'New resume'}
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_partial_update_candidate_own(self):
        """Talent Associate can patch own Candidate."""
        candidate = f.create_candidate(self.client_obj)

        data = {'name': 'New name'}
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)

    def test_partial_update_candidate_linked_via_proposal(self):
        """Talent Associate can't patch the Candidate with Proposal."""
        candidate = f.create_candidate(self.agency)
        f.create_proposal(f.create_job(self.client_obj), candidate, self.recruiter)

        data = {'name': 'New name'}
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_partial_update_candidate_not_linked_via_proposal(self):
        """Talent Associate can't patch the Candidate without Proposal."""
        candidate = f.create_candidate(self.agency)

        data = {'name': 'New name'}
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_partial_update_candidate_linked_to_other_client(self):
        """Talent Associate can't patch the Candidate other Client."""
        candidate = f.create_candidate(self.agency)
        f.create_proposal(f.create_job(f.create_client()), candidate, self.recruiter)

        data = {'name': 'New name'}
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_delete_candidate_own(self):
        """Talent Associate can delete own Candidate."""
        candidate = f.create_candidate(self.client_obj)
        candidate.archived = True
        candidate.save()

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)

    def test_delete_candidate_linked_via_proposal(self):
        """Talent Associate can't delete the Candidate with Proposal."""
        candidate = f.create_candidate(self.agency)
        f.create_proposal(f.create_job(self.client_obj), candidate, self.recruiter)

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_delete_candidate_not_linked_via_proposal(self):
        """Talent Associate can't delete the Candidate without Proposal."""
        candidate = f.create_candidate(self.agency)

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_delete_candidate_linked_to_other_client(self):
        """Talent Associate can't delete the Candidate other Client."""
        candidate = f.create_candidate(self.agency)
        f.create_proposal(f.create_job(f.create_client()), candidate, self.recruiter)

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    # CandidateFile
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_upload_file(self):
        """Talent Associate can't upload Candidate file for other Candidate."""
        candidate = f.create_candidate(self.agency)

        url = reverse(
            'candidate-file-upload', kwargs={'pk': candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.post(url, data={'file': ''})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_get_file(self):
        """Talent Associate can't upload Candidate file for other Candidate."""
        candidate = f.create_candidate(self.agency)
        candidate.cv = SimpleUploadedFile('file.txt', b'')
        candidate.save()

        url = reverse(
            'candidate-file-get', kwargs={'pk': candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_delete_file(self):
        """Talent Associate can't delete Candidate file for other Candidate."""
        candidate = f.create_candidate(self.agency)
        candidate.cv = SimpleUploadedFile('file.txt', b'')
        candidate.save()

        url = reverse(
            'candidate-file-delete', kwargs={'pk': candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    # Zoho
    @patch('core.views.views.get_zoho_candidate')
    def test_get_candidate(self, get_zoho_candidate_mock):
        """Talent Associate can import Zoho Candidate."""
        get_zoho_candidate_mock.return_value = f.ZOHO_CANDIDATE_DATA

        url = reverse('zoho-get-candidate')

        zoho_candidate_url = (
            'https://recruit.zoho.com/recruit/EntityInfo.do?' 'module=Candidates&id=123'
        )

        response = self.client.post(url, {'url': zoho_candidate_url}, format='json')
        self.assertEqual(response.status_code, 200)

    # Proposal
    def test_get_proposals(self):
        """Talent Associate can get only Proposals linked to his Client."""
        proposal = f.create_proposal(
            f.create_job(self.client_obj),
            f.create_candidate(self.agency),
            self.recruiter,
        )
        f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(self.agency),
            self.recruiter,
        )

        url = reverse('proposal-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual({i['id'] for i in response.json()['results']}, {proposal.pk})

    def test_create_proposal_own_candidate_assigned_job(self):
        """Talent Associate can't create a Proposal."""
        job = f.create_job(self.client_obj)
        candidate = f.create_candidate(self.agency)

        data = {'job': job.pk, 'candidate': candidate.pk}
        url = reverse('proposal-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_get_proposal_own_job(self):
        """Talent Associate can get Proposal for own Job."""
        proposal = f.create_proposal(
            f.create_job(self.client_obj),
            f.create_candidate(self.agency),
            self.recruiter,
        )

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], proposal.pk)

    def test_get_proposal_other_client_job(self):
        """Talent Associate can't get Proposal for other Client's Job."""
        proposal = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(self.agency),
            self.recruiter,
        )

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_update_proposal_agency_job(self):
        """Talent Associate can update Proposal for own Job."""
        job = f.create_job(self.agency)
        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, self.recruiter)

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        self.assert_response.not_found('patch', 'proposal-detail', proposal.pk, data)

    def test_update_proposal_own_job(self):
        """Talent Associate can update Proposal for own Job."""
        job = f.create_job(self.client_obj)
        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, self.recruiter)

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data.items() <= response.json().items())

    def test_update_proposal_other_client_job(self):
        """Talent Associate can't update Proposal for other Client's Job."""
        job = f.create_job(f.create_client())
        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, self.recruiter)

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_patch_proposal_own_job(self):
        """Talent Associate can patch Proposal for own Job."""
        proposal = f.create_proposal(
            f.create_job(self.client_obj),
            f.create_candidate(self.agency),
            self.recruiter,
        )

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data.items() <= response.json().items())

    def test_patch_proposal_other_client_job(self):
        """Talent Associate can't patch Proposal for other Client's Job."""
        proposal = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(self.agency),
            self.recruiter,
        )

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_delete_proposal_own_job(self):
        """Talent Associate can't delete Proposal for own Job."""
        proposal = f.create_proposal(
            f.create_job(self.client_obj),
            f.create_candidate(self.agency),
            self.recruiter,
        )

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_delete_proposal_other_client_job(self):
        """Talent Associate can't delete Proposal for other Client's Job."""
        proposal = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(self.agency),
            self.recruiter,
        )

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    # ProposalComment
    def test_get_proposal_comments(self):
        """Talent Associate can get the list of Proposal comments."""
        proposal = f.create_proposal(
            f.create_job(self.client_obj),
            f.create_candidate(self.agency),
            self.recruiter,
        )
        comment = f.create_proposal_comment(self.user, proposal)

        url = reverse('proposalcomment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual({i['id'] for i in response.json()['results']}, {comment.pk})

    def test_create_proposal_comment_own_proposal(self):
        """Talent Associate can create Proposal Comment for own Proposal."""
        proposal = f.create_proposal(
            f.create_job(self.client_obj),
            f.create_candidate(self.agency),
            self.recruiter,
        )
        data = {'proposal': proposal.pk, 'text': 'Test comment'}

        url = reverse('proposalcomment-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)

    def test_create_proposal_comment_own_client_proposal(self):
        """Talent Associate can create Comment for Proposal from own Client."""
        proposal = f.create_proposal(
            f.create_job(self.client_obj),
            f.create_candidate(self.agency),
            f.create_client_administrator(self.client_obj),
        )
        data = {'proposal': proposal.pk, 'text': 'Test comment'}

        url = reverse('proposalcomment-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)

    def test_create_proposal_comment_other_proposal(self):
        """Talent Associate can't create Comment for other Clients Proposal."""
        proposal_other = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(self.agency),
            self.recruiter,
        )
        data = {'proposal': proposal_other.pk, 'text': 'Test comment'}

        url = reverse('proposalcomment-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 400)

    def test_get_proposal_comment_own(self):
        """Talent Associate can get own Proposal Comment details."""
        proposal = f.create_proposal(
            f.create_job(self.client_obj),
            f.create_candidate(self.agency),
            self.recruiter,
        )
        comment = f.create_proposal_comment(self.user, proposal)

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], comment.pk)

    def test_get_proposal_comment_user_own_client(self):
        """Talent Associate can get own Client User's Proposal Comment."""
        proposal = f.create_proposal(
            f.create_job(self.client_obj),
            f.create_candidate(self.agency),
            self.recruiter,
        )
        hm = f.create_hiring_manager(self.client_obj)
        comment = f.create_proposal_comment(hm, proposal)

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], comment.pk)

    def test_get_proposal_comment_other_client(self):
        """Talent Associate can't get Proposal Comment of other Client."""
        client_other = f.create_client()
        client_admin_other = f.create_client_administrator(client_other)

        proposal = f.create_proposal(
            f.create_job(client_other), f.create_candidate(self.agency), self.recruiter,
        )
        comment = f.create_proposal_comment(client_admin_other, proposal)

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_get_proposal_comment_other_client_public(self):
        """Talent Associate can't get public Comment of other Client."""
        client_other = f.create_client()
        client_admin_other = f.create_client_administrator(client_other)

        proposal = f.create_proposal(
            f.create_job(client_other), f.create_candidate(self.agency), self.recruiter,
        )
        comment = f.create_proposal_comment(client_admin_other, proposal, public=True)

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_get_proposal_comment_agency(self):
        """Talent Associate can't get Agency's Proposal Comment."""
        proposal = f.create_proposal(
            f.create_job(self.client_obj),
            f.create_candidate(self.agency),
            self.recruiter,
        )
        comment = f.create_proposal_comment(self.recruiter, proposal)

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_get_proposal_comment_agency_public(self):
        """Talent Associate can get Agency's public Proposal Comment."""
        proposal = f.create_proposal(
            f.create_job(self.client_obj),
            f.create_candidate(self.agency),
            self.recruiter,
        )
        comment = f.create_proposal_comment(self.recruiter, proposal, public=True)

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], comment.pk)

    # Notification
    def test_mark_all_as_read(self):
        """Talent Associate User can mark all Notifications as read."""
        url = reverse('notification-mark-all-as-read')
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    def test_mark_as_read(self):
        """Talent Associate User can mark own Notification as read."""
        v = m.NotificationTypeEnum.CANDIDATE_SHORTLISTED_FOR_JOB
        notification = f.create_notification(self.user, verb=v, actor=self.agency)

        url = reverse('notification-mark-as-read', kwargs={'pk': notification.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    def test_mark_as_read_other_user(self):
        """Talent Associate User can't mark other User Notification as read."""
        v = m.NotificationTypeEnum.CANDIDATE_SHORTLISTED_FOR_JOB
        notification = f.create_notification(f.create_user(), verb=v, actor=self.agency)

        url = reverse('notification-mark-as-read', kwargs={'pk': notification.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    # Contract
    def test_get_conracts(self):
        """Talent Associate can get Contracts linked to his own Client only."""

        contract = f.create_contract(self.agency, self.client_obj)
        f.create_contract(self.agency, f.create_client())

        url = reverse('contract-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual({el['id'] for el in response.json()['results']}, {contract.pk})

    def test_create_contract(self):
        """Talent Associate can create a Contract."""
        data = {'agency': self.agency.pk}
        url = reverse('contract-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(data.items() <= response.json().items())

    def test_get_contract_own_client(self):
        """Talent Associate can get Contract of his own Client."""
        contract = f.create_contract(self.agency, self.client_obj)

        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], contract.pk)

    def test_get_contract_other_client(self):
        """Talent Associate can't get Contract of the other Client."""
        contract = f.create_contract(self.agency, f.create_client())

        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_update_contract_own_client(self):
        """Talent Associate can update the Contract of his own Client."""
        contract = f.create_contract(self.agency, self.client_obj)

        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        data = {
            'is_client_signed': True,
            'status': m.ContractStatus.PENDING.key,
        }
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], contract.id)

    def test_update_contract_other_client(self):
        """Talent Associate can't update the Contract of the other Client."""
        contract = f.create_contract(self.agency, f.create_client())

        data = {'agency': self.agency.pk}
        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_partial_update_contract_own_client(self):
        """Talent Associate can patch the Contract of his own Client."""
        contract = f.create_contract(self.agency, self.client_obj)

        data = {
            'is_client_signed': True,
            'status': m.ContractStatus.PENDING.key,
        }
        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], contract.id)

    def test_partial_update_contract_other_client(self):
        """Talent Associate can't patch the Contract of the other Client."""

        contract = f.create_contract(self.agency, f.create_client())

        data = {'agency': self.agency.pk}
        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_delete_contract_own_client(self):
        """Talent Associate can delete the Contract of his own Client."""
        contract = f.create_contract(self.agency, self.client_obj)

        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)

    def test_delete_contract_other_client(self):
        """Talent Associate can't delete the Contract of the other Client."""
        contract = f.create_contract(self.agency, f.create_client())

        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    # User
    def test_get_user(self):
        """Talent Associate can get his own User detail."""
        url = reverse('user-read-current')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.user.pk)

    def test_change_password(self):
        """Talent Associate can update his own User password."""
        data = {
            'old_password': f.DEFAULT_USER['password'],
            'new_password1': 'New password',
            'new_password2': 'New password',
        }
        url = reverse('change-password')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'Password changed.'})

    def test_confirm_password_reset(self):
        """TA can confirm password reset with the correct token."""
        url = reverse('confirm-password-reset')
        data = {
            'uidb64': f.get_user_uidb64(self.user),
            'token': f.get_user_token(self.user),
            'new_password1': 'New password',
            'new_password2': 'New password',
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'Password reset successfully.'})

    def test_login(self):
        """Talent Associate can log into another account."""
        other_user = f.create_client_administrator(
            self.client_obj, 'otheruser@test.com', 'password'
        )

        data = {'email': 'otheruser@test.com', 'password': 'password'}
        url = reverse('user-login')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(other_user.pk, response.data['id'])

    def test_logout(self):
        """Talent Associate can log out."""
        url = reverse('user-logout')
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'Logged out.'})

    def test_reset_password(self):
        """Talent Associate can request a password reset."""
        data = {'email': self.user.email}
        url = reverse('reset-password')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'Password reset email sent.'})

    def test_update_settings(self):
        """Talent Associate can update hist own User settings."""
        data = {'email': 'newemail@test.com'}
        url = reverse('user-update-settings')
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data.items() <= response.json().items())

    def test_upload_photo(self):
        """Can save user photo."""
        image_data = f.get_jpeg_image_content()
        response = self.client.post(
            reverse('user-upload-photo'),
            {'file': SimpleUploadedFile('img.jpg', image_data)},
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_photo(self):
        """Can delete user photo."""
        response = self.client.post(reverse('user-delete-photo'))
        self.assertEqual(response.status_code, 200)

    def test_check_linkedin_candidate_exists(self):
        """Talent Associate can check candidate exists."""
        url = reverse('ext-api-check-linkedin-candidate-exists')
        data = {'linkedinUrl': 'https://www.linkedin.com/in/someslug/'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

    def test_add_linkedin_candidate(self):
        """"Talent Associate can add Candidate."""
        url = reverse('ext-api-add-linkedin-candidate')

        data = {
            'name': 'Some Candidate',
            'contactInfo': {'linkedIn': 'https://www.linkedin.com/in/someslug/'},
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

    def test_proposal_move_to_job(self):
        """Should move proposal to other job."""
        job = f.create_job(self.client_obj)
        job.assign_agency(self.agency)

        proposal = f.create_proposal(
            job, f.create_candidate(self.agency), self.recruiter
        )

        another_job = f.create_job(self.client_obj)
        another_job.assign_agency(self.agency)

        data = {'job': another_job.id}
        url = reverse('proposal-move-to-job', kwargs={'pk': proposal.id})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)

    def test_linkedin_data_get_candidate_data_own(self):
        """Talent Associate can get linkedin data of own Candidate."""
        candidate = f.create_candidate(self.client_obj)
        data = f.create_candidate_linkedin_data(candidate)

        url = reverse(
            'candidatelinkedindata-get-candidate-data', kwargs={'pk': data.id}
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_linkedin_data_get_candidate_daclient_admin_other_client(self):
        """Talent Associate can't get linkedin data of other's Candidate."""
        candidate = f.create_candidate(f.create_client())
        data = f.create_candidate_linkedin_data(candidate)

        url = reverse(
            'candidatelinkedindata-get-candidate-data', kwargs={'pk': data.id}
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_linkedin_data_get_candidate_data_agency(self):
        """Talent Associate can't get linkedin data of Agency's Candidate."""
        candidate = f.create_candidate(self.agency)
        data = f.create_candidate_linkedin_data(candidate)

        url = reverse(
            'candidatelinkedindata-get-candidate-data', kwargs={'pk': data.id}
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_dashboard_get_statistics(self):
        """Should return data."""
        url = reverse('dashboard-get-statistics')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_deal_pipeline_metrics(self):
        """Talent Associate has no access to the deal pipeline metrics"""
        self.assert_response.no_permission('get', 'deal_pipeline-predicted-values')

    @patch('core.models.Job.import_longlist')
    def test_job_import_longlist(self, import_longlist_mock):
        """Talent Associates can import longlist"""
        job = f.create_job(self.client_obj)
        data = {
            'from_job': job.pk,
            'candidates': [],
        }
        self.assert_response.ok('post', 'job-import-longlist', job.pk, data)


class TestProposalInterviewViewSet(APITestCase):
    def setUp(self):
        self.agency, self.members = f.create_agency_with_members(f.create_recruiter,)
        self.url = reverse('proposal_interviews-list')

        recruiter = self.members[0]

        self.user = f.create_user()
        client = f.create_client(primary_contact=self.user)
        client.assign_administrator(self.user)

        self.client.force_login(self.user)
        job = f.create_job(client)
        self.proposal = f.create_proposal_with_candidate(job, self.user)

        self.interview = f.create_proposal_interview(self.proposal, self.user)

        self.proposal_client = f.create_proposal_with_candidate(
            job, client.primary_contact
        )
        self.interview_client = f.create_proposal_interview(
            self.proposal_client, client.primary_contact
        )

        self.interview_same_proposal_other_member = f.create_proposal_interview(
            self.proposal, recruiter
        )

        self.proposal_other_member = f.create_proposal_with_candidate(job, self.user)
        self.interview_other_proposal_other_member = f.create_proposal_interview(
            self.proposal_other_member, recruiter
        )

        self.object_url = reverse(
            'proposal_interviews-detail', kwargs={'pk': self.interview.pk}
        )

    @staticmethod
    def get_create_update_request_data(proposal=None):
        proposal_part = {'proposal': proposal.id} if proposal else dict()
        return {
            'start_at': f.DEFAULT_INTERVIEW.start_at,
            'end_at': f.DEFAULT_INTERVIEW.end_at,
            'status': f.DEFAULT_INTERVIEW.status,
            **proposal_part,
        }

    def test_get(self):
        """Should return only interviews to proposals agency has access to"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertSetEqual(
            set(item['id'] for item in response.json()['results']),
            {
                self.interview.id,
                self.interview_client.id,
                self.interview_same_proposal_other_member.id,
                self.interview_other_proposal_other_member.id,
            },
        )

    def test_create_interview_agency(self):
        response = self.client.post(
            self.url,
            self.get_create_update_request_data(self.proposal_other_member),
            format='json',
        )

        self.assertEqual(response.status_code, 201)

    def test_create(self):
        response = self.client.post(
            self.url,
            self.get_create_update_request_data(self.proposal_client),
            format='json',
        )

        self.assertEqual(response.status_code, 201)

    def test_update(self):
        response = self.client.patch(
            self.object_url, self.get_create_update_request_data(), format='json'
        )

        self.assertEqual(response.status_code, 200)
