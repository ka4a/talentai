"""Tests related to views of the core Django app."""
import tempfile
from unittest.case import skip
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from djangorestframework_camel_case.util import camelize, underscoreize
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from rest_framework.serializers import FileField

from core import fixtures as f
from core import models as m
from core import serializers as s
from core.converter import PDFConverter
from core.views.user_activate_account import get_activation_token
from core.views.user_activate_account import get_user_from_activation_token
from core.zoho import ZohoImportError
from core.utils import LinkedinProfile, format_serializer_as_response

User = get_user_model()


class UserTests(APITestCase):
    """Tests related to User endpoints."""

    def setUp(self):
        """Create a User during set up process."""
        super().setUp()

        self.user = f.create_superuser(
            'a@test.com', 'password', first_name='First', last_name='Last'
        )

    def test_read_current(self):
        """Should return current user."""
        self.client.force_login(self.user)

        response = self.client.get(reverse('user-read-current'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), camelize(s.UserSerializer(self.user).data))

    def test_reset_password(self):
        """Should send email with reset link."""
        url = reverse('reset-password')
        response = self.client.post(url, {'email': self.user.email}, format='json')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertIn(self.user.email, email.to)
        self.assertIn('/reset', email.body)

    def test_confirm_password_reset(self):
        """Should update user's password."""
        url = reverse('confirm-password-reset')
        data = {
            'uidb64': f.get_user_uidb64(self.user),
            'token': f.get_user_token(self.user),
            'new_password1': 'newPassword@',
            'new_password2': 'newPassword@',
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            self.client.login(email=self.user.email, password='newPassword@')
        )

    def test_confirm_password_reset_invalid_token(self):
        """Should not update user's password."""
        url = reverse('confirm-password-reset')
        data = {
            'uidb64': f.get_user_uidb64(self.user),
            'token': '514-aabbccddf4ddec1018e5',
            'new_password1': 'newPassword@',
            'new_password2': 'newPassword@',
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)

        self.assertFalse(
            self.client.login(email=self.user.email, password='newPassword@')
        )

    def test_change_password(self):
        """Should change current user's password."""
        self.client.force_login(self.user)

        url = reverse('change-password')
        data = {
            'old_password': 'password',
            'new_password1': 'newPassword@',
            'new_password2': 'newPassword@',
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            self.client.login(email=self.user.email, password='newPassword@')
        )

    def test_update_settings(self):
        """Should update current user's settings."""
        self.client.force_login(self.user)

        url = reverse('user-update-settings')
        data = {
            'email': 'newEmail@test.com',
            'first_name': 'newFirstName',
            'last_name': 'newLastName',
            'locale': 'en',
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertEqual(
            response.json(), camelize(s.UserUpdateSerializer(self.user).data)
        )
        self.assertEqual(self.user.email, 'newEmail@test.com')

    def test_update_legal(self):
        """Should update current user's settings."""
        self.client.force_login(self.user)

        url = reverse('user-update-legal')
        data = {'is_legal_agreed': True}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_legal_agreed)

    def test_update_settings_password(self):
        """Should update current user's password."""
        self.client.force_login(self.user)

        new_password = 'tCf_-IVj5D0'

        url = reverse('user-update-settings')
        data = {'oldPassword': 'password', 'newPassword': new_password}
        response = self.client.patch(url, data, format='json')

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.check_password(new_password))

    def test_update_settings_password_not_updated(self):
        """Should NOT update current user's password."""
        self.client.force_login(self.user)

        new_password = 'tCf_-IVj5D0'

        url = reverse('user-update-settings')
        data = {'oldPassword': 'invalid', 'newPassword': new_password}
        response = self.client.patch(url, data, format='json')

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertTrue('oldPassword' in response.json())
        self.assertFalse(self.user.check_password(new_password))

    def test_user_notifications_count(self):
        """Should return user's unread notifications count."""
        self.client.force_login(self.user)

        client = f.create_client()

        f.create_notification(
            self.user, m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT, actor=client,
        )

        response = self.client.get(reverse('user-notifications-count'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {'count': self.user.unread_notifications_count}
        )

    def test_upload_photo(self):
        """Should save user photo."""
        self.client.force_login(self.user)
        self.assertFalse(self.user.photo)

        image_data = f.get_jpeg_image_content()
        response = self.client.post(
            reverse('user-upload-photo'),
            {'file': SimpleUploadedFile('img.jpg', image_data)},
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertTrue(self.user.photo)

    def test_delete_photo(self):
        """Should delete user photo."""
        self.client.force_login(self.user)

        self.user.photo.save('img.jpg', ContentFile(f.get_jpeg_image_content()))
        self.user.save()

        response = self.client.post(reverse('user-delete-photo'))

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertFalse(self.user.photo)

    def test_update_frontend_setting(self):
        """Should update frontend settings"""
        user = f.create_client_administrator(f.create_client())
        self.client.force_login(user)
        url = reverse('user-update-settings')

        proper_value = 10  # see core.models.FrontendSettingsSchema

        data = {'frontend_settings': {'jobs_show_per': proper_value}}
        response = self.client.patch(url, data, format='json')
        user.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.frontend_settings['jobs_show_per'], proper_value)

    def test_update_frontend_settings_not_proper_value(self):
        """Non proper values are not allowed"""
        user = f.create_client_administrator(f.create_client())
        self.client.force_login(user)
        url = reverse('user-update-settings')

        not_proper_value = 17  # see core.models.FrontendSettingsSchema

        data = {'frontend_settings': {'jobs_show_per': not_proper_value}}

        response = self.client.patch(url, data, format='json')
        user.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertNotEqual(user.frontend_settings['jobs_show_per'], not_proper_value)
        self.assertEqual(
            underscoreize(response.json()),
            {
                "frontend_settings": {
                    'jobs_show_per': [
                        f'The value {not_proper_value} is not allowed. Must be '
                        f'one of {m.FrontendSettingsSchema.PAGINATION_SCHEMA}'
                    ]
                }
            },
        )


class TeamTests(APITestCase):
    def setUp(self):
        """Create necessary object during initialization."""
        agency = f.create_agency()
        self.team = f.create_team(agency)

        self.client.force_login(f.create_agency_administrator(agency))

    def test_get_teams(self):
        """Should return a list of teams of User's Agency."""
        url = reverse('team-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), camelize(s.TeamSerializer([self.team], many=True).data)
        )


# deep converting ordered dictionary to regular one
# so difference displayed clearer


class ManagerTests(APITestCase):
    """Tests related to Manager endpoints."""

    def setUp(self):
        """Create Talent Associate and all the related objects."""
        self.client_obj = f.create_client()
        self.hm = f.create_hiring_manager(self.client_obj)
        self.job = f.create_job(self.client_obj, owner=self.hm)
        self.client_admin = f.create_client_administrator(self.client_obj)
        self.client.force_login(self.client_admin)

    def test_get_managers(self):
        """Should return a list of all Hiring Managers assigned and not."""
        hm_assigned = f.create_hiring_manager(self.client_obj)
        self.job.assign_manager(hm_assigned)

        url = reverse('manager-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['results'],
            format_serializer_as_response(
                s.UserSerializer(
                    self.client_obj.members.all().order_by('id'), many=True
                )
            ),
        ),

    def test_assign_manager(self):
        """Should assign a User as a Manager for the Job."""
        url = reverse('manager-assign')
        response = self.client.post(
            url, data={'job': self.job.pk, 'user': self.hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'User assigned as a Job Manager.'})
        self.assertTrue(self.hm in self.job.managers)

    def test_assign_manager_already_assigned(self):
        """Should not assign same Manager twice."""
        self.job.assign_manager(self.hm)

        url = reverse('manager-assign')
        response = self.client.post(
            url, data={'job': self.job.pk, 'user': self.hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {'detail': 'User is already assigned as a Job Manager.'}
        )
        self.assertEqual(self.job.managers.count(), 1)
        self.assertTrue(self.hm in self.job.managers)

    def test_assign_manager_client_admin_associate(self):
        """Should assign client admin as a Manager."""
        url = reverse('manager-assign')
        response = self.client.post(
            url, data={'job': self.job.pk, 'user': self.client_admin.pk}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.job.managers.count(), 1)

    def test_assign_manager_recruiter(self):
        """Should not assign Recruiter as a Manager."""
        r = f.create_recruiter(f.create_agency())

        url = reverse('manager-assign')
        response = self.client.post(
            url, data={'job': self.job.pk, 'user': r.pk}, format='json'
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.job.managers.count(), 0)

    def test_remove_from_job_manager(self):
        """Should remove a User from the Job Managers."""
        self.job.assign_manager(self.hm)

        url = reverse('manager-remove-from-job')
        response = self.client.post(
            url, data={'job': self.job.pk, 'user': self.hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'User removed from Job Managers.'})
        self.assertFalse(self.hm in self.job.managers)

    def test_remove_from_job_manager_not_in_managers(self):
        """Should not remove User if he is not in Managers."""
        url = reverse('manager-remove-from-job')
        response = self.client.post(
            url, data={'job': self.job.pk, 'user': self.hm.pk}, format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {'detail': 'User is not a Manager of this Job.'}
        )

    def test_remove_from_job_manager_client_admin_not_in_managers(self):
        """Should not remove if not manager."""
        url = reverse('manager-remove-from-job')
        response = self.client.post(
            url, data={'job': self.job.pk, 'user': self.client_admin.pk}, format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {'detail': 'User is not a Manager of this Job.'}
        )
        self.assertEqual(self.job.managers.count(), 0)

    def test_remove_from_job_manager_recruiter(self):
        """Should not remove Recruiter."""
        r = f.create_recruiter(f.create_agency())

        url = reverse('manager-remove-from-job')
        response = self.client.post(
            url, data={'job': self.job.pk, 'user': r.pk}, format='json'
        )

        self.assertEqual(response.status_code, 403)

    def test_invite_manager(self):
        """Should return a proper message."""
        url = reverse('manager-invite')
        response = self.client.post(
            url,
            data={
                'first_name': 'Test',
                'last_name': 'Name',
                'email': 'testmail@localhost',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'Invite link sent.'})

    def test_invite_manager_user_created(self):
        """User successfully created."""
        url = reverse('manager-invite')
        self.client.post(
            url,
            data={
                'first_name': 'Test',
                'last_name': 'Name',
                'email': 'testmail@localhost',
            },
            format='json',
        )

        self.assertEqual(User.objects.filter(email='testmail@localhost').count(), 1)

    def test_invite_manager_email_sent(self):
        """Invite link sent."""
        url = reverse('manager-invite')
        self.client.post(
            url,
            data={
                'first_name': 'Test',
                'last_name': 'Name',
                'email': 'testmail@localhost',
            },
            format='json',
        )

        email = mail.outbox[0]

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('testmail@localhost', email.to)
        self.assertIn('/reset', email.body)

    def test_invite_manager_user_is_hiring_manager(self):
        """Should create a User with the Hiring Manager profile."""
        url = reverse('manager-invite')
        self.client.post(
            url,
            data={
                'first_name': 'Test',
                'last_name': 'Name',
                'email': 'testmail@localhost',
            },
            format='json',
        )

        user = User.objects.filter(email='testmail@localhost').first()
        self.assertTrue(isinstance(user.profile, m.ClientStandardUser))

    def test_invite_manager_user_client(self):
        """Should create a User with the same Organization."""
        url = reverse('manager-invite')
        self.client.post(
            url,
            data={
                'first_name': 'Test',
                'last_name': 'Name',
                'email': 'testmail@localhost',
            },
            format='json',
        )

        user = User.objects.filter(email='testmail@localhost').first()
        self.assertEqual(user.profile.client, self.client_admin.profile.client)

    def test_invite_manager_use_in_managers(self):
        """Should assign a new User as a Manager for the Organization."""
        url = reverse('manager-invite')
        self.client.post(
            url,
            data={
                'first_name': 'Test',
                'last_name': 'Name',
                'email': 'testmail@localhost',
            },
            format='json',
        )

        user = User.objects.filter(email='testmail@localhost').first()
        self.assertTrue(
            user.profile
            in self.client_admin.profile.client.clientstandarduser_set.all()
        )


class LoginTests(APITestCase):
    """Login tests."""

    def test_login(self):
        """Returns a serialized User object."""
        user = f.create_user(
            'a@test.com', 'password', first_name='First', last_name='Last'
        )

        url = reverse('user-login')
        data = {'email': user.email, 'password': 'password'}
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), camelize(s.UserSerializer(user).data))

    def test_login_is_active_false_with_correct_password(self):
        """Returns deactivated error if User is not active."""
        user = f.create_user(
            'a@test.com',
            'password',
            first_name='First',
            last_name='Last',
            is_active=False,
        )

        url = reverse('user-login')
        data = {'email': user.email, 'password': 'password'}
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Your account is deactivated.'})

    def test_login_is_active_false_with_wrong_password(self):
        """Returns credentials error if User is not active, password wrong."""
        user = f.create_user(
            'a@test.com',
            'password',
            first_name='First',
            last_name='Last',
            is_active=False,
        )

        url = reverse('user-login')
        data = {'email': user.email, 'password': 'incorrect'}
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Email or password is not valid.'})

    def test_login_not_existing_email(self):
        """Returns credentials error if not existing email used."""
        f.create_user(
            'a@test.com', 'password', first_name='First', last_name='Last',
        )

        url = reverse('user-login')
        data = {'email': 'other@test.com', 'password': 'password'}
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Email or password is not valid.'})

    def test_login_incorrect_password(self):
        """Returns credentials error if wrong password passed."""
        user = f.create_user(
            'a@test.com', 'password', first_name='First', last_name='Last',
        )

        url = reverse('user-login')
        data = {'email': user.email, 'password': 'incorrect'}
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Email or password is not valid.'})


