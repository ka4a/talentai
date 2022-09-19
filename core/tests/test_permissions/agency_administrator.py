"""Tests related to Agency Administrator user permissions."""
import tempfile
from unittest.mock import patch, Mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings, RequestFactory
from djangorestframework_camel_case.util import camelize, underscoreize
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from core import fixtures as f, models as m, serializers as s
from core.tests.generic_response_assertions import GenericResponseAssertionSet
from core.utils import pick, SerializerErrorsMock


class AgencyAdministratorTests(APITestCase):
    """Tests related to the Agency Administrator role."""

    def setUp(self):
        """Create the required objects during initialization."""
        super().setUp()
        self.user = f.create_user()
        self.agency = f.create_agency(primary_contact=self.user)
        self.agency.assign_agency_administrator(self.user)
        self.assert_response = GenericResponseAssertionSet(self)

        self.client.force_login(self.user)

    # Manager
    def test_get_managers(self):
        """Agency Admin can't get a list of Managers."""
        self.assert_response.no_permission('get', 'manager-list')

    def test_assign_manager(self):
        """Agency Admin can't assign User as a Manager for the Job."""
        client = f.create_client()
        job = f.create_job(client)
        hm = f.create_hiring_manager(client)

        self.assert_response.no_permission(
            'post', 'manager-assign', data={'job': job.pk, 'user': hm.pk}
        )

    def test_remove_from_job_manager(self):
        """Agency Admin can't remove User from Job Managers."""
        client = f.create_client()
        job = f.create_job(client)
        hm = f.create_hiring_manager(client)

        self.assert_response.no_permission(
            'post', 'manager-remove-from-job', data={'job': job.pk, 'user': hm.pk}
        )

    def test_invite_manager(self):
        """Agency Admin can't invite Hiring Manager."""
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

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    # Client
    def test_get_clients(self):
        """Agency Admin can get the list of Clients."""
        f.create_client()
        client_2 = f.create_client()
        f.create_contract(self.agency, client_2)
        f.create_proposal(
            f.create_job(client_2), f.create_candidate(self.agency), self.user,
        )

        url = reverse('client-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual({el['id'] for el in response.json()['results']}, {client_2.pk})

    def test_create_client(self):
        """Agency Admin can create a Client."""
        data = {'name': 'Test client'}
        url = reverse('client-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {'name': 'Test client'})

    def test_get_client(self):
        """Agency Admin can get the Client details."""
        client = f.create_client()
        f.create_contract(self.agency, client)

        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], client.pk)

    def test_get_client_without_contract(self):
        """Agency Admin can't get Client details if there's no Contract."""
        client = f.create_client()

        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_update_client(self):
        """Agency Admin can't update the Client."""
        client = f.create_client(name='Test client')

        data = {'name': 'New name'}
        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_update_own_client(self):
        """Agency Admin can update their own Client"""
        client = f.create_client()
        client.owner_agency = self.agency
        client.save()

        data = {'name': 'New name'}
        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'name': 'New name'})

    def test_partial_update_client(self):
        """Agency Admin can't partially update the Client."""
        client = f.create_client(name='Test client')

        data = {'name': 'New name'}
        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_partial_update_own_client(self):
        """Agency Admin can partially update their own Client"""
        client = f.create_client()
        client.owner_agency = self.agency
        client.save()

        data = {'name': 'New name'}
        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'name': 'New name'})

    def test_delete_client(self):
        """Agency Admin can't delete the Client."""
        client = f.create_client(name='Test client')

        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    # Client registration request
    def test_create_client_registration_request(self):
        """Agency Admin can create a Client registration request."""
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
        """Agency Admin can create an Agency registration request."""
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
        """Agency Admin can get only these Jobs his Agency assigned to."""
        f.create_job(f.create_client())
        job, client = f.get_job_assigned_to_agency_and_client(self.agency)

        url = reverse('job-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual({el['id'] for el in response.json()['results']}, {job.pk})

    def create_job_with_expired_contract(self):
        contract = f.create_contract(
            self.agency, f.create_client(), m.ContractStatus.EXPIRED.key
        )
        job = f.create_job(contract.client)
        job.assign_agency(self.agency)
        return job

    def test_get_jobs_unsigned_contract(self):
        self.create_job_with_expired_contract()
        job = self.create_assigned_job()

        results = self.assert_response.ok('get', 'job-list').json()['results']

        id_set = {item['id'] for item in results}
        self.assertEqual({job.pk}, id_set)

    def test_get_jobs_unpublished(self):
        """Agency Admin can get only published Jobs."""
        client = f.create_client()
        j1 = f.get_job_assigned_to_agency(self.agency, client)

        f.get_job_assigned_to_agency(self.agency, client, job_data={'published': False})

        url = reverse('job-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual({el['id'] for el in response.json()['results']}, {j1.pk})

    def get_create_job_data(self, client_id=None, owner_id=None):
        return {
            'function': m.Function.objects.first().pk,
            'title': 'Test job',
            'responsibilities': 'Test responsibilities',
            'required_languages': [],
            'questions': [],
            'agencies': [],
            'assignees': [],
            'managers': [],
            'client': client_id,
            'work_location': 'Tokyo',
            'country': 'jp',
            'interview_templates': [],
        }

    def test_create_job(self):
        """Agency Manager can create a Job."""
        data = self.get_create_job_data(
            client_id=f.create_client(owner_agency=self.agency).id,
            owner_id=f.create_recruiter(self.user.profile.org).id,
        )
        data['interview_templates'] = [
            {
                'interview_type': template.interview_type,
                'order': template.default_order,
            }
            for template in m.InterviewTemplate.objects.all()
        ]
        response = self.assert_response.created('post', 'job-list', data=data)

        response_data = underscoreize(response.json())

        qs = m.Job.objects.filter(id=response_data['id'])
        self.assertTrue(qs.exists())

        job = qs.first()
        self.assertIn(self.user, job.assignees)

        # current agency is automatically assigned
        data['agencies'] = [self.agency.id]
        data['interview_templates'] = [
            {
                'interview_type': 'general',
                'description': '',
                'id': 1,
                'interviewer': None,
                'order': 1,
            },
            {
                'interview_type': 'technical_fit',
                'description': '',
                'id': 2,
                'interviewer': None,
                'order': 2,
            },
            {
                'interview_type': 'cultural_fit',
                'description': '',
                'id': 3,
                'interviewer': None,
                'order': 3,
            },
        ]
        self.assertEqual(
            len(data.pop('interview_templates')),
            len(response_data.pop('interview_templates')),
        )

        for key in data.keys() & response_data.keys():
            self.assertEqual(data[key], response_data[key], msg=key)

    def test_create_job_without_client(self):
        data = self.get_create_job_data(
            owner_id=f.create_recruiter(self.user.profile.org).id,
        )
        data.pop('client')

        errors = SerializerErrorsMock(s.CreateUpdateJobSerializer)
        errors.add_field_error('client', 'required')

        self.assert_response.bad_request(
            'post', 'job-list', data=data, expected_data=errors.messages
        )

    def test_create_job_with_not_owned_client(self):
        data = self.get_create_job_data(
            owner_id=f.create_recruiter(self.user.profile.org).id,
            client_id=f.create_client().pk,
        )

        errors = SerializerErrorsMock(s.CreateUpdateJobSerializer)
        errors.add_field_error('client', 'does_not_exist', pk_value=data['client'])

        self.assert_response.bad_request(
            'post', 'job-list', data=data, expected_data=errors.messages
        )

    def test_create_job_with_not_own_client(self):
        """Agency Admin can't create a Job for client agency doesn't own."""
        owner = f.create_recruiter(self.user.profile.org)

        data = {
            'function': m.Function.objects.first().pk,
            'title': 'Test job',
            'responsibilities': 'Test responsibilities',
            'work_location': 'Test location',
            'required_languages': [],
            'questions': [],
            'agencies': [],
            'assignees': [],
            'managers': [],
            'owner': owner.id,
            'client': f.create_client().id,
        }

        self.assert_response.bad_request('post', 'job-list', data=data)

    def test_get_public_job(self):
        """Agency Admin can get public Job details."""
        job = f.create_job(f.create_client(), public=True)

        url = reverse(
            'private-job-posting-public-detail', kwargs={'uuid': job.public_uuid}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_job_agency_assigned(self):
        """Agency Admin can get the Job his Agency assigned to."""
        job = f.get_job_assigned_to_agency(self.agency,)

        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], job.pk)

    def test_get_job_not_assigned(self):
        """Agency Admin can't get the Job his Agency not assigned to."""
        job = f.create_job(f.create_client())

        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_get_job_unpublished(self):
        """Agency Admin can't get the unpublished Job."""
        job = f.create_job(f.create_client(), published=False)

        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_update_job_assigned(self):
        """Agency Admin can't update the Job his Agency assigned to."""
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)

        data = {
            'title': 'New title',
            'responsibilities': 'New responsibilities',
            'work_location': 'New location',
            'required_languages': [],
            'questions': [],
            'agencies': [self.agency.pk],
            'assignees': [],
            'managers': [],
        }

        self.assert_response.not_found('put', 'job-detail', job.pk, data)

    def test_update_job_not_assigned(self):
        """Agency Admin can't update the Job his Agency not assigned to."""
        job = f.create_job(f.create_client())

        data = {
            'title': 'New title',
            'responsibilities': 'New responsibilities',
            'work_location': 'New location',
            'required_languages': [],
            'questions': [],
            'agencies': [self.agency.pk],
            'assignees': [],
            'managers': [],
        }
        self.assert_response.not_found('put', 'job-detail', job.pk, data)

    def test_partial_update_job_assigned(self):
        """Agency Admin can't patch the Job his Agency assigned to."""
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)

        self.assert_response.not_found(
            'patch', 'job-detail', job.pk, {'title': 'New title'}
        )

    def test_partial_update_job_not_assigned(self):
        """Agency Admin can't patch the Job his Agency not assigned to."""
        job = f.create_job(f.create_client())

        self.assert_response.not_found(
            'patch', 'job-detail', job.pk, {'title': 'New title'}
        )

    def fill_job(self, job, openings_count=1, proposals_count=None):

        job.status = m.JobStatus.FILLED.key
        job.openings_count = openings_count

        job.save()

        if proposals_count is None:
            proposals_count = openings_count

        offer_accepted = m.ProposalStatus.objects.filter(group='offer_accepted').first()
        for i in range(proposals_count):
            f.create_proposal(
                job, f.create_candidate(self.agency), self.user, status=offer_accepted
            )

        return job

    def test_partial_update_reopen_job(self):
        """Agency Admin should be able to reopen the job"""
        job = f.create_job(self.agency)
        job = m.Job.objects.get(pk=job.id)
        job = self.fill_job(job)

        data = {'status': m.JobStatus.OPEN.key, 'openings_count': 2}

        self.assert_response.ok('patch', 'job-detail', job.pk, data)

    def test_partial_update_reopen_client_job(self):
        """Agency Admin shouldn't be able to reopen client's job even if assigned"""
        job = self.fill_job(self.create_assigned_job())

        data = {'status': m.JobStatus.OPEN.key, 'openings_count': 2}

        self.assert_response.no_permission('patch', 'job-detail', job.pk, data)

    def test_partial_update_reopen_job_not_enough_openings(self):
        """Agency Admin shouldn't be able to reopen the job, if no openings_available"""
        job = self.fill_job(f.create_job(self.agency))

        data = {'status': m.JobStatus.OPEN.key}
        errors = SerializerErrorsMock(s.CreateUpdateJobSerializer)
        errors.add_field_error('status', 'not_enough_openings')

        self.assert_response.bad_request(
            'patch', 'job-detail', job.pk, data, errors.messages
        )

    def test_delete_job_assigned(self):
        """Agency Admin can't delete the Job his Agency assigned to."""
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)

        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_delete_job_not_assigned(self):
        """Agency Admin can't delete the Job his Agency not assigned to."""
        job = f.create_job(f.create_client())

        self.assert_response.no_permission('delete', 'job-detail', job.pk)

    def create_assigned_job(self):
        client = f.create_client()
        f.create_contract(self.agency, client)
        job = f.create_job(client)
        job.assign_agency(self.agency)
        job.create_default_interview_templates()
        return job

    def get_expected_assignee_response_data(self, assigned):
        return camelize(
            s.JobAssigneeSerializer(
                instance=(user.id for user in assigned),
                many=True,
                context={'request': Mock(user=self.user)},
            ).data
        )

    def create_and_assign_member(self, job):
        other_assigned_member = f.create_agency_manager(self.agency)
        job.assign_member(other_assigned_member)
        return other_assigned_member

    def test_assign_member_own_job(self):
        """Agency admin should be able to assign staff member to a agency own job"""
        job = f.create_job(self.agency)

        member_to_assign = f.create_recruiter(self.agency)

        expected_data = self.get_expected_assignee_response_data([member_to_assign,])

        self.assert_response.ok(
            'patch',
            'job-assign-member',
            job.pk,
            {'assignee': member_to_assign.id},
            expected_data,
        )

    def test_assign_member_client_assigned_job(self):
        """Agency admin should be able to assign staff member to a client's job, if agency is assigned"""
        job = self.create_assigned_job()

        member_to_assign = f.create_recruiter(self.agency)

        expected_data = self.get_expected_assignee_response_data([member_to_assign,])

        self.assert_response.ok(
            'patch',
            'job-assign-member',
            job.pk,
            {'assignee': member_to_assign.id},
            expected_data,
        )

    def test_assign_member_client_job(self):
        """Agency admin shouldn't be able to assign staff member to client's job, if agency is not assigned"""
        job = f.create_job(f.create_client())

        member_to_assign = f.create_recruiter(self.agency)

        self.assert_response.not_found(
            'patch', 'job-assign-member', job.pk, {'assignee': member_to_assign.id}
        )

    def test_assign_member_client_job_contract_expired(self):
        """Agency admin shouldn't be able to assign staff member to client's job, if contract is expired"""
        job = self.create_job_with_expired_contract()

        member_to_assign = f.create_recruiter(self.agency)

        self.assert_response.not_found(
            'patch', 'job-assign-member', job.pk, {'assignee': member_to_assign.id}
        )

    def test_assign_member_of_other_agency(self):
        """User should not be able be able to assign staff member of other organisation"""
        job = self.create_assigned_job()
        other_agency = f.create_agency()
        other_agency_member = f.create_recruiter(other_agency)

        self.assert_response.bad_request(
            'patch',
            'job-assign-member',
            job.pk,
            {'assignee': other_agency_member.id},
            serializer_class=s.AssignJobMemberSerializer,
        )

    def test_assign_member_of_client_to_assigned_to_agency_job(self):
        """User should not be able be able to assign staff member of client to job assigned to user's agency"""
        job = self.create_assigned_job()
        client_member = f.create_hiring_manager(job.organization)

        self.assert_response.bad_request(
            'patch',
            'job-assign-member',
            job.pk,
            {'assignee': client_member.id},
            serializer_class=s.AssignJobMemberSerializer,
        )

    def test_withdraw_member_own_job(self):
        """Agency admin should be able to withdraw assigned staff member to a agency own job"""
        job = f.create_job(self.agency)

        member_to_withdraw = self.create_and_assign_member(job)

        self.assert_response.ok(
            'patch',
            'job-withdraw-member',
            job.pk,
            {'assignee': member_to_withdraw.id},
            [],
        )

    def test_withdraw_member_client_assigned_job(self):
        """Agency admin should be able to withdraw assigned staff member to a client's job, if agency is assigned"""
        job = self.create_assigned_job()

        member_to_withdraw = self.create_and_assign_member(job)

        self.assert_response.ok(
            'patch',
            'job-withdraw-member',
            job.pk,
            {'assignee': member_to_withdraw.id},
            [],
        )

    def test_withdraw_member_client_job(self):
        """Agency admin shouldn't be able to withdraw assigned staff member to client's job, if agency is not assigned"""
        job = f.create_job(f.create_client())

        member_to_withdraw = self.create_and_assign_member(job)

        self.assert_response.not_found(
            'patch', 'job-withdraw-member', job.pk, {'assignee': member_to_withdraw.id}
        )

    def test_create_public_link(self):
        """Agency Admin can't create Job public link."""
        job = self.create_assigned_job()

        self.assert_response.no_permission('post', 'private-job-posting-list')

    def test_remove_public_link(self):
        """Agency Admin can't remove Job public link."""
        job = f.create_job(f.create_client(), public=True)

        self.assert_response.not_found(
            'patch', 'private-job-posting-detail', job.pk, lookup_url_kwarg='job_id'
        )

    # Job file
    def test_create_job_file_client_assigned_job(self):
        """Agency Admin can't create Job file for client job."""
        job = self.create_assigned_job()

        data = {'file': SimpleUploadedFile('file.txt', b'content'), 'job': job.id}
        self.assert_response.no_permission(
            'post', 'job-file-list', data=data, format='multipart'
        )

    def test_create_job_file_own_job(self):
        """Agency Admin can create Job file for own job."""
        job = f.create_job(self.agency)

        data = {'file': SimpleUploadedFile('file.txt', b'content'), 'job': job.id}
        self.assert_response.created(
            'post', 'job-file-list', data=data, format='multipart'
        )

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_get_job_file_not_assigned(self):
        """Agency admin can't create Job file if not assigned."""
        job = f.create_job(f.create_client())

        job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=job
        )

        self.assert_response.not_found('get', 'job-file-detail', job_file.pk)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_get_job_file_agency_assigned(self):
        """Agency admin can't create Job file if Agency assigned."""
        job = f.get_job_assigned_to_agency(self.agency,)

        job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=job
        )

        self.assert_response.ok('get', 'job-file-detail', job_file.pk)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_get_job_file_agency_own(self):
        """Agency admin can't create Job file if Agency assigned."""
        job = f.create_job(self.agency)

        job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=job
        )

        self.assert_response.ok('get', 'job-file-detail', job_file.pk)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_delete_client_job_file(self):
        """Agency Admin can't delete Job file.."""
        job = self.create_assigned_job()

        job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=job
        )

        self.assert_response.no_permission('delete', 'job-file-detail', job_file.pk)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_delete_own_job_file(self):
        """Agency Admin can't delete Job file.."""
        job = f.create_job(self.agency)

        job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=job
        )

        self.assert_response.no_content('delete', 'job-file-detail', job_file.pk)
        self.assertFalse(m.JobFile.objects.filter(id=job_file.id).exists())

    # Agency
    def test_get_agencies(self):
        """Agency Admin can get the list of Agencies."""
        f.create_agency()

        url = reverse('agency-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {el['id'] for el in response.json()['results']}, {self.agency.pk}
        )

    def test_create_agency(self):
        """Agency Admin can't create an Agency."""
        data = {'name': 'Test agency'}
        url = reverse('agency-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_get_agency_own(self):
        """Agency Admin can get his own Agency details."""
        url = reverse('agency-detail', kwargs={'pk': self.agency.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.agency.pk)

    def test_get_agency_other(self):
        """Agency Admin can't get other Agency details."""
        agency = f.create_agency()

        url = reverse('agency-detail', kwargs={'pk': agency.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_update_agency_own(self):
        """Agency Admin can update own Agency."""
        data = {'name': 'New agency'}
        url = reverse('agency-detail', kwargs={'pk': self.agency.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data.items() <= response.json().items())

    def test_update_agency_other(self):
        """Agency Admin can't update other Agency."""
        agency = f.create_agency(name='Other agency')
        data = {'name': 'New agency'}
        url = reverse('agency-detail', kwargs={'pk': agency.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_partial_update_agency_own(self):
        """Agency Admin can patch own Agency."""
        data = {'name': 'New agency'}
        url = reverse('agency-detail', kwargs={'pk': self.agency.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data.items() <= response.json().items())

    def test_partial_update_agency_other(self):
        """Agency Admin can't patch other Agency."""
        agency = f.create_agency(name='Other agency')
        data = {'name': 'New agency'}
        url = reverse('agency-detail', kwargs={'pk': agency.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_delete_agency_own(self):
        """Agency Admin can't delete own Agency."""
        url = reverse('agency-detail', kwargs={'pk': self.agency.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_delete_agency_other(self):
        """Agency Admin can't delete other Agency."""
        agency = f.create_agency(name='Other agency')
        url = reverse('agency-detail', kwargs={'pk': agency.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    # Staff
    def test_get_agency_staff_list(self):
        """Agency Admin can get Staff."""
        recruiter = f.create_recruiter(self.agency)

        recruiter_other_team = f.create_recruiter(self.agency)
        recruiter_other_team.profile.teams.set([f.create_team(self.agency)])
        recruiter_other_team.save()

        # Recruiter from other Agency
        f.create_recruiter(f.create_agency())

        url = reverse('staff-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {el['id'] for el in response.json()['results']},
            {self.user.pk, recruiter.pk, recruiter_other_team.pk},
        )

    def test_get_agency_staff(self):
        """Agency Admin can access the Staff detail."""
        recruiter = f.create_recruiter(self.agency)
        url = reverse('staff-detail', kwargs={'pk': recruiter.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_agency_staff_other_team(self):
        """Agency Admin can access the Staff detail from other team."""
        recruiter = f.create_recruiter(self.agency)
        recruiter.profile.teams.set([f.create_team(self.agency)])
        recruiter.save()

        url = reverse('staff-detail', kwargs={'pk': recruiter.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_agency_staff_other_agency(self):
        """Agency Admin can't access the Staff from other Agency."""
        recruiter = f.create_recruiter(f.create_agency())
        url = reverse('staff-detail', kwargs={'pk': recruiter.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_update_agency_staff(self):
        """Agency Admin can update the Staff."""
        data = {'is_active': False, 'teams': []}
        recruiter = f.create_recruiter(self.agency)
        url = reverse('staff-detail', kwargs={'pk': recruiter.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 200)

    def test_update_agency_staff_other_team(self):
        """Agency Admin can update the Staff from other team."""
        data = {'is_active': False, 'teams': []}
        recruiter = f.create_recruiter(self.agency)
        recruiter.profile.teams.set([f.create_team(self.agency)])
        recruiter.save()

        url = reverse('staff-detail', kwargs={'pk': recruiter.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 200)

    def test_update_agency_staff_other_agency(self):
        """Agency Admin can't update the Staff from other Agency."""
        data = {'is_active': False, 'teams': []}
        recruiter = f.create_recruiter(f.create_agency())

        url = reverse('staff-detail', kwargs={'pk': recruiter.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 404)

    def test_patch_agency_staff(self):
        """Agency Admin can patch the Staff."""
        data = {'is_active': False, 'teams': []}
        recruiter = f.create_recruiter(self.agency)
        url = reverse('staff-detail', kwargs={'pk': recruiter.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)

    def test_patch_agency_staff_other_team(self):
        """Agency Admin can patch the Staff from other team."""
        data = {'is_active': False, 'teams': []}
        recruiter = f.create_recruiter(self.agency)
        recruiter.profile.teams.set([f.create_team(self.agency)])
        recruiter.save()

        url = reverse('staff-detail', kwargs={'pk': recruiter.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)

    def test_patch_agency_staff_other_agency(self):
        """Agency Admin can't patch the Staff from other Agency."""
        data = {'is_active': False, 'teams': []}
        recruiter = f.create_recruiter(f.create_agency())

        url = reverse('staff-detail', kwargs={'pk': recruiter.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)

    # Team
    def test_get_agency_teams(self):
        """Agency Admin can get the list of Teams."""
        team_user_in = f.create_team(self.agency)
        self.user.profile.teams.set([team_user_in])

        team_own_agency = f.create_team(self.agency)

        # Other Agency team
        f.create_team(f.create_agency())

        url = reverse('team-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {el['id'] for el in response.json()}, {team_user_in.pk, team_own_agency.pk}
        )

    # Candidate
    def test_get_candidates(self):
        """Agency Admin can get Candidates only from his own Agency."""
        f.create_candidate(f.create_agency())
        candidate = f.create_candidate(self.agency)

        url = reverse('candidate-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {el['id'] for el in response.json()['results']}, {candidate.pk}
        )

    def test_create_candidate(self):
        """Agency Admin can create a Candidate."""
        data = {
            'email': "testcandidate@localhost",
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
        self.assertEqual(camelize(data), pick(camelize(data), response.json()))

    def test_get_candidate_own_agency(self):
        """Agency Admin can get the Candidate of his own Agency."""
        candidate = f.create_candidate(self.agency)

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], candidate.pk)

    def test_get_candidate_other_agency(self):
        """Agency Admin can't get the Candidate of the other Agency."""
        candidate = f.create_candidate(f.create_agency())

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_update_candidate_own_agency(self):
        """Agency Admin can update the Candidate of his own Agency."""
        candidate = f.create_candidate(
            self.agency,
            first_name='Test',
            last_name='name',
            email='test@mail.com',
            summary='Test summary',
        )
        data = {
            'first_name': 'New',
            'last_name': 'Candidate',
            'email': 'new@mail.com',
            'summary': 'New summary',
            'owner': self.user.pk,
            'current_salary': 0,
            'current_country': 'jp',
        }
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(camelize(data), pick(camelize(data), response.json()))

    def test_update_candidate_other_agency(self):
        """Agency Admin can't update the Candidate of the other Agency."""
        candidate = f.create_candidate(f.create_agency())

        data = {'first_name': 'New name', 'summary': 'New summary'}
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_partial_update_candidate_own_agency(self):
        """Agency Admin can patch the Candidate of his own Agency."""
        candidate = f.create_candidate(
            self.agency,
            first_name='Test',
            last_name='name',
            email='test@mail.com',
            summary='Test summary',
        )
        data = {'first_name': 'New'}
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(camelize(data).items() <= response.json().items())

    def test_partial_update_candidate_other_agency(self):
        """Agency Admin can't patch the Candidate of the other Agency."""
        candidate = f.create_candidate(f.create_agency())

        data = {'name': 'New name'}
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_delete_candidate_own_agency(self):
        """Agency Admin can delete the Candidate from his own Agency."""
        candidate = f.create_candidate(self.agency)
        candidate.archived = True
        candidate.save()

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)

    def test_delete_candidate_other_agency(self):
        """Agency Admin can't delete the Candidate from the other Agency."""
        candidate = f.create_candidate(f.create_agency())

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    # CandidateFile
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_upload_file_own_candidate(self):
        """Agency Admin can upload Candidate file for own Candidate."""
        candidate = f.create_candidate(self.agency)

        url = reverse(
            'candidate-file-upload', kwargs={'pk': candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.post(url, data={'file': ''})

        self.assertEqual(response.status_code, 200)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_upload_file_other_candidate(self):
        """Agency Admin can't upload Candidate file for other Candidate."""
        candidate = f.create_candidate(f.create_agency())

        url = reverse(
            'candidate-file-upload', kwargs={'pk': candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.post(url, data={'file': ''})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_get_file_own_candidate(self):
        """Agency Admin can upload Candidate file for own Candidate."""
        candidate = f.create_candidate(self.agency)
        candidate.photo = SimpleUploadedFile('file.txt', b'')
        candidate.save()

        url = reverse(
            'candidate-file-get', kwargs={'pk': candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_get_file_other_candidate(self):
        """Agency Admin can't upload Candidate file for other Candidate."""
        candidate = f.create_candidate(f.create_agency())
        candidate.photo = SimpleUploadedFile('file.txt', b'')
        candidate.save()

        url = reverse(
            'candidate-file-get', kwargs={'pk': candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_delete_file_own_candidate(self):
        """Agency Admin can delete Candidate file for own Candidate."""
        candidate = f.create_candidate(self.agency)
        candidate.photo = SimpleUploadedFile('file.txt', b'')
        candidate.save()

        url = reverse(
            'candidate-file-delete', kwargs={'pk': candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 200)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_delete_file_other_candidate(self):
        """Agency Admin can't delete Candidate file for other Candidate."""
        candidate = f.create_candidate(f.create_agency())
        candidate.photo = SimpleUploadedFile('file.txt', b'')
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
        """Agency Administrator can import Zoho Candidate."""
        get_zoho_candidate_mock.return_value = f.ZOHO_CANDIDATE_DATA

        url = reverse('zoho-get-candidate')

        zoho_candidate_url = (
            'https://recruit.zoho.com/recruit/EntityInfo.do?' 'module=Candidates&id=123'
        )

        response = self.client.post(url, {'url': zoho_candidate_url}, format='json')
        self.assertEqual(response.status_code, 200)

    # Proposal
    def test_get_proposals(self):
        """Agency Admin can get Proposals linked to his own Agency only."""
        job = f.create_job(f.create_client())
        agency = f.create_agency()
        f.create_proposal(
            job, f.create_candidate(agency), f.create_agency_administrator(agency)
        )
        proposal = f.create_proposal(job, f.create_candidate(self.agency), self.user)

        url = reverse('proposal-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual({el['id'] for el in response.json()['results']}, {proposal.pk})

    def test_create_proposal_own_agency_assigned_job(self):
        """Agency Admin can create Proposal: own Candidate, assigned Job."""
        job = self.create_assigned_job()
        candidate = f.create_candidate(self.agency)

        data = {'job': job.pk, 'candidate': candidate.pk}

        response_data = self.assert_response.created(
            'post', 'proposal-list', data=data
        ).json()

        proposal = m.Proposal.objects.get(id=response_data['id'])
        self.assertEqual(
            proposal.interviews.count(),
            m.InterviewTemplate.objects.filter(default=True).count(),
        )
        self.assertEqual(data, pick(response_data, data))

    def test_create_proposal_agency_own_job(self):
        """Agency Admin can create Proposal: own Candidate, own Job."""
        data = {
            'job': f.create_job(self.agency).pk,
            'candidate': f.create_candidate(self.agency).pk,
        }

        response_data = self.assert_response.created(
            'post', 'proposal-list', data=data
        ).json()

        self.assertEqual(data, pick(response_data, data))

    def test_create_proposal_own_agency_not_assigned_job(self):
        """Agency Admin can't create Proposal: own Candidate, not assigned Job."""
        self.assert_response.no_permission(
            'post',
            'proposal-list',
            data={
                'job': f.create_job(f.create_client()).pk,
                'candidate': f.create_candidate(self.agency).pk,
            },
        )

    def test_create_proposal_other_agency_assigned_job(self):
        """Agency Admin can't create Proposal: other Cand, assigned Job."""
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)
        candidate = f.create_candidate(f.create_agency())

        data = {'job': job.pk, 'candidate': candidate.pk}
        url = reverse('proposal-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_create_proposal_other_agency_not_assigned_job(self):
        """Agency Admin can't create Proposal: o. Cand not assigned Job."""
        job = f.create_job(f.create_client())
        candidate = f.create_candidate(f.create_agency())

        data = {'job': job.pk, 'candidate': candidate.pk}
        url = reverse('proposal-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_get_proposal_own_agency(self):
        """Agency Admin can get Proposal linked to his own Agency."""
        proposal = f.create_proposal(
            f.create_job(f.create_client()), f.create_candidate(self.agency), self.user,
        )

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], proposal.pk)

    def test_get_proposal_other_agency(self):
        """Agency Admin can't get Proposal linked to other Agency."""
        proposal = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(f.create_agency()),
            self.user,
        )

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_update_proposal_own_agency_own_job(self):
        """Recruiter can update own Agency Proposal with own Job."""
        job = f.create_job(self.agency)
        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, self.user)

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}

        self.assert_response.ok('put', 'proposal-detail', proposal.pk, data)

    def test_update_proposal_own_agency_assigned_job(self):
        """Agency Admin can't update own Agency Prop with assigned Job."""
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)
        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, self.user)

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        errors = SerializerErrorsMock(s.UpdateProposalSerializer)
        errors.add_non_field_error('not_member_of_job_owner')

        self.assert_response.bad_request(
            'put', 'proposal-detail', proposal.pk, data, errors.messages
        )

    def test_update_proposal_own_agency_not_assigned_job(self):
        """Agency Admin can't update own Agency Proposal not assigned Job."""
        job = f.create_job(f.create_client())
        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, self.user)

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        errors = SerializerErrorsMock(s.UpdateProposalSerializer)
        errors.add_non_field_error('not_member_of_job_owner')

        self.assert_response.bad_request(
            'put', 'proposal-detail', proposal.pk, data, errors.messages
        )

    def test_update_proposal_other_agency_assigned_job(self):
        """Agency Admin can't update other Agency Proposal assigned Job."""
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)
        candidate = f.create_candidate(f.create_agency())
        proposal = f.create_proposal(job, candidate, self.user)

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_update_proposal_other_agency_not_assigned_job(self):
        """Agency Admin can't upd other Agency Proposal not assigned Job."""
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)
        candidate = f.create_candidate(f.create_agency())
        proposal = f.create_proposal(job, candidate, self.user)

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_partial_update_proposal_own_agency_assigned_job(self):
        """Agency Admin can't patch own Agency Proposal with assigned Job."""
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)
        proposal = f.create_proposal(job, f.create_candidate(self.agency), self.user)

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        errors = SerializerErrorsMock(s.UpdateProposalSerializer)
        errors.add_non_field_error('not_member_of_job_owner')

        self.assert_response.bad_request(
            'patch', 'proposal-detail', proposal.pk, data, errors.messages
        )

    def test_partial_update_proposal_own_agency_not_assigned_job(self):
        """Agency Admin can't patch own Agency Proposal not assigned Job."""
        proposal = f.create_proposal(
            f.create_job(f.create_client()), f.create_candidate(self.agency), self.user,
        )

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        errors = SerializerErrorsMock(s.UpdateProposalSerializer)
        errors.add_non_field_error('not_member_of_job_owner')

        self.assert_response.bad_request(
            'patch', 'proposal-detail', proposal.pk, data, errors.messages
        )

    def test_partial_update_proposal_own_agency_own_job(self):
        """Agency Admin can't patch own Agency Proposal not assigned Job."""
        proposal = f.create_proposal(
            f.create_job(self.agency), f.create_candidate(self.agency), self.user,
        )

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        self.assert_response.ok('patch', 'proposal-detail', proposal.pk, data)

    def test_partial_update_proposal_other_agency_assigned_job(self):
        """Agency Admin can't patch other Agency Proposal assigned Job."""
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)
        proposal = f.create_proposal(
            job, f.create_candidate(f.create_agency()), self.user
        )

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_partial_update_proposal_other_agency_not_assigned_job(self):
        """Agency Admin can't patch other Agency Prop, not assigned Job."""
        proposal = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(f.create_agency()),
            self.user,
        )

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_delete_proposal_own_agency_assigned_job(self):
        """Agency Admin can't delete own Agency Proposal assigned Job."""
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)
        proposal = f.create_proposal(
            job, f.create_candidate(self.agency), self.user, stage='longlist'
        )

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)

    def test_delete_proposal_own_agency_not_assigned_job(self):
        """Agency Admin can't delete own Agency Proposal not assigned Job."""
        proposal = f.create_proposal(
            f.create_job(f.create_client()), f.create_candidate(self.agency), self.user,
        )

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_delete_proposal_other_agency_assigned_job(self):
        """Agency Admin can't delete other Agency Proposal assigned Job."""
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)
        proposal = f.create_proposal(
            job, f.create_candidate(f.create_agency()), self.user
        )

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_delete_proposal_other_agency_not_assigned_job(self):
        """Agency Admin can't delete other Agency Prop, not assigned Job."""
        proposal = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(f.create_agency()),
            self.user,
        )

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    # ProposalComment
    def test_get_proposal_comments(self):
        """Agency Admin can get the list of Proposal comments."""
        proposal = f.create_proposal(
            f.create_job(f.create_client()), f.create_candidate(self.agency), self.user,
        )
        comment = f.create_proposal_comment(self.user, proposal)

        url = reverse('proposalcomment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual({i['id'] for i in response.json()['results']}, {comment.pk})

    def test_create_proposal_comment_own_proposal(self):
        """Agency Admin can create Proposal Comment for own Proposal."""
        proposal = f.create_proposal(
            f.create_job(f.create_client()), f.create_candidate(self.agency), self.user,
        )
        data = {'proposal': proposal.pk, 'text': 'Test comment'}

        url = reverse('proposalcomment-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)

    def test_create_proposal_comment_own_agency_proposal(self):
        """Agency Admin can create Comment for Proposal from own Agency."""
        proposal = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(self.agency),
            f.create_recruiter(self.agency),
        )
        data = {'proposal': proposal.pk, 'text': 'Test comment'}

        url = reverse('proposalcomment-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)

    def test_create_proposal_comment_other_proposal(self):
        """Agency Admin can't create Comment for other Agency's Proposal."""
        proposal_other = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(f.create_agency()),
            self.user,
        )
        data = {'proposal': proposal_other.pk, 'text': 'Test comment'}

        url = reverse('proposalcomment-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 400)

    def test_get_proposal_comment_own(self):
        """Agency Admin can get own Proposal Comment details."""
        proposal = f.create_proposal(
            f.create_job(f.create_client()), f.create_candidate(self.agency), self.user,
        )
        comment = f.create_proposal_comment(self.user, proposal)

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], comment.pk)

    def test_get_proposal_comment_user_own_agency(self):
        """Agency Admin can get own Agency User's Proposal Comment."""
        proposal = f.create_proposal(
            f.create_job(f.create_client()), f.create_candidate(self.agency), self.user,
        )
        recruiter = f.create_recruiter(self.agency)
        comment = f.create_proposal_comment(recruiter, proposal)

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], comment.pk)

    def test_get_proposal_comment_other_agency(self):
        """Agency Admin can't get Proposal Comment of other Agency."""
        agency_other = f.create_agency()
        recruiter = f.create_recruiter(agency_other)

        proposal = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(agency_other),
            recruiter,
        )
        comment = f.create_proposal_comment(recruiter, proposal)

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_get_proposal_comment_other_agency_public(self):
        """Agency Admin can't get public Comment of other Agency."""
        agency_other = f.create_agency()
        recruiter = f.create_recruiter(agency_other)

        proposal = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(agency_other),
            recruiter,
        )
        comment = f.create_proposal_comment(recruiter, proposal, public=True)

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_get_proposal_comment_client(self):
        """Agency Admin can't get Client's Proposal Comment."""
        client = f.create_client()
        client_admin = f.create_client_administrator(client)

        proposal = f.create_proposal(
            f.create_job(client), f.create_candidate(self.agency), self.user
        )
        comment = f.create_proposal_comment(ta, proposal)

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_get_proposal_comment_client_public(self):
        """Agency Admin can get Client's public Proposal Comment."""
        client = f.create_client()
        client_admin = f.create_client_administrator(client)

        proposal = f.create_proposal(
            f.create_job(client), f.create_candidate(self.agency), self.user
        )
        comment = f.create_proposal_comment(ta, proposal, public=True)

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], comment.pk)

    # Notification
    def test_mark_all_as_read(self):
        """Agency Admin User can mark all Notifications as read."""
        url = reverse('notification-mark-all-as-read')
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    def test_mark_as_read(self):
        """Agency Admin User can mark own Notification as read."""
        notification = f.create_notification(
            self.user,
            verb=m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
            actor=f.create_agency(),
        )

        url = reverse('notification-mark-as-read', kwargs={'pk': notification.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    def test_mark_as_read_other_user(self):
        """Agency Admin User can't mark other User Notification as read."""
        notification = f.create_notification(
            f.create_user(),
            verb=m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
            actor=f.create_agency(),
        )

        url = reverse('notification-mark-as-read', kwargs={'pk': notification.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    # Contract
    def test_get_contracts(self):
        """Agency Admin can get Contracts linked to his own Agency only."""
        client = f.create_client()
        contract = f.create_contract(self.agency, client)
        f.create_contract(f.create_agency(), client)

        url = reverse('contract-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual({el['id'] for el in response.json()['results']}, {contract.pk})

    def test_create_contract_own_agency(self):
        """Agency Admin can't create a Contract for his own Agency."""
        data = {'agency': self.agency.pk}
        url = reverse('contract-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_create_contract_other_agency(self):
        """Agency Admin can't create a Contract for the other Agency."""
        data = {'agency': f.create_agency().pk}
        url = reverse('contract-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_get_contract_own_agency(self):
        """Agency Admin can get Contract linked to his own Agency."""
        contract = f.create_contract(self.agency, f.create_client())

        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], contract.pk)

    def test_get_contract_other_agency(self):
        """Agency Admin can't get Contract linked to other Agency."""
        contract = f.create_contract(f.create_agency(), f.create_client())

        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_update_contract_own_agency(self):
        """Agency Admin can update the Contract of his own Agency."""
        contract = f.create_contract(self.agency, f.create_client())

        data = {'agency': self.agency.pk}
        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], contract.pk)

    def test_update_contract_other_agency(self):
        """Agency Admin can't update the Contract of the other Agency."""
        agency = f.create_agency()
        contract = f.create_contract(agency, f.create_client())

        data = {'agency': agency.pk}
        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def check_partial_update_contract(self, agency, status):
        client = f.create_client()
        contract = f.create_contract(
            agency, client, m.ContractStatus.AGENCY_INVITED.key
        )
        client.primary_contact = f.create_client_administrator(client)
        client.save()

        data = {'is_agency_signed': True}
        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.patch(url, data, format='json')

        response_data = f.NO_PERMISSION

        if status == 200:
            response_data = {
                'id': contract.id,
                'status': contract.status,
                'isAgencySigned': True,
            }

        if status == 404:
            response_data = f.NOT_FOUND

        self.assertEqual(response.status_code, status)
        self.assertEqual(response.json(), response_data)

    def test_partial_update_contract_own_agency(self):
        """Agency Admin can't patch the Contract of his own Agency."""
        self.check_partial_update_contract(self.agency, 200)

    def test_partial_update_contract_other_agency(self):
        """Agency Admin can't patch the Contract of the other Agency."""
        self.check_partial_update_contract(f.create_agency(), 404)

    def test_delete_contract_own_agency(self):
        """Agency Admin can't delete the Contract of his own Agency."""
        contract = f.create_contract(self.agency, f.create_client())

        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    def test_delete_contract_other_agency(self):
        """Agency Admin can't delete the Contract of the other Agency."""
        contract = f.create_contract(f.create_agency(), f.create_client())

        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NO_PERMISSION)

    # User
    def test_get_user(self):
        """Agency Admin can get his own User detail."""
        url = reverse('user-read-current')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.user.pk)

    def test_change_password(self):
        """Agency Admin can update his own User password."""
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
        """Agency Admin can confirm password reset with the correct token."""
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
        """Agency Admin can log into another account."""
        other_user = f.create_agency_administrator(
            self.agency, 'otheruser@test.com', 'password'
        )

        data = {'email': 'otheruser@test.com', 'password': 'password'}
        url = reverse('user-login')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(other_user.pk, response.data['id'])

    def test_logout(self):
        """Agency Admin can log out."""
        url = reverse('user-logout')
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'Logged out.'})

    def test_reset_password(self):
        """Agency Admin can request a password reset."""
        data = {'email': self.user.email}
        url = reverse('reset-password')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'Password reset email sent.'})

    def test_update_settings(self):
        """Agency Admin can update hist own User settings."""
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
        """Should check candidate exists."""
        url = reverse('ext-api-check-linkedin-candidate-exists')
        data = {'linkedinUrl': 'https://www.linkedin.com/in/someslug/'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

    def test_add_linkedin_candidate(self):
        """Should create Candidate."""
        url = reverse('ext-api-add-linkedin-candidate')

        data = {
            'name': 'Some Candidate',
            'contactInfo': {'linkedIn': 'https://www.linkedin.com/in/someslug/'},
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

    def test_proposal_move_to_job(self):
        """Should move proposal to other job."""
        client = f.create_client()

        job = f.get_job_assigned_to_agency(self.agency, client)

        proposal = f.create_proposal(
            job, f.create_candidate(self.agency), f.create_recruiter(self.agency)
        )

        another_job = f.create_job(client)
        another_job.assign_agency(self.agency)

        data = {'job': another_job.id}
        url = reverse('proposal-move-to-job', kwargs={'pk': proposal.id})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)

    def test_linkedin_data_get_candidate_data(self):
        """Should return candidate data."""
        candidate = f.create_candidate(self.agency)
        data = f.create_candidate_linkedin_data(candidate)

        url = reverse(
            'candidatelinkedindata-get-candidate-data', kwargs={'pk': data.id}
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_linkedin_data_get_candidate_data_other_agency(self):
        """Should not return candidate data of other agency."""
        candidate = f.create_candidate(f.create_agency())
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
        """Agency Administrator has access to the deal pipeline metrics"""
        self.assert_response.ok('get', 'deal_pipeline-predicted-values')

    @patch('core.models.Job.import_longlist')
    def test_job_import_longlist(self, import_longlist_mock):
        """Agency Administrator can import longlist"""
        job = f.create_job(self.agency)
        data = {
            'from_job': job.pk,
            'candidates': [],
        }
        self.assert_response.ok('post', 'job-import-longlist', job.pk, data)


class TestProposalInterviewViewSet(APITestCase):
    def setUp(self):
        self.agency, self.members = f.create_agency_with_members(f.create_recruiter,)
        self.url = reverse('proposal_interviews-list')

        self.assertEqual(
            m.AgencyAdministrator, type(self.agency.primary_contact.profile)
        )
        self.user = self.agency.primary_contact

        recruiter = self.members[0]
        self.client.force_login(self.user)

        client = f.create_client()
        job = f.create_job(client)
        job.assign_agency(self.agency)
        f.create_contract(self.agency, client)

        self.proposal = f.create_proposal_with_candidate(job, self.user)

        agency_job = f.create_job(self.agency, client=client)
        self.proposal_agency_job = f.create_proposal_with_candidate(
            agency_job, self.user
        )
        self.proposal_agency_job_other_member = f.create_proposal_with_candidate(
            agency_job, recruiter
        )

        self.assert_response = GenericResponseAssertionSet(self)

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

    @staticmethod
    def get_create_update_request_data(proposal=None):
        proposal_part = {'proposal': proposal.pk} if proposal else dict()
        return {
            'start_at': f.DEFAULT_INTERVIEW.start_at,
            'end_at': f.DEFAULT_INTERVIEW.end_at,
            'status': f.DEFAULT_INTERVIEW.status,
            **proposal_part,
        }

    def test_get(self):
        """Should return only interviews to proposals agency has access to"""
        response = self.assert_response.ok('get', 'proposal_interviews-list')
        self.assertSetEqual(
            set(item['id'] for item in response.json()['results']),
            {
                self.interview.id,
                self.interview_same_proposal_other_member.id,
                self.interview_other_proposal_other_member.id,
            },
        )

    def test_create_interview_other_member(self):
        """Agency is not allowed to create interviews"""
        errors = SerializerErrorsMock(s.CreateUpdateProposalInterviewSerializer)
        errors.add_field_error('proposal', 'not_org_job')

        self.assert_response.bad_request(
            'post',
            'proposal_interviews-list',
            data=self.get_create_update_request_data(self.proposal_other_member),
            expected_data=errors.messages,
        )

    def test_create_interview_client_proposal(self):
        """Agency is not allowed to create interviews"""

        errors = SerializerErrorsMock(s.CreateUpdateProposalInterviewSerializer)
        errors.add_field_error(
            'proposal', 'does_not_exist', pk_value=self.proposal_client.pk
        )

        self.assert_response.bad_request(
            'post',
            'proposal_interviews-list',
            data=self.get_create_update_request_data(self.proposal_client),
            expected_data=errors.messages,
        )

    def test_create_interview_agency_job(self):
        """Agency is allowed to create interviews to proposals, that proposed to agency job"""

        self.assert_response.created(
            'post',
            'proposal_interviews-list',
            data=self.get_create_update_request_data(self.proposal_agency_job),
        )

    def test_update(self):
        self.assert_response.no_permission(
            'patch',
            'proposal_interviews-detail',
            self.interview.pk,
            self.get_create_update_request_data(self.proposal_other_member),
        )

    def test_update_mine_agency_job(self):
        interview = f.create_proposal_interview(self.proposal_agency_job, self.user)

        self.assert_response.ok(
            'patch',
            'proposal_interviews-detail',
            interview.pk,
            self.get_create_update_request_data(self.proposal_agency_job_other_member),
        )

    def test_delete(self):
        self.assert_response.no_permission(
            'delete', 'proposal_interviews-detail', self.interview.pk,
        )

    def test_delete_mine_agency_job(self):
        interview = f.create_proposal_interview(self.proposal_agency_job, self.user)

        self.assert_response.no_content(
            'delete', 'proposal_interviews-detail', interview.pk
        )
