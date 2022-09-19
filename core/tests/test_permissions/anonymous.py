"""Tests related to not authenticated user permissions."""
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from core import fixtures as f
from core import models as m


class AnonymousTests(APITestCase):
    """Tests related to the not authenticated User."""

    # Manager
    def test_get_managers(self):
        """Anonymous User can't get a list of Managers."""
        f.create_hiring_manager(f.create_client())

        url = reverse('manager-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_assign_manager(self):
        """Anonymous User can't assign User as a Manager for the Job."""
        client = f.create_client()
        job = f.create_job(client)
        hm = f.create_hiring_manager(client)

        url = reverse('manager-assign')
        response = self.client.post(
            url, data={'job': job.pk, 'user': hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_remove_from_job_manager(self):
        """Anonymous User can't remove User from Job Managers."""
        client = f.create_client()
        job = f.create_job(client)
        hm = f.create_hiring_manager(client)

        url = reverse('manager-remove-from-job')
        response = self.client.post(
            url, data={'job': job.pk, 'user': hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_invite_manager(self):
        """Anonymous User can't invite Hiring Managers."""
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
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    # Client
    def test_get_clients(self):
        """Anonymous User can't get list of Clients."""
        f.create_client()

        url = reverse('client-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_create_client(self):
        """Anonymous User can't create a Client."""
        data = {'name': 'Test client'}
        url = reverse('client-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_get_client(self):
        """Anonymous User can't get Client details."""
        client = f.create_client()

        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_update_client(self):
        """Anonymous User can't update the Client."""
        client = f.create_client()

        data = {'name': 'New name'}
        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_partial_update_client(self):
        """Anonymous User can't partially update the Client."""
        client = f.create_client()

        data = {'name': 'New name'}
        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_delete_client(self):
        """Anonymous User can't delete the Client."""
        client = f.create_client()

        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    # Client registration request
    def test_create_client_registration_request(self):
        """Anonymous User can create a Client registration request."""
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
        """Anonymous User can create an Agency registration request."""
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
        """Anonymous User can't get the list of Jobs."""
        f.create_job(f.create_client())

        url = reverse('job-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_create_job(self):
        """Anonymous User can't create a Job."""
        data = {
            'title': 'Test job',
            'responsibilities': 'Test responsibilities',
            'work_location': 'Test location',
            'required_languages': [],
            'questions': [],
            'agencies': [],
            'assignees': [],
            'managers': [],
        }
        url = reverse('job-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_get_public_job(self):
        """Anonymous User can get public Job details."""
        job = f.create_job(f.create_client(), public=True)

        url = reverse(
            'private-job-posting-public-detail', kwargs={'uuid': job.public_uuid}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_job(self):
        """Anonymous User can't get Job details."""
        job = f.create_job(f.create_client())

        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_update_job(self):
        """Anonymous User can't update own Job."""
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

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_partial_update_job(self):
        """Anonymous User can't partially update own Job."""
        job = f.create_job(f.create_client())

        data = {'title': 'New title'}
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_delete_job(self):
        """Anonymous User can't delete own Job."""
        job = f.create_job(f.create_client())

        data = {'title': 'New title'}
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_create_public_link(self):
        """Anonymous User can't create Job public link."""
        job = f.create_job(f.create_client())

        url = reverse('private-job-posting-list')
        response = self.client.post(url, {'is_enabled': True}, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_remove_public_link(self):
        """Anonymous User can't remove Job public link."""
        job = f.create_job(f.create_client(), public=True)

        url = reverse('private-job-posting-detail', kwargs={'job_id': job.pk})
        response = self.client.patch(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    # Job file
    def test_create_job_file(self):
        """Anonymous User can't create Job file."""
        url = reverse('job-file-list')
        response = self.client.post(
            url,
            data={
                'file': SimpleUploadedFile('file.txt', b''),
                'job': f.create_job(f.create_client()).id,
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_get_job_file(self):
        """Anonymous User can't get Private Job file."""
        job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'),
            job=f.create_job(f.create_client()),
        )

        url = reverse('job-file-detail', kwargs={'pk': job_file.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_delete_job_file(self):
        """Anonymous User can't delete Job file.."""
        job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'),
            job=f.create_job(f.create_client()),
        )

        url = reverse('job-file-detail', kwargs={'pk': job_file.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    # Agency
    def test_get_agencies(self):
        """Anonymous User can't get the list of Agencies."""
        f.create_agency()

        url = reverse('agency-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_create_agency(self):
        """Anonymous User can't create an Agency."""
        data = {'name': 'Test agency'}
        url = reverse('agency-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_get_agency(self):
        """Anonymous User can't get Agency details."""
        agency = f.create_agency()

        url = reverse('agency-detail', kwargs={'pk': agency.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_update_agency(self):
        """Anonymous User can't update own Agency."""
        agency = f.create_agency()

        data = {'name': 'New agency'}
        url = reverse('agency-detail', kwargs={'pk': agency.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_partial_update_agency(self):
        """Anonymous User can't patch own Agency."""
        agency = f.create_agency()

        data = {'name': 'New agency'}
        url = reverse('agency-detail', kwargs={'pk': agency.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_delete_agency(self):
        """Anonymous User can't delete own Agency."""
        agency = f.create_agency()

        url = reverse('agency-detail', kwargs={'pk': agency.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    # Staff
    def test_get_agency_staff_list(self):
        """Anonymous User can't get Staff."""
        url = reverse('staff-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_get_agency_staff(self):
        """Anonymous User can't access the Staff detail."""
        recruiter = f.create_recruiter(f.create_agency())
        url = reverse('staff-detail', kwargs={'pk': recruiter.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_update_agency_staff(self):
        """Anonymous User can't update the Staff."""
        recruiter = f.create_recruiter(f.create_agency())
        data = {'is_active': False, 'teams': []}
        url = reverse('staff-detail', kwargs={'pk': recruiter.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_patch_agency_staff(self):
        """Anonymous User can't patch the Staff."""
        recruiter = f.create_recruiter(f.create_agency())
        data = {'is_active': False, 'teams': []}
        url = reverse('staff-detail', kwargs={'pk': recruiter.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    # Team
    def test_get_agency_teams(self):
        """Anonymous User can't get the list of Teams."""
        f.create_team(f.create_agency())

        url = reverse('team-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    # Candidate
    def test_get_candidates(self):
        """Anonymous User can't get the list of Candidates."""
        agency = f.create_agency()
        f.create_candidate(agency)

        url = reverse('candidate-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_create_candidate(self):
        """Anonymous User can't create a Candidate."""
        data = {'name': 'Test candidate', 'resume': 'Test resume'}
        url = reverse('candidate-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_get_candidate(self):
        """Anonymous User can't get Candidate details."""
        agency = f.create_agency()
        candidate = f.create_candidate(agency)

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_update_candidate(self):
        """Anonymous User can't update the Candidate."""
        candidate = f.create_candidate(f.create_agency())

        data = {'name': 'New name', 'resume': 'New resume'}
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_partial_update_candidate(self):
        """Anonymous User can't patch the Candidate."""
        candidate = f.create_candidate(f.create_agency())

        data = {'name': 'New name'}
        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_delete_candidate(self):
        """Anonymous User can't delete the Candidate."""
        candidate = f.create_candidate(f.create_agency())

        url = reverse('candidate-detail', kwargs={'pk': candidate.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    # CandidateFile
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_upload_candidate_file(self):
        """Anonymous User can't upload Candidate file."""
        agency = f.create_agency()
        candidate = f.create_candidate(agency)

        url = reverse(
            'candidate-file-upload', kwargs={'pk': candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.post(url, data={'file': ''})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_get_candidate_file(self):
        """Anonymous User can't get Candidate file."""
        agency = f.create_agency()
        candidate = f.create_candidate(agency)

        url = reverse(
            'candidate-file-get', kwargs={'pk': candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_delete_candidate_file(self):
        """Anonymous User can't delete Candidate file."""
        agency = f.create_agency()
        candidate = f.create_candidate(agency)

        url = reverse(
            'candidate-file-delete', kwargs={'pk': candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    # Proposal
    def test_get_proposals(self):
        """Anonymous User can't get the list of Proposals."""
        agency = f.create_agency()
        f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(agency),
            f.create_recruiter(agency),
        )

        url = reverse('proposal-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_create_proposal(self):
        """Anonymous User can't create a Proposal."""
        job = f.create_job(f.create_client())
        candidate = f.create_candidate(f.create_agency())

        data = {'job': job.pk, 'candidate': candidate.pk}
        url = reverse('proposal-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_get_proposal(self):
        """Anonymous User can't get Proposal details."""
        agency = f.create_agency()
        proposal = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(agency),
            f.create_recruiter(agency),
        )

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_update_proposal(self):
        """Anonymous User can't update the Proposal."""
        job = f.create_job(f.create_client())
        agency = f.create_agency()
        candidate = f.create_candidate(agency)
        proposal = f.create_proposal(job, candidate, f.create_recruiter(agency))

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_partial_update_proposal(self):
        """Anonymous User can't patch the Proposal."""
        agency = f.create_agency()
        proposal = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(agency),
            f.create_recruiter(agency),
        )

        new_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        data = {'status': new_status.id}
        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_delete_proposal(self):
        """Anonymous User can't delete the Proposal."""
        agency = f.create_agency()
        proposal = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(agency),
            f.create_recruiter(agency),
        )

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    # ProposalComment
    def test_get_proposal_comments(self):
        """Anonymous User can't get the list of Proposal comments."""
        agency = f.create_agency()
        recruiter = f.create_recruiter(agency)
        proposal = f.create_proposal(
            f.create_job(f.create_client()), f.create_candidate(agency), recruiter,
        )
        f.create_proposal_comment(recruiter, proposal)

        url = reverse('proposalcomment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_get_proposal_comment(self):
        """Anonymous User can't get Proposal Comment details."""
        agency = f.create_agency()
        recruiter = f.create_recruiter(agency)
        proposal = f.create_proposal(
            f.create_job(f.create_client()), f.create_candidate(agency), recruiter,
        )
        comment = f.create_proposal_comment(recruiter, proposal)

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_create_proposal_comment(self):
        """Anonymous User can't create Propoal Comment."""
        agency = f.create_agency()
        proposal = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(agency),
            f.create_recruiter(agency),
        )
        data = {'proposal': proposal.pk, 'text': 'Test comment'}

        url = reverse('proposalcomment-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    # Notification
    def test_mark_all_as_read(self):
        """Anonymous User can't mark all Notifications as read."""
        url = reverse('notification-mark-all-as-read')
        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_mark_as_read(self):
        """Anonymous User can't mark Notification as read."""
        notification = f.create_notification(
            f.create_user(),
            verb=m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
            actor=f.create_client(),
        )

        url = reverse('notification-mark-as-read', kwargs={'pk': notification.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    # Contract
    def test_get_contracts(self):
        """Anonymous User can't get the list of Contracts."""
        f.create_contract(f.create_agency(), f.create_client())

        url = reverse('contract-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_create_contract(self):
        """Anonymous User can't create a Contract."""
        data = {'agency': f.create_agency().pk}
        url = reverse('contract-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_get_contract(self):
        """Anonymous User can't get Contract details."""
        contract = f.create_contract(f.create_agency(), f.create_client())

        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_update_contract(self):
        """Anonymous User can't update the Contract."""
        agency = f.create_agency()
        contract = f.create_contract(agency, f.create_client())

        data = {'agency': agency.pk}
        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_partial_update_contract(self):
        """Anonymous User can't patch the Contract."""
        agency = f.create_agency()
        contract = f.create_contract(agency, f.create_client())

        data = {'agency': agency.pk}
        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_delete_contract(self):
        """Anonymous User can't delete the Contract."""
        contract = f.create_contract(f.create_agency(), f.create_client())

        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    # User
    def test_get_user(self):
        """Anonymous User can get his own User detail."""
        url = reverse('user-read-current')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_change_password(self):
        """Anonymous User can update his own User password."""
        data = {
            'old_password': f.DEFAULT_USER['password'],
            'new_password1': 'New password',
            'new_password2': 'New password',
        }
        url = reverse('change-password')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_confirm_password_reset(self):
        """Anonymous User can confirm password reset with the correct token."""
        user = f.create_recruiter(f.create_agency(), 'otheruser@test.com', 'password')

        url = reverse('confirm-password-reset')
        data = {
            'uidb64': f.get_user_uidb64(user),
            'token': f.get_user_token(user),
            'new_password1': 'New password',
            'new_password2': 'New password',
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'Password reset successfully.'})

    def test_login(self):
        """Anonymous User can log into another account."""
        user = f.create_client_administrator(
            f.create_client(), 'otheruser@test.com', 'password'
        )

        data = {'email': 'otheruser@test.com', 'password': 'password'}
        url = reverse('user-login')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.pk, response.data['id'])

    def test_logout(self):
        """Anonymous User can log out."""
        url = reverse('user-logout')
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'Logged out.'})

    def test_reset_password(self):
        """Anonymous User can request a password reset."""
        user = f.create_recruiter(f.create_agency(), 'otheruser@test.com', 'password')

        data = {'email': user.email}
        url = reverse('reset-password')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'Password reset email sent.'})

    def test_update_settings(self):
        """Anonymous User can update hist own User settings."""
        data = {'email': 'newemail@test.com'}
        url = reverse('user-update-settings')
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_upload_photo(self):
        """Can save user photo."""
        image_data = f.get_jpeg_image_content()
        response = self.client.post(
            reverse('user-upload-photo'),
            {'file': SimpleUploadedFile('img.jpg', image_data)},
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_photo(self):
        """Can delete user photo."""
        response = self.client.post(reverse('user-delete-photo'))
        self.assertEqual(response.status_code, 403)

    def test_check_linkedin_candidate_exists(self):
        """Anonymous User can't check candidate exists."""
        url = reverse('ext-api-check-linkedin-candidate-exists')
        data = {'linkedinUrl': 'https://www.linkedin.com/in/someslug/'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_add_linkedin_candidate(self):
        """Anonymous User can't add candidate."""
        url = reverse('ext-api-add-linkedin-candidate')

        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_proposal_move_to_job(self):
        """Should not move proposal to other job."""
        agency = f.create_agency()
        recruiter = f.create_recruiter(agency)
        client = f.create_client()

        job = f.create_job(client)
        job.assign_agency(agency)

        proposal = f.create_proposal(job, f.create_candidate(agency), recruiter)

        another_job = f.create_job(client)
        another_job.assign_agency(agency)

        data = {'job': another_job.id}
        url = reverse('proposal-move-to-job', kwargs={'pk': proposal.id})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 403)

    def test_linkedin_data_get_candidate_data(self):
        """Should not return candidate data."""
        candidate = f.create_candidate(f.create_agency())
        data = f.create_candidate_linkedin_data(candidate)

        url = reverse(
            'candidatelinkedindata-get-candidate-data', kwargs={'pk': data.id}
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_dashboard_get_statistics(self):
        """Should not return data."""
        url = reverse('dashboard-get-statistics')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)


class TestProposalInterviewViewSet(APITestCase):
    def setUp(self):
        self.agency, self.members = f.create_agency_with_members(
            f.create_recruiter, f.create_agency_manager
        )
        self.url = reverse('proposal_interviews-list')

        recruiter, self.user = self.members

        client = f.create_client()
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

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_create_interview_other_member(self):
        """Anonymous are not allowed to create interviews"""
        response = self.client.post(
            self.url, self.get_create_update_request_data(self.proposal_other_member)
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_create_interview_client_proposal(self):
        """Anonymous are not allowed to create interviews"""
        response = self.client.post(
            self.url, self.get_create_update_request_data(self.proposal_client)
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)

    def test_update(self):
        """Anonymous are not allowed to modify interviews"""
        response = self.client.patch(
            self.object_url, self.get_create_update_request_data()
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), f.NOT_AUTHENTICATED)