class AgencyRegistrationViewSetTests(APITestCase):
    """AgencyRegistrationViewSet tests."""

    def test_agency_registration_request(self):
        """Should create AgencyRegistrationRequest."""
        url = reverse('agencyregistrationrequest-list')
        response = self.client.post(
            url,
            data={
                'name': 'Agency Name',
                'user': {
                    'firstName': 'John',
                    'lastName': 'Smith',
                    'email': 'john.smith@test.com',
                    'password': '7*&^&zkd',
                    'country': 'jp',
                },
                'termsOfService': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)

        r = m.AgencyRegistrationRequest.objects.first()
        self.assertEqual(r.name, 'Agency Name')
        self.assertEqual(r.user.first_name, 'John')
        self.assertEqual(r.user.last_name, 'Smith')
        self.assertEqual(r.user.email, 'john.smith@test.com')

    def test_agency_registration_request_via_job(self):
        """Should create AgencyRegistrationRequest."""
        client = f.create_client()
        job = f.create_job(client, public=True)

        url = reverse('agencyregistrationrequest-list')
        response = self.client.post(
            url,
            data={
                'viaJob': str(job.public_uuid),
                'name': 'Agency Name',
                'user': {
                    'firstName': 'John',
                    'lastName': 'Smith',
                    'email': 'john.smith@test.com',
                    'password': '7*&^&zkd',
                    'country': 'jp',
                },
                'termsOfService': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)

        r = m.AgencyRegistrationRequest.objects.first()
        self.assertEqual(r.via_job, job)

    def test_agency_registration_request_with_invite(self):
        """Should create Agency with unused invite."""
        invite = m.AgencyInvite.objects.create(
            email='bob@x.agency', private_note='invite for X'
        )
        url = reverse('agencyregistrationrequest-list')
        response = self.client.post(
            url,
            data={
                'token': invite.token,
                'name': 'Agency Name',
                'user': {
                    'firstName': 'John',
                    'lastName': 'Smith',
                    'email': 'john.smith@test.com',
                    'password': '7*&^&zkd',
                    'country': 'jp',
                },
                'termsOfService': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)

        invite.refresh_from_db()
        self.assertIsNotNone(invite.used_by)
        agency = invite.used_by
        self.assertEqual(agency.name, 'Agency Name')

    def test_agency_registration_request_with_invite_already_used(self):
        """Should not create Agency with already used invite."""
        agency = f.create_agency()
        invite = m.AgencyInvite.objects.create(
            email='bob@x.agency', private_note='invite for X'
        )
        invite.used_by = agency
        invite.save()

        url = reverse('agencyregistrationrequest-list')
        response = self.client.post(
            url,
            data={
                'token': invite.token,
                'name': 'Agency Name',
                'user': {
                    'firstName': 'John',
                    'lastName': 'Smith',
                    'email': 'john.smith@test.com',
                    'password': '7*&^&zkd',
                    'country': 'jp',
                },
                'termsOfService': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)

        invite.refresh_from_db()
        self.assertEqual(invite.used_by, agency)
        self.assertIsNone(m.Agency.objects.exclude(id=agency.id).first())

        r = m.AgencyRegistrationRequest.objects.first()
        self.assertEqual(r.name, 'Agency Name')


class ClientRegistrationViewSetTests(APITestCase):
    """ClientRegistrationViewSet tests."""

    def test_client_registration_request(self):
        """Should create ClientRegistrationRequest."""
        url = reverse('clientregistrationrequest-list')
        response = self.client.post(
            url,
            data={
                'name': 'Client Name',
                'user': {
                    'firstName': 'John',
                    'lastName': 'Smith',
                    'email': 'john.smith@test.com',
                    'password': '7*&^&zkd',
                },
                'termsOfService': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)

        r = m.ClientRegistrationRequest.objects.first()
        self.assertEqual(r.name, 'Client Name')
        self.assertEqual(r.user.first_name, 'John')
        self.assertEqual(r.user.last_name, 'Smith')
        self.assertEqual(r.user.email, 'john.smith@test.com')


class ClientTests(APITestCase):
    """Tests related to the Client viewset."""

    def setUp(self):
        """Create related objects during initialization."""
        super().setUp()

        user = f.create_superuser('a@test.com', 'password')
        self.client.force_login(user)

    def test_get_clients(self):
        """Should return a list of all Clients."""
        client_1 = f.create_client(name='Test client 1')
        client_2 = f.create_client(name='Test client 2')

        url = reverse('client-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            response.json()['results'],
            [
                {
                    'id': client_1.pk,
                    'name': 'Test client 1',
                    'proposalsCount': None,
                    'openJobsCount': None,
                    'country': client_1.country,
                    'ownerAgencyId': None,
                },
                {
                    'id': client_2.pk,
                    'name': 'Test client 2',
                    'proposalsCount': None,
                    'openJobsCount': None,
                    'country': client_2.country,
                    'ownerAgencyId': None,
                },
            ],
        )

    def test_get_clients_without_clients(self):
        """Should return an empty list if no Clients created."""
        url = reverse('client-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'], [])

    def test_get_client(self):
        """Should return Client details."""
        client = f.create_client()

        url = reverse('client-detail', kwargs={'pk': client.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                'id': client.pk,
                'name': f.DEFAULT_CLIENT['name'],
                'proposalsCount': None,
                'openJobsCount': None,
                'country': client.country,
                'ownerAgencyId': None,
            },
        )

    def test_get_client_without_client(self):
        """Should return 404 status code if not existing pk requested."""
        url = reverse('client-detail', kwargs={'pk': f.NOT_EXISTING_PK})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


class JobFileTests(APITestCase):
    """Tests reltaed to the JobFile viewset."""

    def setUp(self):
        """Create Job during class initialization."""
        super().setUp()
        client = f.create_client()
        self.user = f.create_client_administrator(client)
        self.job = f.create_job(client)

        self.client.force_login(self.user)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_create_job_file(self):
        """Should upload a Job file."""
        url = reverse('job-file-list')
        response = self.client.post(
            url,
            data={
                'file': SimpleUploadedFile('file.txt', b'i am not empty anymore'),
                'job': self.job.pk,
            },
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data.get('job'), self.job.pk)
        self.assertTrue(data.get('file').endswith('file.txt'))
        self.assertNotEqual(self.job.jobfile_set.count(), 0)

    def test_create_job_file_without_file(self):
        """Job file is not uploaded if no file in request."""
        url = reverse('job-file-list')
        response = self.client.post(url, data={'job': self.job.pk})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {'file': [FileField.default_error_messages['required']]}
        )
        self.assertEqual(self.job.jobfile_set.count(), 0)

    def test_create_job_file_without_job(self):
        """Job file is not uploaded if no job id in request."""
        url = reverse('job-file-list')
        response = self.client.post(
            url,
            data={'file': SimpleUploadedFile('file.txt', b'i am not empty anymore'),},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)
        self.assertEqual(self.job.jobfile_set.count(), 0)

    @patch('core.signals.convert_job_file.delay')
    # mock task call to prevent triggering conversion unnecessary
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_get_job_file(self, *args):
        """Should return Job file as an attachment."""
        job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=self.job
        )

        url = reverse('job-file-detail', kwargs={'pk': job_file.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'contents')
        self.assertTrue(
            response.get('Content-Disposition').startswith('inline; filename="')
        )

    def test_get_job_file_not_existing_pk(self):
        """Response 404 returned when not existing pk provided."""
        url = reverse('job-file-detail', kwargs={'pk': f.NOT_EXISTING_PK})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_get_job_file_without_file(self):
        """Response 404 returned if no file in JobFile object."""
        job_file = m.JobFile.objects.create(job=self.job)

        url = reverse('job-file-detail', kwargs={'pk': job_file.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_delete_job_file(self):
        """Job file deleted."""
        job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=self.job
        )

        url = reverse('job-file-detail', kwargs={'pk': job_file.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(m.JobFile.objects.filter(pk=job_file.pk).first(), None)


class AgencyTests(APITestCase):
    """Tests related to the Agency viewset."""

    def setUp(self):
        """Create related objects during initialization."""
        super().setUp()
        self.client_admin = f.create_client_administrator(f.create_client())
        self.client.force_login(self.client_admin)

    def test_get_agencies(self):
        """Should return a list of all Agencies."""
        agency_1 = f.create_agency(name='Test Agency 1')
        agency_2 = f.create_agency(name='Test Agency 2')

        url = reverse('agency-list')
        response = self.client.get(url, {'ordering': 'id'})

        agencies_json = s.AgencyListSerializer(
            [agency_1, agency_2], context={'request': response.wsgi_request}, many=True
        ).data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'], camelize(agencies_json))

    def test_get_agencies_without_agencies(self):
        """Should return an empty list if no Agencies created."""
        url = reverse('agency-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'], [])

    def test_get_agency(self):
        """Should return Agency details."""
        agency = f.create_agency()

        url = reverse('agency-detail', kwargs={'pk': agency.pk})
        response = self.client.get(url)

        agency_json = s.AgencySerializer(
            agency, context={'request': response.wsgi_request},
        ).data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), camelize(agency_json))

    def test_get_agency_without_client(self):
        """Should return 404 status code if not existing pk requested."""
        url = reverse('agency-detail', kwargs={'pk': f.NOT_EXISTING_PK})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_get_agencies_with_superuser(self):
        """Should return 403 once Admin request agencies"""
        admin = f.create_admin()
        self.client.force_login(admin)

        url = reverse('agency-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {'detail': 'You do not have permission to perform this action.'},
        )


def make_serialize_contract(context):
    def serialize_contract(_contract):
        return camelize(s.ContractSerializer(_contract, context=context).data)

    return serialize_contract


class ContractTests(APITestCase):
    """Tests related to the Contract viewset."""

    def setUp(self):
        """Create related objects during initialization."""
        super().setUp()
        self.agency_1 = f.create_agency()
        self.agency_2 = f.create_agency()
        self.client_obj = f.create_client()
        f.create_client_administrator(self.client_obj, 'a@test.com', 'password')
        self.client.login(email='a@test.com', password='password')

    def test_get_contracts(self):
        """Should return a list of all Contracts."""
        contract_1 = f.create_contract(self.agency_1, self.client_obj)
        contract_2 = f.create_contract(self.agency_2, self.client_obj)

        url = reverse('contract-list')
        response = self.client.get(url)
        serialize = make_serialize_contract(response.context)

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.json()['results'], [serialize(contract_2), serialize(contract_1),]
        )

    def test_get_contracts_without_contracts(self):
        """Should return an empty list if not Contracts created."""
        url = reverse('contract-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'], [])

    def test_get_contract(self):
        """Should return Contract details."""
        contract = f.create_contract(self.agency_1, self.client_obj)

        url = reverse('contract-detail', kwargs={'pk': contract.pk})
        response = self.client.get(url)
        serialize = make_serialize_contract(response.context)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), serialize(contract),
        )

    def test_get_contract_without_contract(self):
        """Should return 404 status code if not existing pk requested."""
        url = reverse('contract-detail', kwargs={'pk': f.NOT_EXISTING_PK})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_get_contracts_with_superuser(self):
        """Should return 403 once Admin request contracts"""
        admin = f.create_admin()
        self.client.force_login(admin)

        url = reverse('contract-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {'detail': 'You do not have permission to perform this action.'},
        )


class CandidateFileTests(APITestCase):
    """Tests related to the CandidateFile viewset."""

    def setUp(self):
        """Create Candidate during class initialization."""
        super().setUp()
        self.user = f.create_user('test@test.com', 'password')
        agency = f.create_agency()
        agency.assign_recruiter(self.user)
        self.candidate = f.create_candidate(agency)

        self.client.force_login(self.user)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_upload_candidate_file(self):
        """Should upload the Candidate file."""
        url = reverse(
            'candidate-file-upload', kwargs={'pk': self.candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.post(
            url, data={'file': SimpleUploadedFile('file.txt', b'')}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'detail': 'Candidate file uploaded.'})
        self.candidate.refresh_from_db()
        self.assertNotEqual(self.candidate.photo.file, None)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_upload_candidate_resume(self):
        """Should upload the Candidate resume and call PDFConverter.convert() method."""
        FILE_NAME = 'file.txt'

        with patch.object(PDFConverter, 'convert', return_value=None) as mock_method:
            url = reverse(
                'candidate-file-upload',
                kwargs={'pk': self.candidate.pk, 'ftype': 'resume'},
            )
            response = self.client.post(
                url, data={'file': SimpleUploadedFile(FILE_NAME, b'1010')}
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'detail': 'Candidate file uploaded.'})
            self.candidate.refresh_from_db()
            self.assertNotEqual(self.candidate.resume.file, None)

        mock_method.assert_called()

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_upload_candidate_file_without_file(self):
        """Should not upload a file if no file provided."""
        url = reverse(
            'candidate-file-upload', kwargs={'pk': self.candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'No file in request data.'})

        self.candidate.refresh_from_db()
        with self.assertRaises(ValueError):
            self.candidate.resume.file

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_get_candidate_file(self):
        """Should return Candidate file as an attachment."""
        self.candidate.photo = SimpleUploadedFile('file.txt', b'contents')
        self.candidate.save()

        url = reverse(
            'candidate-file-get', kwargs={'pk': self.candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'contents')
        self.assertTrue(
            response.get('Content-Disposition').startswith('inline; filename="')
        )

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_get_candidate_file_without_file(self):
        """Should return 404 error if no file on Candidate."""
        url = reverse(
            'candidate-file-get', kwargs={'pk': self.candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'File not found.'})

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_delete_candidate_file(self):
        """Should delete Candidate file."""
        self.candidate.photo = SimpleUploadedFile('file.txt', b'contents')
        self.candidate.save()

        url = reverse(
            'candidate-file-delete', kwargs={'pk': self.candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 200)

        self.candidate.refresh_from_db()
        with self.assertRaises(ValueError):
            self.candidate.photo.file

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_delete_candidate_file_without_file(self):
        """Should return 404 error if no file on Candidate."""
        url = reverse(
            'candidate-file-delete', kwargs={'pk': self.candidate.pk, 'ftype': 'photo'}
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'File not found.'})


class CandidateNoteViewSetTests(APITestCase):
    """Tests related to CandidateNoteViewSet."""

    def setUp(self):
        """Create Agency during Candidate test class initialization."""
        super().setUp()
        self.client_obj = f.create_client()
        self.agency = f.create_agency()
        self.recruiter = f.create_recruiter(self.agency)

        self.candidate = f.create_candidate(self.agency)

        job = f.create_job(self.client_obj)
        f.create_proposal(job, self.candidate, self.recruiter)

        self.client.force_login(self.recruiter)

    def test_get_candidate(self):
        """Should return Candidate note."""
        f.create_candidate_note(self.candidate, self.agency, 'Some note')

        url = reverse('candidate-note-detail', kwargs={'pk': self.candidate.pk})
        response = self.client.get(url)

        candidate_json = s.CandidateNoteUpdateSerializer(
            self.candidate, context={'request': response.wsgi_request}
        ).data
        candidate_json['note'] = 'Some note'

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), camelize(candidate_json))

    def test_get_candidate_for_client(self):
        """Should return Candidate note for client user."""
        f.create_candidate_note(self.candidate, self.agency, 'Agency note')
        f.create_candidate_note(self.candidate, self.client_obj, 'Client note')

        client_admin = f.create_client_administrator(self.client_obj)
        self.client.force_login(client_admin)

        url = reverse('candidate-note-detail', kwargs={'pk': self.candidate.pk})
        response = self.client.get(url)

        candidate_json = s.CandidateNoteUpdateSerializer(
            self.candidate, context={'request': response.wsgi_request}
        ).data
        candidate_json['note'] = 'Client note'

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), camelize(candidate_json))

    def test_partial_update_candidate_own_agency(self):
        """Should update Candidate note."""
        data = {'note': 'New note'}
        url = reverse('candidate-note-detail', kwargs={'pk': self.candidate.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.candidate.get_note(self.agency), 'New note')


class ProposalCommentTests(APITestCase):
    """Tests for ProposalComment viewset."""

    def setUp(self):
        """Create the required objects during initialization."""
        super().setUp()
        self.client_obj = f.create_client()
        self.job = f.create_job(self.client_obj)

        self.agency = f.create_agency('Awesome Agency')

        self.recruiter = f.create_recruiter(self.agency)

        f.create_contract(self.agency, self.client_obj)
        self.job.assign_agency(self.agency)
        self.job.assign_member(self.recruiter)
        self.client_admin = f.create_client_administrator(
            self.client_obj, 'a@test.com', 'password'
        )
        self.proposal = f.create_proposal(
            self.job, f.create_candidate(self.agency), self.recruiter
        )

        self.client.force_login(self.client_admin)

    def test_get_proposal_comments(self):
        """Should return a list of Proposal Comments."""
        comment_1 = f.create_proposal_comment(self.client_admin, self.proposal)
        comment_2 = f.create_proposal_comment(self.client_admin, self.proposal)

        url = reverse('proposalcomment-list')
        response = self.client.get(url)

        comments_data = s.ProposalCommentSerializer(
            [comment_2, comment_1],
            context={'request': response.wsgi_request},
            many=True,
        ).data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'], camelize(comments_data))

    def test_get_proposal_comments_without_comments(self):
        """Should return an empty list if no Comments created."""
        url = reverse('proposalcomment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'], [])

    def test_create_proposal_comment(self):
        """Should create Proposal comment."""
        data = {'proposal': self.proposal.pk, 'text': 'Test comment'}
        url = reverse('proposalcomment-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)

    def test_get_proposal_comment(self):
        """Should return Proposal comment details."""
        comment = f.create_proposal_comment(self.client_admin, self.proposal)

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        comment_data = s.ProposalCommentSerializer(
            comment, context={'request': response.wsgi_request}
        ).data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), camelize(comment_data))

    def test_get_proposal_comment_public_system(self):
        """Should return public system Proposal comment details."""
        comment = f.create_proposal_comment(
            self.recruiter, self.proposal, public=True, system=True
        )

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        comment_data = s.ProposalCommentSerializer(
            comment, context={'request': response.wsgi_request}
        ).data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), camelize(comment_data))

    def test_get_proposal_comment_not_public_system(self):
        """Shouldn't return non public Proposal comment details."""
        comment = f.create_proposal_comment(
            self.recruiter, self.proposal, public=False, system=True
        )

        url = reverse('proposalcomment-detail', kwargs={'pk': comment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not found."})

    def test_get_proposal_comment_without_proposal(self):
        """Should return 404 status code if not existing pk requested."""
        url = reverse('proposalcomment-detail', kwargs={'pk': f.NOT_EXISTING_PK})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_get_proposal_comments_with_superuser(self):
        """Should return 403 once Admin request proposal comments"""
        admin = f.create_admin()
        self.client.force_login(admin)

        url = reverse('proposalcomment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {'detail': 'You do not have permission to perform this action.'},
        )

    def create_proposal_and_fetch_it_back(self, receiver, public=False, proposal=None):

        creator = f.create_client_administrator(
            self.client_obj, first_name='John', last_name='Doe'
        )
        data = {
            "proposal": proposal.pk if proposal else self.proposal.pk,
            "text": "Awesome comment",
            "public": public,
        }

        self.client.force_login(creator)
        url = reverse('proposalcomment-list')
        self.client.post(url, data, format='json')

        self.client.force_login(receiver)
        url = reverse('proposalcomment-list')
        response = self.client.get(url)

        return underscoreize(response.json())

    def test_proposal_comment_display_name_by_same_org(self):
        """Inside the organization users should see names of each other"""
        client_admin = f.create_client_administrator(self.client_obj)
        response = self.create_proposal_and_fetch_it_back(client_admin)

        comment = response['results'][0]

        self.assertEqual(comment['author']['first_name'], 'John')
        self.assertEqual(comment['author']['last_name'], 'Doe')

    def test_proposal_comment_display_name_public_comment(self):
        """In shared proposal activity users should see names of each other"""
        response = self.create_proposal_and_fetch_it_back(self.recruiter, public=True)
        comment = response['results'][0]

        self.assertEqual(comment['author']['first_name'], 'John')
        self.assertEqual(comment['author']['last_name'], 'Doe')


@skip("TODO(ZOO-963)")
class NotificationsTests(APITestCase):
    """Tests related to NotificationsViewSet."""

    def setUp(self):
        """Create the required objects during initialization."""
        super().setUp()

        self.user = f.create_user('a@test.com')
        self.client.force_login(self.user)

        self.client_obj = f.create_client()

    def test_mark_all_as_read(self):
        """Should mark all user notifications as read."""
        f.create_notification(
            self.user,
            verb=m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
            actor=self.client_obj,
        )
        f.create_notification(
            self.user,
            verb=m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
            actor=self.client_obj,
        )

        self.assertEqual(self.user.unread_notifications_count, 2)

        url = reverse('notification-mark-all-as-read')
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.unread_notifications_count, 0)

    def test_mark_all_as_read_other_user(self):
        """Should not mark all other User's Notifications as read."""
        user_other = f.create_user()
        f.create_notification(
            user_other,
            verb=m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
            actor=self.client_obj,
        )

        self.assertEqual(user_other.unread_notifications_count, 1)

        url = reverse('notification-mark-all-as-read')
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(user_other.unread_notifications_count, 1)

    def test_mark_as_read(self):
        """Should mark User notification as read."""
        notification = f.create_notification(
            self.user,
            verb=m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
            actor=self.client_obj,
        )

        self.assertEqual(self.user.unread_notifications_count, 1)

        url = reverse('notification-mark-as-read', kwargs={'pk': notification.pk})
        response = self.client.post(url)
        notification.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})
        self.assertFalse(notification.unread)

    def test_mark_as_read_without_notification(self):
        """Should mark User notification as read."""
        url = reverse('notification-mark-as-read', kwargs={'pk': f.NOT_EXISTING_PK})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_get_notifications(self):
        """Should return a list of all Notifications."""
        n = f.create_notification(
            self.user,
            verb=m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
            actor=self.client_obj,
        )

        another_user = f.create_user('b@test.com')
        f.create_notification(
            another_user,
            verb=m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
            actor=self.client_obj,
        )

        url = reverse('notification-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['results'], s.NotificationSerializer([n], many=True).data
        )

    @patch('core.views.jobs.notify_client_updated_job')
    def test_notify_client_updated_job(self, notify_mock):
        client_admin = f.create_client_administrator(self.client_obj)
        job = f.create_job(self.client_obj)

        self.client.force_login(client_admin)

        data = {'title': 'New title'}
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)

        notify_mock.assert_called_once_with(
            client_admin, job, {'title': {'from': job.title, 'to': 'New title'}}
        )

    @patch('core.views.jobs.notify_client_assigned_agency')
    def test_notify_client_assigned_agency(self, notify_mock):
        agency = f.create_agency()
        client_admin = f.create_client_administrator(self.client_obj)
        job = f.create_job(self.client_obj)

        self.client.force_login(client_admin)

        data = {'agencies': [agency.id]}
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)

        notify_mock.assert_called_once_with(
            client_admin, job, {'agencies': {'added': {agency.id}}}
        )

    @patch('core.views.views.notify_client_admin_assigned_manager')
    def test_notify_client_admin_assigned_manager(self, notify_mock):
        client_admin = f.create_client_administrator(self.client_obj)
        manager = f.create_hiring_manager(self.client_obj)
        job = f.create_job(self.client_obj)

        self.client.force_login(client_admin)

        data = {'managers': [manager.id]}
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)

        notify_mock.assert_called_once_with(
            client_admin, job, {'managers': {'added': {manager.id}}}
        )

    @patch('core.views.views.notify_client_admin_assigned_manager')
    def test_notify_client_admin_assigned_manager_endpoint(self, notify_mock):
        client_admin = f.create_client_administrator(self.client_obj)
        manager = f.create_hiring_manager(self.client_obj)
        job = f.create_job(self.client_obj)

        self.client.force_login(client_admin)

        data = {'user': manager.id, 'job': job.id}
        url = reverse('manager-assign')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)

        notify_mock.assert_called_once_with(
            client_admin, job, {'managers': {'added': {manager.id}}}
        )

    @patch('core.views.views.notify_client_created_contract')
    def test_notify_client_created_contract(self, notify_mock):
        agency = f.create_agency()
        client_admin = f.create_client_administrator(self.client_obj)

        self.client.force_login(client_admin)

        data = {'agency': agency.pk, 'client': self.client_obj.pk}
        url = reverse('contract-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)

        notify_mock.assert_called_once_with(
            client_admin,
            m.Contract.objects.filter(agency=agency, client=self.client_obj).first(),
        )

    @patch('core.views.proposals.notify_candidate_proposed_for_job')
    def test_notify_candidate_proposed_for_job(self, notify_mock):
        agency = f.create_agency()
        recruiter = f.create_recruiter(agency)
        candidate = f.create_candidate(agency)

        job = f.get_job_assigned_to_agency(agency)
        job.assign_member(recruiter)

        self.client.force_login(recruiter)

        data = {'job': job.pk, 'candidate': candidate.pk}
        url = reverse('proposal-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)

        notify_mock.assert_called_once_with(
            recruiter, m.Proposal.objects.filter(job=job, candidate=candidate).first()
        )

    @patch('core.views.proposals.notify_candidate_proposed_for_job')
    def test_notify_candidate_proposed_for_multiple_jobs(self, notify_mock):
        agency = f.create_agency()
        recruiter = f.create_recruiter(agency)
        candidate = f.create_candidate(agency)

        jobs = []
        for i in range(5):
            job = f.get_job_assigned_to_agency(agency)
            job.assign_member(recruiter)
            jobs.append(job)

        self.client.force_login(recruiter)

        data = [{'job': job.pk, 'candidate': candidate.pk} for job in jobs]
        url = reverse('proposal-batch-create')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)

        for job in jobs:
            notify_mock.assert_any_call(
                recruiter,
                m.Proposal.objects.filter(job=job, candidate=candidate).first(),
            )

    @patch('core.views.proposals.notify_client_changed_proposal_status')
    def test_notify_client_changed_proposal_status(self, notify_mock):
        agency = f.create_agency()
        recruiter = f.create_recruiter(agency)
        client_admin = f.create_client_administrator(self.client_obj)

        job = f.create_job(self.client_obj)
        job.assign_agency(agency)
        candidate = f.create_candidate(agency)
        proposal = f.create_proposal(job, candidate, recruiter)

        self.client.force_login(client_admin)

        status_before = proposal.status
        expected_next_status = f.get_random_proposal_status(
            m.ProposalStatusGroup.SUITABLE.key
        )

        data = {'status': expected_next_status.id}
        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)

        notify_mock.assert_called_once_with(
            client_admin,
            proposal,
            {'status': {'from': status_before.id, 'to': expected_next_status.id}},
        )

    @patch('core.views.proposals.notify_proposal_moved')
    def test_notify_proposal_moved(self, notify_mock):
        agency = f.create_agency()
        recruiter = f.create_recruiter(agency)
        client_admin = f.create_client_administrator(self.client_obj)

        job = f.create_job(self.client_obj)
        job.assign_agency(agency)

        another_job = f.create_job(self.client_obj)
        another_job.assign_agency(agency)

        candidate = f.create_candidate(agency)
        proposal = f.create_proposal(job, candidate, recruiter)

        self.client.force_login(client_admin)

        data = {'job': another_job.id}
        url = reverse('proposal-move-to-job', kwargs={'pk': proposal.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)

        notify_mock.assert_called_once_with(client_admin, proposal)


class RegistrationCheckEmailViewTests(APITestCase):
    """RegistrationCheckEmailView tests."""

    def setUp(self):
        """Create fixtures."""
        super().setUp()

        self.agency = f.create_agency()
        self.agency.email_domain = 'agency.com'
        self.agency.save()

    def test_check_email_agency(self):
        """Should return OK."""
        email = 'recruiter@agency.com'
        url = reverse('registration-check-email')
        data = {'type': 'agency', 'email': email}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {'type': 'agency', 'email': email, 'agencyExists': True}
        )

    def test_check_email_client(self):
        """Should return OK."""
        email = 'someone@client.com'
        url = reverse('registration-check-email')
        data = {'type': 'client', 'email': email}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {'type': 'client', 'email': email, 'agencyExists': False}
        )

    def test_check_email_client_agency_exists(self):
        """Should return error for client."""
        email = 'someone@agency.com'
        url = reverse('registration-check-email')
        data = {'type': 'client', 'email': email}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 400)

    def test_check_email_no_agency(self):
        """Should return agencyExists False."""
        email = 'recruiter@another.com'
        url = reverse('registration-check-email')
        data = {'type': 'agency', 'email': email}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {'type': 'agency', 'email': email, 'agencyExists': False}
        )


class RecruiterRegistrationViewTests(APITestCase):
    """RecruiterRegistrationView tests."""

    def setUp(self):
        """Create fixtures."""
        super().setUp()

        self.agency = f.create_agency()
        self.agency.email_domain = 'agency.com'
        self.agency.save()

    def test_register(self):
        """Should create recruiter for agency."""
        email = 'recruiter@agency.com'
        url = reverse('recruiter-registration-register')
        data = {
            'email': email,
            'first_name': 'John',
            'last_name': 'Smith',
            'password': '7*&^&zkd',
            'terms_of_service': 1,
            'country': 'jp',
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)

        user = m.User.objects.filter(email=email).first()
        self.assertIsNotNone(user)

        self.assertEqual(user.on_activation_action, 'make_user_agency_admin')
        self.assertEqual(user.on_activation_params['agency_id'], self.agency.id)

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]

        self.assertIn(email, message.to)
        self.assertIn('/account/activate/', message.body)

    def test_register_invalid(self):
        """Should not create recruiter."""
        email = 'recruiter@another.com'
        url = reverse('recruiter-registration-register')
        data = {
            'email': email,
            'first_name': 'John',
            'last_name': 'Smith',
            'terms_of_service': 1,
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 400)

        user = m.User.objects.filter(email=email).first()
        self.assertIsNone(user)


class ActivateAccountViewTests(APITestCase):
    """ActivateAccountView tests."""

    def test_token_generation(self):
        """Should generate valid token."""

        user = f.create_user('test@test.com')
        user.is_activated = False
        user.save()

        token = get_activation_token(user)
        unsigned_user = get_user_from_activation_token(token)

        self.assertEqual(user, unsigned_user)

    def test_get_user_from_activation_token(self):
        """Should not return already activated user."""

        user = f.create_user('test@test.com')
        user.is_activated = True
        user.save()

        token = get_activation_token(user)
        unsigned_user = get_user_from_activation_token(token)
        self.assertIsNone(unsigned_user)

    @patch('core.views.user_activate_account.activate_user')
    def test_activate_user(self, activate_user_mock):
        """Should activate user."""

        user = f.create_user('test@test.com')
        user.is_activated = False
        user.save()

        token = get_activation_token(user)

        url = reverse('activate-account')
        data = {'token': token}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        activate_user_mock.assert_called_with(user)

    @patch('core.views.user_activate_account.activate_user')
    def test_activate_user_invalid_token(self, activate_user_mock):
        """Should not activate user."""

        user = f.create_user('test@test.com')
        user.is_activated = False
        user.save()

        with patch('core.views.user_activate_account.ACTIVATION_TOKEN_SALT', 'invalid'):
            token = get_activation_token(user)

        url = reverse('activate-account')
        data = {'token': token}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 403)
        activate_user_mock.assert_not_called()


class LocaleViewSetTests(APITestCase):
    """LocaleViewSet tests."""

    def test_ok(self):
        """Should return OK."""
        url = reverse('locale-get-locale')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_returns_custom_proposal_statuses_for_client_members(self):
        """Should return custom proposal statuses for client members."""
        client = f.create_client()
        client_admin = f.create_client_administrator(client)
        self.client.force_login(client_admin)

        url = reverse('locale-get-locale')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('proposalShortlistStatuses' in response.json())
        self.assertTrue(response.json()['proposalShortlistStatuses'])


class CandidateLinkedinDataViewSetTests(APITestCase):
    """CandidateLinkedinDataViewSet tests."""

    def setUp(self):
        self.agency = f.create_agency()
        self.candidate = f.create_candidate(self.agency)
        self.data = f.create_candidate_linkedin_data(self.candidate)
        self.recruiter = f.create_recruiter(self.agency)
        self.client.force_login(self.recruiter)

    def test_get_candidate_data(self):
        url = reverse(
            'candidatelinkedindata-get-candidate-data', kwargs={'pk': self.data.id}
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        candidate_data = s.CandidateSerializer(
            instance=self.candidate, context={'request': response.wsgi_request}
        ).data

        self.assertDictEqual(
            candidate_data, underscoreize(response.json().get('candidate'))
        )
        self.assertDictEqual(
            LinkedinProfile(self.data.data).candidate_data,
            underscoreize(response.json().get('patchData')),
        )


class DashboardViewSetTests(APITestCase):
    def setUp(self):
        self.client_obj = f.create_client()
        self.client_admin = f.create_client_administrator(self.client_obj)
        self.client.force_login(self.client_admin)

    def test_dashboard_get_statistics(self):
        """Should return required keys and values shouldn't be None."""
        url = reverse('dashboard-get-statistics')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        required_keys = {
            'total_candidates_submitted',
            'pending_cv_review',
            'interviewing',
            'offer_stage',
            'wins',
            'live_jobs',
        }

        self.assertEqual(required_keys, set(response.data))
        self.assertTrue(None not in response.data.values())


class ZohoViewSetTests(APITestCase):
    def setUp(self):
        self.agency = f.create_agency()
        self._client = f.create_client()
        self.recruiter = f.create_recruiter(self.agency)
        self.client_admin_associate = f.create_client_administrator(self._client)
        self.client.force_login(self.recruiter)

    @patch('core.zoho.get_zoho_candidate_data')
    @patch('core.zoho.get_zoho_candidate_tabular_data')
    def import_candidate(
        self, user, get_zoho_candidate_tabular_data_mock, get_zoho_candidate_data_mock,
    ):
        get_zoho_candidate_data_mock.return_value = f.ZOHO_CANDIDATE_DATA
        get_zoho_candidate_tabular_data_mock.return_value = f.ZOHO_TABULAR_DATA

        url = reverse('zoho-get-candidate')

        zoho_candidate_url = (
            'https://recruit.zoho.com/recruit/EntityInfo.do?' 'module=Candidates&id=123'
        )

        getResponse = self.client.post(url, {'url': zoho_candidate_url}, format='json')
        self.assertEqual(getResponse.status_code, 200, msg=getResponse.data)

        saveResponse = self.client.post(
            path=reverse('zoho-save-candidate'),
            data=getResponse.content,
            content_type='application/json',
        )
        self.assertEqual(saveResponse.status_code, 200, msg=getResponse.data)

        candidate = m.Candidate.objects.filter(id=saveResponse.json()['id']).first()

        candidate_json = s.CandidateSerializer(
            candidate, context={'request': getResponse.wsgi_request}
        ).data
        self.assertCountEqual(saveResponse.data, candidate_json)

    def test_import_zoho_candidate_by_agency(self):
        self.import_candidate(self.recruiter)

    def test_import_zoho_candidate_by_client(self):
        self.client.force_login(self.client_admin_associate)
        self.import_candidate(self.client_admin_associate)

    def test_import_candidate_invalid_url(self):
        url = reverse('zoho-get-candidate')

        zoho_candidate_url = 'https://localhost'

        response = self.client.post(url, {'url': zoho_candidate_url}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertTrue('url' in response.data)

    @patch('core.views.views.get_zoho_candidate')
    def test_import_candidate_error(self, get_zoho_candidate_mock):
        get_zoho_candidate_mock.side_effect = ZohoImportError('Error!')

        url = reverse('zoho-get-candidate')

        zoho_candidate_url = (
            'https://recruit.zoho.com/recruit/EntityInfo.do?' 'module=Candidates&id=123'
        )

        response = self.client.post(url, {'url': zoho_candidate_url}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], 'Error!')


class FeedbackTests(APITestCase):
    def setUp(self):
        user = f.create_client_administrator(f.create_client())
        self.client.force_login(user)

    def test_create_feedback(self):
        """Should create feedback instance"""
        url = reverse('feedback-list')
        data = f.DEFAULT_FEEDBACK

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(underscoreize(response.json()), data)
        self.assertTrue(m.Feedback.objects.exists())

    def test_create_feedback_missing_data(self):
        """All the field must be provided"""
        url = reverse('feedback-list')
        data = f.DEFAULT_FEEDBACK
        data.pop('text')

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'text': ['This field is required.']})


class GetPublicJobFiles(APITestCase):
    @patch('core.signals.convert_job_file.delay')
    # mock task call to prevent triggering conversion unnecessary
    def setUp(self, *args):
        self.client_org = f.create_client()
        self.agency_org = f.create_agency()
        self.job = f.create_job(self.client_org, public=True)
        self.job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=self.job
        )

        self.non_public_job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'wrong'),
            job=f.create_job(self.client_org),
        )
        self.users = [
            None,
            f.create_client_administrator(self.client_org),
            f.create_hiring_manager(self.client_org),
            f.create_agency_administrator(self.agency_org),
            f.create_recruiter(self.agency_org),
            f.create_agency_manager(self.agency_org),
        ]

    def get_url(self, pk=None, uuid=None):
        return reverse(
            'job-file-get-public',
            kwargs={
                'pk': pk or self.job_file.pk,
                'uuid': uuid or self.job_file.job.public_uuid,
            },
        )

    def assert_not_found(self, response):
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), f.NOT_FOUND)

    def test_correct(self):
        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'contents')

    def test_wrong_job_id(self):
        self.assert_not_found(
            self.client.get(self.get_url(uuid='b4f66f24-f025-4448-bc55-823c11728ad6'))
        )

    def test_wrong_file_id(self):
        self.assert_not_found(
            self.client.get(self.get_url(pk=self.non_public_job_file.pk))
        )

    def test_permissions(self):
        for user in self.users:
            if user:
                self.client.force_login(user)

            response = self.client.get(self.get_url())

            self.assertEqual(
                response.status_code,
                200,
                msg='{0} has no access'.format(
                    str(user.profile) if user else 'Anonymous User'
                ),
            )

            self.client.logout()


class AgencyClientInfoTests(APITestCase):
    def setUp(self):
        self.agency = f.create_agency()
        self.client_obj = f.create_client()  # has a contract with agency

        self.client_obj_2 = f.create_client()  # doesn't have a contract with agency

        self.agency_client = f.create_client()
        self.agency_client.owner_agency = self.agency
        self.agency_client.save()  # created by agency

        self.request_data = {
            'industry': m.Industry.CONSULTING.key,
            'type': m.ClientType.KEY_ACCOUNT.key,
        }

        f.create_contract(self.agency, self.client_obj)

        self.agency_admin = f.create_agency_administrator(self.agency)
        self.client_admin = f.create_client_administrator(self.client_obj)

    def test_attach_info(self):
        """Agency should be able to attach info to the Client."""
        self.client.force_login(self.agency_admin)
        response = self.client.patch(
            reverse('agency_client_info-detail', kwargs={'client': self.client_obj.pk}),
            self.request_data,
            format='json',
        )
        agency_client_info = m.AgencyClientInfo.objects.filter(
            agency=self.agency, client=self.client_obj
        ).first()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            agency_client_info.industry, m.Industry.CONSULTING.key,
        )
        self.assertEqual(agency_client_info.type, m.ClientType.KEY_ACCOUNT.key)

    def test_attach_info_own_client(self):
        """Agency should be able to attach info to the Client that was created by the Agency"""
        self.client.force_login(self.agency_admin)
        response = self.client.patch(
            reverse(
                'agency_client_info-detail', kwargs={'client': self.agency_client.pk}
            ),
            self.request_data,
            format='json',
        )
        agency_client_info = m.AgencyClientInfo.objects.filter(
            agency=self.agency, client=self.agency_client
        ).first()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            agency_client_info.industry, m.Industry.CONSULTING.key,
        )
        self.assertEqual(agency_client_info.type, m.ClientType.KEY_ACCOUNT.key)

    def test_attach_info_no_access(self):
        """Agency can't attach info to the Client it has no access to."""
        self.client.force_login(self.agency_admin)
        response = self.client.patch(
            reverse(
                'agency_client_info-detail', kwargs={'client': self.client_obj_2.pk}
            ),
            self.request_data,
            format='json',
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_attach_info_client_to_itself(self):
        """Client can't attach info to itself."""
        self.client.force_login(self.client_admin)
        response = self.client.patch(
            reverse('agency_client_info-detail', kwargs={'client': self.client_obj.pk}),
            self.request_data,
            format='json',
        )

        self.assertEqual(response.status_code, 403)

    def test_attach_info_client_to_other_client(self):
        """Client can't attach info to other Client"""
        self.client.force_login(self.client_admin)
        response = self.client.patch(
            reverse(
                'agency_client_info-detail', kwargs={'client': self.client_obj_2.pk}
            ),
            self.request_data,
            format='json',
        )

        self.assertEqual(response.status_code, 403)

    def test_update_attached_info(self):
        """Agencies may updated attached info"""
        agency = f.create_agency()
        client = f.create_client()
        f.create_contract(agency, client)

        agency_admin = f.create_agency_administrator(agency)

        agency_client_info = m.AgencyClientInfo.objects.create(
            agency=agency, client=client
        )

        self.client.force_login(agency_admin)
        response = self.client.patch(
            reverse('agency_client_info-detail', kwargs={'client': client.pk}),
            self.request_data,
            format='json',
        )
        agency_client_info.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            agency_client_info.industry, m.Industry.CONSULTING.key,
        )
        self.assertEqual(agency_client_info.type, m.ClientType.KEY_ACCOUNT.key)

    def test_retrieve_attached_info(self):
        """Agencies should be able to get info they attached to the Client"""
        agency = f.create_agency()
        client = f.create_client()
        f.create_contract(agency, client)

        agency_admin = f.create_agency_administrator(agency)

        m.AgencyClientInfo.objects.create(
            agency=agency, client=client, originator=agency_admin,
        )

        self.client.force_login(agency_admin)
        response = self.client.get(
            reverse('agency_client_info-detail', kwargs={'client': client.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            underscoreize(response.json()),
            {
                'industry': '',
                'type': '',
                'originator': agency_admin.pk,
                'info': '',
                'notes': '',
                'account_manager': None,
                'updated_at': response.json()['updatedAt'],
                'updated_by': None,
                'billing_address': '',
                'portal_url': '',
                'portal_login': '',
                'portal_password': '',
                'primary_contact_number': '',
                'website': '',
            },
        )
