"""Tests related to models of the core Django app."""
import tempfile
from unittest.case import skip
import uuid
from enum import Enum
from unittest.mock import patch, PropertyMock

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.db.models.query import QuerySet
from django.db.utils import DataError, IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.exceptions import ValidationError

from core.utils import parse_linkedin_slug
from core import fixtures as f
from core import factories as fa
from core import models as m


class UserManagerTests(TestCase):
    """Tests related to the UserManager class."""

    def setUp(self):
        """Create a UserManager during setup process."""
        self.manager = m.UserManager()
        self.manager.contribute_to_class(model=m.User, name='User')

    def test_create_user_without_email(self):
        """Should raise a ValueError if not email provided."""
        msg = 'The given email must be set'
        with self.assertRaisesRegex(ValueError, msg):
            self.manager._create_user(email=None, password='password')

    def test_create_user_defaults(self):
        """User is not staff and is not a superuser."""
        user = self.manager.create_user(
            email='test@localhost', first_name='super', last_name='user'
        )
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    @patch('core.models.UserManager._create_user')
    def test_create_user_called__create_user(self, create_user_mock):
        """Called _create_user when create_user called."""
        self.manager.create_user(email='test@localhost')
        self.assertTrue(create_user_mock.called)

    def test_create_superuser_defaults(self):
        """User is staff and is a superuser."""
        user = self.manager.create_superuser(
            email='test@localhost',
            password='p@ssw0rd',
            first_name='super',
            last_name='user',
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_superuser_is_staff_false(self):
        """Value Error raised if is_staff set to False."""
        msg = 'Superuser must have is_staff=True.'
        with self.assertRaisesRegex(ValueError, msg):
            self.manager.create_superuser(
                email='test@localhost', password='p@ssw0rd', is_staff=False
            )

    def test_create_superuser_is_superuser_false(self):
        """Value Error raised if is_superuser set to False."""
        msg = 'Superuser must have is_superuser=True.'
        with self.assertRaisesRegex(ValueError, msg):
            self.manager.create_superuser(
                email='test@localhost', password='p@ssw0rd', is_superuser=False
            )

    @patch('core.models.UserManager._create_user')
    def test_create_superuser_called__create_user(self, create_user_mock):
        """Called _create_user when create_superuser called."""
        self.manager.create_superuser(email='test@localhost', password='p@ssw0rd')
        self.assertTrue(create_user_mock.called)


class UserTests(TestCase):
    """Tests related to the User model."""

    def test_user_created(self):
        """User successfully created."""
        user = f.create_user()

        self.assertEqual(m.User.objects.get(pk=user.pk), user)

    def test_unread_notifications_count(self):
        """Should return number of unread notifications for User."""
        agency = f.create_agency()
        client = f.create_client()
        user = f.create_recruiter(agency)
        for i in range(3):
            f.create_notification(
                user, m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT, actor=client,
            )

        another_client = f.create_client()
        another_user = f.create_recruiter(agency)
        for i in range(2):
            f.create_notification(
                another_user,
                m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
                actor=another_client,
            )

        self.assertEqual(user.unread_notifications_count, 3)

    def test_profile_none(self):
        """Default profile is None."""
        user = f.create_user()

        self.assertIsNone(user.profile)

    def test_profile_of_agency_administrator(self):
        """Profile property returns related Agency Administrator profile."""
        user = f.create_user()
        agency = f.create_agency()
        aa = m.AgencyAdministrator.objects.create(agency=agency, user=user)

        self.assertEqual(user.profile, aa)

    def test_profile_of_agency_manager(self):
        """Profile property returns related Agency Manager profile."""
        user = f.create_user()
        agency = f.create_agency()
        am = m.AgencyManager.objects.create(agency=agency, user=user)

        self.assertEqual(user.profile, am)

    def test_profile_of_recruiter(self):
        """Profile property returns related Recruiter profile."""
        user = f.create_user()
        agency = f.create_agency()
        recruiter = m.Recruiter.objects.create(agency=agency, user=user)

        self.assertEqual(user.profile, recruiter)

    def test_profile_of_talentassociate(self):
        """Profile property returns related Client Administrator profile."""
        user = f.create_user()
        client = f.create_client()
        client_admin = m.ClientAdministrator.objects.create(client=client, user=user)

        self.assertEqual(user.profile, client_admin)

    def test_profile_of_hiringmanager(self):
        """Profile property returns related Hiring Manager profile."""
        user = f.create_user()
        client = f.create_client()
        hiring_manager = m.ClientStandardUser.objects.create(client=client, user=user)

        self.assertEqual(user.profile, hiring_manager)

    def test_mutiple_profiles(self):
        """Should raise an AttributeError when User has multiple profiles."""
        user = f.create_user()
        agency = f.create_agency()
        m.Recruiter.objects.create(agency=agency, user=user)
        m.AgencyAdministrator.objects.create(agency=agency, user=user)

        message = 'User have more than 1 profile.'
        with self.assertRaisesMessage(AttributeError, message):
            user.profile

    def test_str(self):
        """User string representation should contain its email."""
        user = f.create_user(email='user@test.com')

        self.assertEqual(str(user), 'user@test.com')

    def test_full_name(self):
        """Full name property should equal to the result of the method."""
        user = f.create_user(
            first_name='Test', last_name='User', email='test@localhost'
        )

        self.assertEqual(user.full_name, user.get_full_name())

    def test_username(self):
        """User model has no username field."""
        self.assertIsNone(m.User.username)

    @skip("TODO(ZOO-977)")
    def test_notifications_defaults(self):
        """All notifications should be enabled by default."""
        user = f.create_user()

        self.assertTrue(user.email_notifications)
        self.assertTrue(user.email_candidate_shortlisted_for_job)
        self.assertTrue(user.email_candidate_longlisted_for_job)
        self.assertTrue(user.email_talent_assigned_manager_for_job)
        self.assertTrue(user.email_client_created_contract)
        self.assertTrue(user.email_client_assigned_agency_for_job)
        self.assertTrue(user.email_client_updated_job)
        self.assertTrue(user.email_client_changed_proposal_status)
        self.assertTrue(user.email_proposal_moved)

    def test_email_unique(self):
        """Integrity Error raised when creating User with same email."""
        email = 'test@localhost'
        f.create_user(email=email)

        with self.assertRaises(ValidationError) as e:
            f.create_user(email=email)
            self.assertEqual(
                e.message_dict,
                {'email': ['User with this Email address already exists.']},
            )


class ProfileMixinTests(TestCase):
    """Tests related to the ProfileMixin abstract model."""

    def test_apply_candidates_filter(self):
        """Should raise a NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            m.ProfileMixin().apply_candidates_filter(m.Candidate.objects.all())

    def test_apply_jobs_filter(self):
        """Should raise a NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            m.ProfileMixin().apply_jobs_filter(m.Job.objects.all())

    def test_apply_job_files_filter(self):
        """Should raise a NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            m.ProfileMixin().apply_job_files_filter(m.JobFile.objects.all())

    @patch('core.models.ProfileMixin.apply_jobs_filter')
    def test_apply_job_files_filter_called_job_filter(self, mock):
        """Should call jobs filter."""
        mock.return_value = []
        m.ProfileMixin().apply_job_files_filter(m.JobFile.objects.all())
        mock.assert_called()

    def test_apply_proposals_filter(self):
        """Should raise a NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            m.ProfileMixin().apply_proposals_filter([])

    def test_contracts_filter(self):
        """Should raise a NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            m.ProfileMixin().contracts_filter

    def test_org(self):
        """Should raise a NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            m.ProfileMixin().org

    @skip("TODO(ZOO-977)")
    def test_notification_types(self):
        """Should raise a NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            m.ProfileMixin().notification_types

    @skip('TODO(ZOO-963)')
    @patch('core.models.ProfileMixin.user', new_callable=PropertyMock)
    @patch('core.models.ProfileMixin.notification_types', new_callable=PropertyMock)
    def test_represent_notification_types(self, mock_obj, mock_user):
        """Should represent Notification type ready for serialization."""
        mock_obj.return_value = Enum(
            'Test',
            [
                (
                    'TEST_NAME',
                    m.NotificationType('email_test_name', 'Setting Label', 'Text'),
                )
            ],
        )
        mock_user.return_value = None

        self.assertEqual(
            m.ProfileMixin().represent_notification_types(),
            [
                {
                    'name': 'test_name',
                    'description': 'Setting Label',
                    'user_field': 'emailTestName',
                    'user_field_enabled': None,
                }
            ],
        )

    @skip('TODO(ZOO-963)')
    @patch('core.models.ProfileMixin.user', new_callable=PropertyMock)
    @patch('core.models.ProfileMixin.notification_types', new_callable=PropertyMock)
    def test_represent_notification_types_with_user_field(self, mock_obj, mock_user):
        """User field enabled should be True if exists on User."""
        mock_obj.return_value = Enum(
            'Test',
            [
                (
                    'TEST_NAME',
                    m.NotificationType('email_test_name', 'Setting Label', 'Text'),
                )
            ],
        )

        class MockUser:
            @property
            def email_test_name(self):
                return True

        mock_user.return_value = MockUser()

        self.assertEqual(
            m.ProfileMixin().represent_notification_types(),
            [
                {
                    'name': 'test_name',
                    'description': 'Setting Label',
                    'user_field': 'emailTestName',
                    'user_field_enabled': True,
                }
            ],
        )

    def test_can_create_proposal(self):
        """Should raise a NotImplementedError.

        This exception propagates from org property of the
        ProfileMixin which is not defined for this class.
        """
        with self.assertRaises(NotImplementedError):
            m.ProfileMixin().can_create_proposal(
                f.create_job(f.create_client()), f.create_candidate(f.create_agency()),
            )

    def test_deleted_with_user(self):
        """Profile deleted when User is deleted."""
        user = f.create_user()
        # Some non abstract model
        m.ClientAdministrator.objects.create(client=f.create_client(), user=user)
        user.delete()

        self.assertEqual(m.ClientAdministrator.objects.count(), 1)


class AgencyRegistrationRequestTests(TestCase):
    """Tests related to the AgencyRegistrationRequest model."""

    def setUp(self):
        """Create a User during object set up."""
        super().setUp()
        self.user = f.create_user(email='testuser@localhost')

    def test_agency_registration_request_created(self):
        """Agency registration request successfully created."""
        request = m.AgencyRegistrationRequest.objects.create(
            ip='1.1.1.1', headers='', name='Test', user=self.user, created=False
        )

        self.assertEqual(
            m.AgencyRegistrationRequest.objects.get(pk=request.pk), request
        )

    def test_agency_registration_request_name_len_129(self):
        """Agency registration request not created with name length 129."""
        with self.assertRaises(DataError):
            m.AgencyRegistrationRequest.objects.create(
                ip='1.1.1.1', headers='', name='a' * 129, user=self.user, created=False
            )

    def test_agency_registration_request_created_default(self):
        """Agency registration request created default value is false."""
        request = m.AgencyRegistrationRequest.objects.create(
            ip='1.1.1.1', headers='{}', name='Test', user=self.user
        )

        self.assertFalse(request.created)

    def test_agency_registration_request_str(self):
        """Agency registration request string should contain the name."""
        request = m.AgencyRegistrationRequest.objects.create(
            ip='1.1.1.1', headers='{}', name='Test', user=self.user, created=False
        )

        self.assertEqual(
            str(request), 'Agency Registration Request #{} "Test"'.format(request.pk)
        )

    def test_deleted_with_user(self):
        """Registration request deleted with the User."""
        user = f.create_user()
        m.AgencyRegistrationRequest.objects.create(
            ip='1.1.1.1', headers='', name='Test', user=user, created=False
        )
        user.delete()

        self.assertEqual(m.AgencyRegistrationRequest.objects.count(), 0)

    def test_approved(self):
        """Should create an agency and assign user as recruiter."""
        user = f.create_user('a@test.com')
        r = m.AgencyRegistrationRequest.objects.create(
            ip='1.1.1.1', headers='', name='Test', user=user,
        )
        agency = r.approve()
        self.assertTrue(r.created)
        self.assertEqual(agency.name, r.name)
        self.assertEqual(type(user.profile), m.AgencyAdministrator)
        self.assertEqual(user.agencyadministrator.agency, agency)

    def test_approved_via_job(self):
        """Should create contract between created agency and job's client."""
        client = f.create_client()
        job = f.create_job(client)
        user = f.create_user('a@test.com')
        agency_registration_request = m.AgencyRegistrationRequest.objects.create(
            ip='1.1.1.1', headers='', name='Test', user=user, via_job=job
        )
        agency = agency_registration_request.approve()

        self.assertTrue(agency.contracts.filter(client=client).count())
        self.assertTrue(job.agencies.filter(id=agency.id).count())


class ClientRegistrationRequestTests(TestCase):
    """Tests related to the ClientRegistrationRequest model."""

    def setUp(self):
        """Create a User during object set up."""
        super().setUp()
        self.user = f.create_user(email='testuser@localhost')

    def test_client_registration_request_created(self):
        """Agency registration request successfully created."""
        request = m.ClientRegistrationRequest.objects.create(
            ip='1.1.1.1', headers='{}', name='Test', user=self.user, created=False
        )

        self.assertEqual(
            m.ClientRegistrationRequest.objects.get(pk=request.pk), request
        )

    def test_client_registration_request_name_len_129(self):
        """Client registration request not created with name length 129."""
        with self.assertRaises(DataError):
            m.ClientRegistrationRequest.objects.create(
                ip='1.1.1.1', headers='', name='a' * 129, user=self.user, created=False
            )

    def test_client_registration_request_created_default(self):
        """Client registration request created default value is false."""
        request = m.ClientRegistrationRequest.objects.create(
            ip='1.1.1.1', headers='{}', name='Test', user=self.user
        )

        self.assertFalse(request.created)

    def test_client_registration_request_str(self):
        """Agency registration request string should contain the name."""
        request = m.ClientRegistrationRequest.objects.create(
            ip='1.1.1.1', headers='{}', name='Test', user=self.user, created=False
        )

        self.assertEqual(
            str(request), 'Client Registration Request #{} "Test"'.format(request.pk)
        )

    def test_deleted_with_user(self):
        """Registration request deleted with the User."""
        user = f.create_user()
        m.ClientRegistrationRequest.objects.create(
            ip='1.1.1.1', headers='{}', name='Test', user=user, created=False
        )
        user.delete()

        self.assertEqual(m.ClientRegistrationRequest.objects.count(), 0)


class OrganizationMixinTests(TestCase):
    """Tests related to the OrganizationMixin abstract model."""

    def test_candidates_filter(self):
        """Should raise a NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            m.OrganizationMixin().members


class ClientTests(TestCase):
    """Tests related to the Client model."""

    def test_client_created(self):
        """Client successfully created."""
        client = m.Client.objects.create(name='Test', primary_contact=f.create_user())

        self.assertEqual(m.Client.objects.get(pk=client.pk), client)

    def test_client_created_with_default_proposal_statuses(self):
        """Client's default proposal statuses are created."""
        client = m.Client.objects.create(name='Test', primary_contact=f.create_user())
        proposal_statuses_count = client.proposal_statuses.count()

        self.assertTrue(proposal_statuses_count > 0)
        self.assertEqual(
            proposal_statuses_count,
            m.ProposalStatus.objects.filter(default=True,)
            .exclude(group__in=m.LONGLIST_PROPOSAL_STATUS_GROUPS)
            .count(),
        )

    def test_client_name_length_128(self):
        """Client successfully created when the name is 128 length."""
        client = m.Client.objects.create(
            name='a' * 128, primary_contact=f.create_user()
        )

        self.assertEqual(m.Client.objects.get(pk=client.pk), client)

    def test_client_name_length_129(self):
        """Validation Error raised when the name is more than 128 length."""
        with self.assertRaises(ValidationError) as e:
            f.create_client(name='a' * 129)
            self.assertEqual(
                e.message_dict,
                {
                    'name': [
                        'Ensure this value has at most 128 characters (it has 129).'
                    ]
                },
            )

    def test_client_str(self):
        """Client string representation should contain its pk and name."""
        client = m.Client.objects.create(
            name='Test Client', primary_contact=f.create_user()
        )

        self.assertEqual(str(client), '{} - Test Client'.format(client.pk))

    def test_assign_administrator_profile_created(self):
        """Client Administrator profile created when User assigned."""
        user = f.create_user()
        client = f.create_client(primary_contact=user)
        client.assign_administrator(user)

        self.assertTrue(m.ClientAdministrator.objects.filter(user=user).exists())

    def test_assign_administrator_added_to_group(self):
        """User added to the Client Administrators group when they assigned."""
        user = f.create_user()
        client = f.create_client(primary_contact=user)
        client.assign_administrator(user)

        self.assertTrue(user.groups.filter(name='Client Administrators').exists())

    def test_assign_standard_user_profile_created(self):
        """Hiring Manager profile created when User assigned."""
        user = f.create_user()
        client = f.create_client(primary_contact=user)
        client.assign_standard_user(user)

        self.assertTrue(m.ClientStandardUser.objects.filter(user=user).exists())

    def test_assign_standard_user_added_to_group(self):
        """User added to the Client Standard Users group when they assigned."""
        user = f.create_user()
        client = f.create_client(primary_contact=user)
        client.assign_standard_user(user)

        self.assertTrue(user.groups.filter(name='Client Standard Users').exists())

    def test_members(self):
        """Should return members of Client organization."""
        client_admin = f.create_user()
        client = f.create_client(primary_contact=client_admin)
        client.assign_administrator(client_admin)
        hiring_manager = f.create_hiring_manager(client)

        another_client_admin = f.create_user()
        another_client = f.create_client(primary_contact=another_client_admin)
        another_client.assign_administrator(another_client_admin)
        f.create_client_administrator(another_client)
        f.create_hiring_manager(another_client)

        agency_admin = f.create_user()
        agency = f.create_agency(primary_contact=agency_admin)
        agency.assign_agency_administrator(agency_admin)
        f.create_agency_manager(agency)
        f.create_recruiter(agency)

        self.assertEqual(
            {i.pk for i in client.members.all()}, {client_admin.pk, hiring_manager.pk},
        )

    def test_featured(self):
        """Client can't be featured organization"""
        client = f.create_client()
        self.assertFalse(hasattr(client, 'enable_researcher_field_feature'))


class ClientAdministratorTests(TestCase):
    """Tests related to the ClientAdministrator model."""

    def setUp(self):
        """Create the required objects during the initialization."""
        super().setUp()
        self.user = f.create_user()
        self.client = f.create_client(primary_contact=self.user)

        self.agency = f.create_agency()
        self.recruiter = f.create_recruiter(self.agency)

    def test_talentassociate_created(self):
        """Client Administrator successfully created."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )

        self.assertEqual(
            m.ClientAdministrator.objects.get(pk=client_admin.pk), client_admin
        )

    def test_talentassociate_without_client(self):
        """Integrity Error raised when no Client passed."""
        with self.assertRaises(IntegrityError):
            m.ClientAdministrator.objects.create(user=self.user)

    def test_talentassociate_without_user(self):
        """Integrity Error raised when no User passed."""
        with self.assertRaises(IntegrityError):
            m.ClientAdministrator.objects.create(client=self.client)

    def test_talentassociate_str(self):
        """Client Administrator string representation contains Client name."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )

        self.assertEqual(
            str(client_admin), 'Client Administrator of "{}"'.format(self.client.name)
        )

    def test_own_candidates_filter(self):
        """Own Candidate linked via Proposal should be in own candidates."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )

        candidate = f.create_candidate(self.client)
        job = f.create_job(self.client)
        f.create_proposal(job, candidate, self.user)

        self.assertTrue(
            candidate
            in client_admin.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_own_candidates_filter_agency(self):
        """Candidate linked via Proposal should not be in own candidates."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )

        candidate = f.create_candidate(self.agency)
        job = f.create_job(self.client)
        f.create_proposal(job, candidate, self.recruiter)

        self.assertFalse(
            candidate
            in client_admin.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_own_candidates_filter_other_client(self):
        """Candidate linked to other Client should not be in own candidates."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )

        client_other = f.create_client()
        candidate = f.create_candidate(client_other)
        job_other = f.create_job(client_other)
        f.create_proposal(job_other, candidate, self.recruiter)

        self.assertFalse(
            candidate
            in client_admin.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter(self):
        """Candidate linked via Proposal should be in candidates."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )

        candidate = f.create_candidate(self.agency)
        job = f.create_job(self.client)
        f.create_proposal(job, candidate, self.recruiter)

        self.assertTrue(
            candidate in client_admin.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter_with_proposal(self):
        """Candidate linked via Proposal should be in candidates."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )

        candidate = f.create_candidate(self.client)
        job = f.create_job(self.client)
        f.create_proposal(job, candidate, self.recruiter)

        self.assertTrue(
            candidate in client_admin.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter_without_proposal(self):
        """Candidate not linked via Proposal should not be in candidates."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )
        candidate = f.create_candidate(self.agency)

        self.assertFalse(
            candidate in client_admin.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter_other_client(self):
        """Candidate linked to other Client should not be in candidates."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )

        candidate = f.create_candidate(self.agency)
        client_other = f.create_client()
        job_other = f.create_job(client_other)
        f.create_proposal(job_other, candidate, self.recruiter)

        self.assertFalse(
            candidate in client_admin.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_apply_jobs_filter(self):
        """Job linked via Proposal should be in jobs."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )

        candidate = f.create_candidate(self.agency)
        job = f.create_job(self.client)
        f.create_proposal(job, candidate, self.recruiter)

        self.assertTrue(
            job in client_admin.apply_jobs_filter(m.Job.objects.all()).all()
        )

    def test_apply_jobs_filter_without_proposal(self):
        """Job linked to other Client should not be in jobs."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )
        client_other = f.create_client()
        job_other = f.create_job(client_other)

        self.assertFalse(
            job_other in client_admin.apply_jobs_filter(m.Job.objects.all()).all()
        )

    def test_apply_jobs_filter_other_client(self):
        """Job not linked via Proposal should not be in jobs."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )

        candidate = f.create_candidate(self.agency)
        client_other = f.create_client()
        job_other = f.create_job(client_other)
        f.create_proposal(job_other, candidate, self.recruiter)

        self.assertFalse(
            job_other in client_admin.apply_jobs_filter(m.Job.objects.all()).all()
        )

    def test_apply_proposals_filter(self):
        """Proposal linked via Client Job should be in the list."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )
        job = f.create_job(self.client)

        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, self.recruiter)

        self.assertTrue(
            proposal in client_admin.apply_proposals_filter(m.Proposal.objects.all())
        )

    def test_apply_proposals_filter_other_client(self):
        """Proposal linked to other Client should not be in the list."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )
        client_other = f.create_client()
        job = f.create_job(client_other)

        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, self.recruiter)

        self.assertFalse(
            proposal in client_admin.apply_proposals_filter(m.Proposal.objects.all())
        )

    def test_contracts_filter(self):
        """Contracts for the own Client should be in the list."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )
        contract = f.create_contract(self.agency, self.client)

        self.assertTrue(
            contract in m.Contract.objects.filter(client_admin.contracts_filter).all()
        )

    def test_contracts_filter_other_client(self):
        """Contracts for other Client should not be in the list."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )
        client_other = f.create_client()
        contract = f.create_contract(self.agency, client_other)

        self.assertFalse(
            contract in m.Contract.objects.filter(client_admin.contracts_filter).all()
        )

    def test_org(self):
        """Should return the Client."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )

        self.assertEqual(client_admin.org, client_admin.client)

    @skip("TODO(ZOO-977)")
    def test_notification_types(self):
        """Should return NotificationTypeEnum enum."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )

        self.assertTrue(isinstance(client_admin.notification_types, list))
        self.assertTrue(len(client_admin.notification_types) > 0)

    def test_can_create_proposal(self):
        """Should return False, only Agency Users can create Proposals."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )

        self.assertFalse(
            client_admin.can_create_proposal(
                f.create_job(self.client), f.create_candidate(self.agency)
            )
        )

    def test_can_create_job_file_own_job(self):
        """Should return True for own Job."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )
        job = f.create_job(self.client)

        self.assertTrue(client_admin.can_create_job_file(job))

    def test_can_create_job_file_other_job(self):
        """Should return False for other Client's Job."""
        client_admin = m.ClientAdministrator.objects.create(
            client=self.client, user=self.user
        )
        job = f.create_job(f.create_client())

        self.assertFalse(client_admin.can_create_job_file(job))

    def test_profile_apply_candidates_filter_edge_case(self):
        """Should return candidate with a few proposals."""
        m.ClientAdministrator.objects.create(client=self.client, user=self.user)

        candidate = f.create_candidate(self.agency)

        for i in range(2):
            job = f.create_job(self.client)
            f.create_proposal(job, candidate, self.recruiter)

        candidates = self.user.profile.apply_candidates_filter(
            m.Candidate.objects.all()
        )

        # if broken, it equals number of proposals instead
        self.assertEqual(len(list(candidates)), 1)

    def test_deleted_when_client_deleted(self):
        """Client Administrator profile deleted when Client is deleted."""
        client = f.create_client()
        m.ClientAdministrator.objects.create(client=client, user=self.user)
        client.delete()

        self.assertEqual(m.ClientAdministrator.objects.count(), 0)


class ClientStandardUserTests(TestCase):
    """Tests related to the ClientStandardUser model."""

    def setUp(self):
        """Create the required objects during the initialization."""
        super().setUp()
        self.client = f.create_client()
        self.user = f.create_user()

        self.agency = f.create_agency()
        self.recruiter = f.create_recruiter(self.agency)

    def test_hiringmanager_created(self):
        """Hiring Manager successfully created."""
        hiring_manager = m.ClientStandardUser.objects.create(
            client=self.client, user=self.user
        )

        self.assertEqual(
            m.ClientStandardUser.objects.get(pk=hiring_manager.pk), hiring_manager
        )

    def test_hiringmanager_without_client(self):
        """Integrity Error raised when no Client passed."""
        with self.assertRaises(IntegrityError):
            m.ClientStandardUser.objects.create(user=self.user)

    def test_hiringmanager_without_user(self):
        """Integrity Error raised when no User passed."""
        with self.assertRaises(IntegrityError):
            m.ClientStandardUser.objects.create(client=self.client)

    def test_hiringmanager_str(self):
        """Hiring Manager string representation contains Client name."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)

        self.assertEqual(
            str(hm), 'Client Standard User of "{}"'.format(self.client.name)
        )

    def test_own_candidates_filter(self):
        """Own Candidate linked via Proposal should be in own candidates."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        candidate = f.create_candidate(self.client)
        job = f.create_job(self.client)
        f.create_proposal(job, candidate, hm.user)
        job.assign_manager(hm.user)

        self.assertTrue(
            candidate in hm.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_own_candidates_filter_agency(self):
        """Candidate linked to an Agency should not be in own candidates."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        client_other = f.create_client()
        job_other = f.create_job(client_other)

        candidate = f.create_candidate(self.agency)

        self.assertFalse(
            candidate in hm.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_own_candidates_filter_other_client(self):
        """Candidate linked to other Client should not be in own candidates."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        client_other = f.create_client()
        job_other = f.create_job(client_other)

        candidate = f.create_candidate(client_other)

        self.assertFalse(
            candidate in hm.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter(self):
        """Candidate from own Client should be in candidates."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        job = f.create_job(self.client)
        job.assign_manager(self.user)

        candidate = f.create_candidate(self.client)
        f.create_proposal(job, candidate, self.user)

        self.assertTrue(
            candidate in hm.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter_with_proposal(self):
        """Candidate linked via Proposal should be in candidates."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        job = f.create_job(self.client)
        job.assign_manager(self.user)

        candidate = f.create_candidate(self.agency)
        f.create_proposal(job, candidate, self.recruiter)

        self.assertTrue(
            candidate in hm.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter_without_proposal(self):
        """Candidate not linked via Proposal should not be in candidates."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        agency = f.create_agency()
        candidate = f.create_candidate(agency)

        self.assertFalse(
            candidate in hm.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter_not_assigned(self):
        """Candidate linked to other Client should be in candidates."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        job = f.create_job(self.client)

        candidate = f.create_candidate(self.agency)
        f.create_proposal(job, candidate, self.recruiter)

        self.assertTrue(
            candidate in hm.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter_other_client(self):
        """Candidate linked to other Client should not be in candidates."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        client_other = f.create_client()
        job_other = f.create_job(client_other)

        candidate = f.create_candidate(self.agency)
        f.create_proposal(job_other, candidate, self.recruiter)

        self.assertFalse(
            candidate in hm.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_apply_jobs_filter(self):
        """Job linked via Proposal should be in jobs."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        job = f.create_job(self.client)
        job.assign_manager(self.user)

        candidate = f.create_candidate(self.agency)
        f.create_proposal(job, candidate, self.recruiter)

        self.assertTrue(job in hm.apply_jobs_filter(m.Job.objects.all()).all())

    def test_apply_jobs_filter_without_proposal(self):
        """Job linked to other Client should not be in jobs."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        client_other = f.create_client()
        job_other = f.create_job(client_other)

        self.assertFalse(job_other in hm.apply_jobs_filter(m.Job.objects.all()).all())

    def test_apply_jobs_filter_not_assigned(self):
        """Not assigned Job should not be in jobs."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        job = f.create_job(self.client)

        candidate = f.create_candidate(self.agency)
        f.create_proposal(job, candidate, self.recruiter)

        self.assertFalse(job in hm.apply_jobs_filter(m.Job.objects.all()).all())

    def test_apply_jobs_filter_other_client(self):
        """Job not linked via Proposal should not be in jobs."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)

        client_other = f.create_client()
        job_other = f.create_job(client_other)

        candidate = f.create_candidate(self.agency)
        f.create_proposal(job_other, candidate, self.recruiter)

        self.assertFalse(job_other in hm.apply_jobs_filter(m.Job.objects.all()).all())

    def test_apply_proposals_filter(self):
        """Proposal of own Client for the assigned Job should be in list."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        job = f.create_job(self.client)
        job.assign_manager(self.user)

        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, self.recruiter)

        self.assertTrue(proposal in hm.apply_proposals_filter(m.Proposal.objects.all()))

    def test_apply_proposals_filter_not_assigned(self):
        """Proposal of own Client for not assigned Job shouldn't be in list."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        job = f.create_job(self.client)

        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, self.recruiter)

        self.assertFalse(
            proposal in hm.apply_proposals_filter(m.Proposal.objects.all())
        )

    def test_apply_proposals_filter_other_client(self):
        """Proposal of the other Client should not be in the list."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        client_other = f.create_client()
        job = f.create_job(client_other)

        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, self.recruiter)

        self.assertFalse(
            proposal in hm.apply_proposals_filter(m.Proposal.objects.all())
        )

    def test_contracts_filter(self):
        """Contracts for the own Client should be in the list."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        agency = f.create_agency()
        contract = f.create_contract(agency, self.client)

        self.assertTrue(
            contract in m.Contract.objects.filter(hm.contracts_filter).all()
        )

    def test_contracts_filter_other_client(self):
        """Contracts for other Client should not be in the list."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        agency = f.create_agency()
        client_other = f.create_client()
        contract = f.create_contract(agency, client_other)

        self.assertFalse(
            contract in m.Contract.objects.filter(hm.contracts_filter).all()
        )

    def test_org(self):
        """Should return the Client."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)

        self.assertEqual(hm.org, hm.client)

    @skip("TODO(ZOO-977)")
    def test_notification_types(self):
        """Should return NotificationTypeEnum enum."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)

        self.assertTrue(isinstance(hm.notification_types, list))
        self.assertTrue(len(hm.notification_types) > 0)

    def test_can_create_proposal(self):
        """Should return False, only Agency Users can create Proposals."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)

        self.assertFalse(
            hm.can_create_proposal(
                f.create_job(self.client), f.create_candidate(f.create_agency()),
            )
        )

    def test_can_create_job_file_assigned_own_job(self):
        """Should return True for own assigned Job."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        job = f.create_job(self.client)
        job.assign_manager(self.user)

        self.assertTrue(hm.can_create_job_file(job))

    def test_can_create_job_file_not_assigned_own_job(self):
        """Should return False for own not assigned Job."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        job = f.create_job(self.client)

        self.assertFalse(hm.can_create_job_file(job))

    def test_can_create_job_file_other_job(self):
        """Should return False for other Client's Job."""
        hm = m.ClientStandardUser.objects.create(client=self.client, user=self.user)
        job = f.create_job(f.create_client())

        self.assertFalse(hm.can_create_job_file(job))

    def test_profile_apply_candidates_filter_edge_case(self):
        """Should return candidate with a few proposals."""
        m.ClientStandardUser.objects.create(client=self.client, user=self.user)

        candidate = f.create_candidate(self.agency)

        for i in range(2):
            job = f.create_job(self.client)
            job.assign_manager(self.user)
            f.create_proposal(job, candidate, self.recruiter)

        candidates = self.user.profile.apply_candidates_filter(
            m.Candidate.objects.all()
        )

        # if broken, it equals number of proposals instead
        self.assertEqual(len(list(candidates)), 1)

    def test_deleted_when_client_deleted(self):
        """Hiring Manager profile deleted when Client is deleted."""
        client = f.create_client()
        m.ClientStandardUser.objects.create(client=client, user=self.user)
        client.delete()

        self.assertEqual(m.ClientStandardUser.objects.count(), 0)


class PrivateJobPostingTests(TestCase):
    def setUp(self):
        """Create a Client during setup process of a test object."""
        super().setUp()
        self.client_obj = f.create_client()
        self.owner = f.create_hiring_manager(self.client_obj)

    def test_public_uuid_default(self):
        """Job public_uuid default value is None."""
        job = m.Job(
            client=self.client_obj,
            title='Test Job',
            responsibilities='Test responsibilities',
            owner=self.owner,
        )
        job.organization = self.client_obj
        job.save()

        private_job_posting = m.PrivateJobPosting(job=job)
        private_job_posting.save()
        self.assertIsNone(private_job_posting.public_uuid)

    def test_public_manager(self):
        """Published Job with uuid should be in public_objects."""
        job = m.Job(client=self.client_obj, owner=self.owner, published=True,)
        job.organization = self.client_obj
        job.save()
        private_job_posting = m.PrivateJobPosting(job=job, public_uuid=uuid.uuid4(),)
        private_job_posting.save()
        self.assertTrue(private_job_posting in m.PrivateJobPosting.public_objects.all())

    def test_public_manager_not_published(self):
        """Closed Job with uuid shouldn't be in public_objects."""
        job = m.Job(client=self.client_obj, owner=self.owner)
        job.organization = self.client_obj
        job.save()

        private_job_posting = m.PrivateJobPosting(job=job, public_uuid=uuid.uuid4(),)
        private_job_posting.save()
        job.status = 'closed'
        job.save()
        self.assertFalse(
            private_job_posting in m.PrivateJobPosting.public_objects.all()
        )

    def test_public_manager_without_public_uuid(self):
        """Published Job without uuid shouldn't be in public_objects."""
        job = m.Job(client=self.client_obj, owner=self.owner, published=True)
        job.organization = self.client_obj
        job.save()
        private_job_posting = m.PrivateJobPosting(job=job)
        private_job_posting.save()
        self.assertFalse(
            private_job_posting in m.PrivateJobPosting.public_objects.all()
        )


class JobTests(TestCase):
    """Tests related to the Job model."""

    def setUp(self):
        """Create a Client during setup process of a test object."""
        super().setUp()
        self.client_obj = f.create_client()
        self.owner = f.create_hiring_manager(self.client_obj)

    def test_job_created(self):
        """Job successfully created."""
        job = m.Job(
            title='Test Job',
            responsibilities='Test responsibilities',
            owner=self.owner,
            client=self.client_obj,
        )
        job.organization = self.client_obj
        job.save()

        self.assertEqual(m.Job.objects.get(pk=job.pk), job)

    def test_job_created_agency(self):
        """Job successfully created."""
        job = m.Job(
            title='Test Job',
            responsibilities='Test responsibilities',
            owner=self.owner,
            client=self.client_obj,
        )
        job.organization = f.create_agency()
        job.save()

        self.assertEqual(m.Job.objects.get(pk=job.pk), job)

    def test_job_title_length_128(self):
        """Job successfully created when the title is 128 characters length."""
        job = m.Job(
            client=self.client_obj,
            title='a' * 128,
            responsibilities='Test responsibilities',
            owner=self.owner,
        )
        job.organization = self.client_obj
        job.save()

        self.assertEqual(m.Job.objects.get(pk=job.pk), job)

    def test_job_title_length_129(self):
        """Data Error raised when the title is more than 128 length."""
        with self.assertRaises(DataError):
            m.Job.objects.create(
                title='a' * 129,
                responsibilities='Test responsibilities',
                owner=self.owner,
            )

    def test_job_without_client(self):
        """Integrity Error raised when no Client specified."""
        with self.assertRaises(IntegrityError):
            m.Job.objects.create(
                title='Test Job', responsibilities='Test responsibilities',
            )

    def test_job_str(self):
        """Job string representation should contain its title."""
        job = m.Job(
            client=self.client_obj,
            title='Test Job',
            responsibilities='Test responsibilities',
            owner=self.owner,
        )
        job.organization = self.client_obj
        job.save()

        self.assertEqual(str(job), 'Test Job')

    def test_candidates(self):
        """Candidate linked via Proposals in list."""
        job = f.create_job(self.client_obj)

        agency = f.create_agency()
        candidate = f.create_candidate(agency)
        f.create_proposal(job, candidate, f.create_recruiter(agency))

        self.assertTrue(candidate in job.candidates())

    def test_candidates_not_linked(self):
        """Candidates not linked via Proposals not in list."""
        agency = f.create_agency()
        candidate = f.create_candidate(agency)
        job = f.create_job(self.client_obj)

        self.assertFalse(candidate in job.candidates())

    def test_candidates_other_job(self):
        """Candidates linked to other Job not in list."""
        agency = f.create_agency()
        candidate = f.create_candidate(agency)
        job = f.create_job(self.client_obj)
        client_other = f.create_client()
        job_other = f.create_job(client_other)
        f.create_proposal(job_other, candidate, f.create_recruiter(agency))

        self.assertFalse(candidate in job.candidates())

    def test_managers_property(self):
        """Property should return a QuerySet of all Job managers."""
        manager = f.create_hiring_manager(self.client_obj)
        job = f.create_job(self.client_obj)
        job.assign_manager(manager)

        self.assertTrue(isinstance(job.managers, QuerySet))
        self.assertEqual([manager], list(job.managers))

    def test_assignees_property(self):
        """Property should return a QuerySet of all Job assignees."""
        recruiter = f.create_recruiter(f.create_agency())
        job = f.create_job(self.client_obj)
        job.assign_member(recruiter)

        self.assertTrue(isinstance(job.assignees, QuerySet))
        self.assertEqual([recruiter], list(job.assignees))

    def test_assign_manager(self):
        """Should add the User to the list of Managers of the Job."""
        manager = f.create_hiring_manager(self.client_obj)
        job = f.create_job(self.client_obj)
        job.assign_manager(manager)

        self.assertTrue(manager in job.managers)

    def test_set_managers(self):
        """Should set Users to Managers of the Job, rewrite previous."""
        job = f.create_job(self.client_obj)
        job.assign_manager(f.create_hiring_manager(self.client_obj))

        manager_1 = f.create_hiring_manager(self.client_obj)
        manager_2 = f.create_hiring_manager(self.client_obj)
        job.set_managers([manager_1, manager_2])

        self.assertSetEqual({manager_1, manager_2}, set(job.managers))

    def test_withdraw_manager(self):
        """Should remove the User from the list of Recruiters of the Job."""
        manager = f.create_hiring_manager(self.client_obj)
        job = f.create_job(self.client_obj)
        job.assign_manager(manager)
        job.withdraw_manager(manager)

        self.assertFalse(manager in job.managers)

    def test_assign_member(self):
        """Should add the User to the list of Assignees of the Job."""
        recruiter = f.create_recruiter(f.create_agency())
        job = f.create_job(self.client_obj)
        job.assign_member(recruiter)

        self.assertTrue(recruiter in job.assignees)

    def test_assign_member_not_hiring_member(self):
        """Should not add the User to Assignees if not Agency Member."""
        user = f.create_user()
        job = f.create_job(self.client_obj)

        message = (
            'User should be one of Recruiter, ' 'Agency Manager or Agency Administrator'
        )
        with self.assertRaisesMessage(TypeError, message):
            job.assign_member(user)

    def test_set_members(self):
        """Should set Users to Assignees of the Job, rewrite previous."""
        job = f.create_job(self.client_obj)
        job.assign_member(f.create_recruiter(f.create_agency()))

        agency = f.create_agency()
        recruiter_1 = f.create_recruiter(agency)
        recruiter_2 = f.create_recruiter(agency)
        job.set_members([recruiter_1, recruiter_2])

        self.assertEqual([recruiter_1, recruiter_2], list(job.assignees))

    def test_set_members_not_changes_for_other_job(self):
        """Should not change other job assignments."""
        agency = f.create_agency()

        recruiter_1 = f.create_recruiter(agency)
        recruiter_2 = f.create_recruiter(agency)

        job = f.create_job(self.client_obj)
        job.assign_member(recruiter_1)

        another_job = f.create_job(self.client_obj)
        another_job.set_members([recruiter_2])

        self.assertEqual([recruiter_1], list(job.assignees))

    def test_set_members_one_not_hiring_member(self):
        """Should raise TypeError if at least one User not an Agency Member."""
        user = f.create_user()
        recruiter = f.create_recruiter(f.create_agency())
        job = f.create_job(self.client_obj)

        message = (
            'User should be one of Recruiter, '
            'Agency Manager or Agency Administrator.'
        )
        with self.assertRaisesMessage(TypeError, message):
            job.set_members([user, recruiter])

    def test_withdraw_member(self):
        """Should remove the User from the list of Recruiters of the Job."""
        recruiter = f.create_recruiter(f.create_agency())
        job = f.create_job(self.client_obj)
        job.assign_member(recruiter)
        job.withdraw_member(recruiter)

        self.assertFalse(recruiter in job.assignees)

    def test_assign_agency(self):
        """Should add job assignment for agency."""
        agency = f.create_agency()
        job = f.create_job(self.client_obj)
        job.assign_agency(agency)

        self.assertTrue(agency in job.agencies.all())

    def test_set_agencies(self):
        """Should set Agencies assigned to Job, overwriting previous."""
        job = f.create_job(self.client_obj)

        agencies = [f.create_agency() for _ in range(3)]

        job.assign_agency(agencies[0])
        job.set_agencies([agencies[1], agencies[2]])

        def assert_has_active_contract(agency, is_active):
            self.assertEqual(
                m.JobAgencyContract.objects.filter(
                    job=job, agency=agency, is_active=True
                ).exists(),
                is_active,
            )

        assert_has_active_contract(agencies[0], False)
        assert_has_active_contract(agencies[1], True)
        assert_has_active_contract(agencies[2], True)

    def test_set_agencies_not_changes_for_other_job(self):
        """Should not change other job assignments."""
        agency = f.create_agency()
        another_agency = f.create_agency()

        job = f.create_job(self.client_obj)
        job.assign_agency(agency)

        another_job = f.create_job(self.client_obj)
        another_job.set_agencies([another_agency])

        self.assertEqual([agency], list(job.agencies.all()))

    def test_withdraw_agency(self):
        """Should remove Agency from assigned Agencies of Job."""
        agency = f.create_agency()
        job = f.create_job(self.client_obj)
        job.assign_agency(agency)
        job.withdraw_agency(agency)

        self.assertFalse(agency in job.agencies.all())

    def test_deleted_when_client_deleted(self):
        """Job deleted when Client is deleted."""
        client = f.create_client()
        owner = f.create_hiring_manager(f.create_client())
        job = m.Job(
            client=self.client_obj,
            title='Test Job',
            responsibilities='Test responsibilities',
            owner=owner,
        )
        job.organization = client
        job.save()
        client.delete()

        self.assertEqual(m.Job.objects.count(), 0)

    def test_import_longlist(self):
        """Should copy longlist from one job to another job"""
        client = f.create_client()
        hiring_manager = f.create_hiring_manager(client)
        candidate_1 = f.create_candidate(client)
        candidate_2 = f.create_candidate(client)
        candidate_3 = f.create_candidate(client)

        job_1 = f.create_job(client)
        job_2 = f.create_job(client)

        f.create_proposal(job_1, candidate_1, hiring_manager, stage='longlist')
        f.create_proposal(job_1, candidate_2, hiring_manager, stage='longlist')
        f.create_proposal(job_1, candidate_3, hiring_manager, stage='longlist')

        candidates = [candidate_1.pk, candidate_2.pk, candidate_3.pk]
        job_2.import_longlist(hiring_manager, job_1, candidates)

        self.assertEqual(
            sorted(
                list(
                    m.Proposal.longlist.filter(job=job_2).values_list(
                        'candidate', flat=True
                    )
                )
            ),
            sorted(candidates),
        )

    def test_import_longlist_already_proposed(self):
        """Should not create duplicated proposals"""
        client = f.create_client()
        hiring_manager = f.create_hiring_manager(client)
        candidate_1 = f.create_candidate(client)
        candidate_2 = f.create_candidate(client)
        candidate_3 = f.create_candidate(client)
        candidate_4 = f.create_candidate(client)

        job_1 = f.create_job(client)
        job_2 = f.create_job(client)

        f.create_proposal(job_1, candidate_1, hiring_manager, stage='longlist')
        f.create_proposal(job_1, candidate_2, hiring_manager, stage='longlist')
        f.create_proposal(job_1, candidate_3, hiring_manager, stage='longlist')
        f.create_proposal(job_1, candidate_4, hiring_manager, stage='longlist')

        # already proposed candidates
        f.create_proposal(job_2, candidate_1, hiring_manager, stage='longlist')
        f.create_proposal(job_2, candidate_2, hiring_manager, stage='longlist')

        candidates = [candidate_1.pk, candidate_2.pk, candidate_3.pk, candidate_4.pk]
        job_2.import_longlist(hiring_manager, job_1, candidates)

        self.assertEqual(
            sorted(
                list(
                    m.Proposal.longlist.filter(job=job_2).values_list(
                        'candidate', flat=True
                    )
                )
            ),
            sorted(candidates),
        )


class JobFileTests(TestCase):
    """Tests related to the JobFile model."""

    def setUp(self):
        """Create Job object during class initialization."""
        super().setUp()
        self.job = f.create_job(f.create_client())

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_job_file_created(self):
        """Job file successfully created."""
        job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=self.job
        )

        self.assertEqual(m.JobFile.objects.get(pk=job_file.pk), job_file)
        self.assertFalse(job_file.file.name == '')

    def test_job_file_without_job(self):
        """Job file without Job not created."""
        with self.assertRaises(IntegrityError):
            m.JobFile.objects.create(file=SimpleUploadedFile('file.txt', b'contents'))

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_job_file_without_file(self):
        """Job file without file created."""
        job_file = m.JobFile.objects.create(job=self.job)

        self.assertEqual(m.JobFile.objects.get(pk=job_file.pk), job_file)
        self.assertTrue(job_file.file.name == '')


class JobQuestionTests(TestCase):
    """Tests related to the JobQuestion model."""

    def setUp(self):
        """Create Job during object initialization."""
        super().setUp()
        self.client_obj = f.create_client()
        self.job = f.create_job(self.client_obj)

    def test_job_question_created(self):
        """Job question succesfully created."""
        question = m.JobQuestion.objects.create(job=self.job, text='Test text')

        self.assertEqual(m.JobQuestion.objects.get(pk=question.pk), question)

    def test_job_text_lenght_1025(self):
        """Job question with text length 1025 not created."""
        with self.assertRaises(DataError):
            m.JobQuestion.objects.create(job=self.job, text='a' * 1025)

    def test_job_questions_without_job(self):
        """Job question without Job not created."""
        with self.assertRaises(IntegrityError):
            m.JobQuestion.objects.create(text='Test text')

    def test_job_question_str(self):
        """Job question string representation contains the text."""
        question = m.JobQuestion.objects.create(job=self.job, text='Test text')

        self.assertEqual(str(question), 'Test text')

    def test_deleted_when_job_deleted(self):
        """Job Question deleted when Job is deleted."""
        job = f.create_job(self.client_obj)
        m.JobQuestion.objects.create(job=job, text='Test text')
        job.delete()

        self.assertEqual(m.JobQuestion.objects.count(), 0)


class AgencyTests(TestCase):
    """Tests related to the Agency model."""

    def test_agency_created(self):
        """Agency successfully created."""
        agency = m.Agency.objects.create(primary_contact=f.create_user(),)

        self.assertEqual(m.Agency.objects.get(pk=agency.pk), agency)

    def test_agency_created_with_default_proposal_statuses(self):
        """Client's default proposal statuses are created."""
        agency = m.Agency.objects.create(name='Test', primary_contact=f.create_user())
        proposal_statuses_count = agency.proposal_statuses.count()

        self.assertTrue(proposal_statuses_count > 0)
        self.assertEqual(
            proposal_statuses_count,
            m.ProposalStatus.objects.filter(default=True,)
            .exclude(group__in=m.LONGLIST_PROPOSAL_STATUS_GROUPS)
            .count(),
        )

    def test_agency_name_length_128(self):
        """Agency successfully created when the name is 128 length."""
        agency = m.Agency.objects.create(
            name='a' * 128, primary_contact=f.create_user()
        )

        self.assertEqual(m.Agency.objects.get(pk=agency.pk), agency)

    def test_agency_name_length_129(self):
        """Data Error raised when the name is more than 128 length."""
        with self.assertRaises(DataError):
            m.Agency.objects.create(name='a' * 129, primary_contact=f.create_user())

    def test_agency_str(self):
        """Agency string representation should contain its pk and name."""
        agency = m.Agency.objects.create(
            name='Test Agency', primary_contact=f.create_user()
        )

        self.assertEqual(str(agency), '{} - Test Agency'.format(agency.pk))

    def test_assign_agency_administrator_profile_created(self):
        """Agency administrator profile created when the User is assigned."""
        user = f.create_user()
        agency = m.Agency.objects.create(primary_contact=user)
        agency.assign_agency_administrator(user)

        self.assertTrue(m.AgencyAdministrator.objects.filter(user=user).exists())

    def test_assign_agency_administrator_added_to_group(self):
        """User added to Agency Administrators group when they are assigned."""
        user = f.create_user()
        agency = m.Agency.objects.create(primary_contact=user)
        agency.assign_agency_administrator(user)

        self.assertTrue(user.groups.filter(name='Agency Administrators').exists())

    def test_assign_agency_manager_profile_created(self):
        """Agency manager profile created when the User is assigned."""
        user = f.create_user()
        agency = m.Agency.objects.create(primary_contact=user)
        agency.assign_agency_manager(user)

        self.assertTrue(m.AgencyManager.objects.filter(user=user).exists())

    def test_assign_agency_manager_added_to_group(self):
        """User added to Agency Managers group when they are assigned."""
        user = f.create_user()
        agency = m.Agency.objects.create(primary_contact=user)
        agency.assign_agency_manager(user)

        self.assertTrue(user.groups.filter(name='Agency Managers').exists())

    def test_assign_recruiter_profile_created(self):
        """Recruiter profile created when the User is assigned."""
        user = f.create_user()
        agency = m.Agency.objects.create(primary_contact=user)
        agency.assign_recruiter(user)

        self.assertTrue(m.Recruiter.objects.filter(user=user).exists())

    def test_assign_recruiter_added_to_group(self):
        """User added to Recruiters group when they are assigned."""
        user = f.create_user()
        agency = m.Agency.objects.create(primary_contact=user)
        agency.assign_recruiter(user)

        self.assertTrue(user.groups.filter(name='Recruiters').exists())

    def test_members(self):
        """Should return members of Agency organization."""
        aa = f.create_user()
        agency = m.Agency.objects.create(primary_contact=aa)
        agency.assign_agency_administrator(aa)

        am = f.create_agency_manager(agency)
        recruiter = f.create_recruiter(agency)

        another_agency_administrator = f.create_user()
        another_agency = m.Agency.objects.create(
            primary_contact=another_agency_administrator,
        )
        another_agency.assign_agency_administrator(another_agency_administrator)
        f.create_agency_manager(another_agency)
        f.create_recruiter(another_agency)

        client_admin = f.create_user()
        client = f.create_client(primary_contact=client_admin)
        client.assign_administrator(client_admin)
        f.create_hiring_manager(client)

        self.assertEqual(
            {i.pk for i in agency.members.all()}, {recruiter.pk, aa.pk, am.pk}
        )

    def test_get_by_email_domain(self):
        """Should return Agency by email domain."""

        agency = f.create_agency(primary_contact=f.create_user())
        agency.email_domain = 'agency.com'
        agency.save()

        self.assertEqual(agency.get_by_email_domain('recruiter@agency.com'), agency)

    def test_default_values(self):
        """Agencies should not be featured by default"""
        agency = f.create_agency()
        self.assertEqual(agency.enable_researcher_field_feature, False)


class AgencyInviteTests(TestCase):
    """Tests for the AgencyInvite model."""

    def test_created(self):
        """Agency invite successfully created."""
        invite = m.AgencyInvite.objects.create(
            email='test@test.com', private_note='Test note'
        )

        self.assertEqual(m.AgencyInvite.objects.get(pk=invite.pk), invite)

    def test_str(self):
        """Agency invite string representation contains its pk."""
        invite = m.AgencyInvite.objects.create(
            email='test@test.com', private_note='Test note'
        )

        self.assertEqual(str(invite), 'Agency Invite #{}'.format(invite.pk))

    def test_get_absolute_url(self):
        """Get absolute url method returns the correct value."""
        token = 'test'

        invite = m.AgencyInvite.objects.create(
            email='test@test.com', private_note='Test note', token=token
        )

        self.assertEqual(
            invite.get_absolute_url(),
            reverse('agency_sign_up_token', kwargs={'token': token}),
        )

    def test_private_note_max_length_1025(self):
        """Agency invite private not cannot be more than 1024 symbols."""
        with self.assertRaises(DataError):
            m.AgencyInvite.objects.create(
                email='test@test.com', private_note='a' * 1025
            )

    @patch('core.models.secrets.token_urlsafe')
    def test_token_default(self, mock):
        """Agency invite token default value is set by a custom method."""
        token = 'test'
        mock.return_value = token

        invite = m.AgencyInvite.objects.create(
            email='test@test.com', private_note='Test note'
        )

        mock.assert_called_with(16)
        self.assertEqual(invite.token, token)

    def test_token_max_length_129(self):
        """Agency invite token cannot be more than 128 symbols."""
        with self.assertRaises(DataError):
            m.AgencyInvite.objects.create(
                email='test@test.com', private_note='Test note', token='a' * 129
            )

    def test_token_not_editable(self):
        """Agency invite token field is not editable."""
        token_field = m.AgencyInvite._meta.get_field('token')

        self.assertFalse(token_field.editable)

    def test_token_unique(self):
        """Integrity error rased when the invite with same token created."""
        token = 'test'

        m.AgencyInvite.objects.create(
            email='test@test.com', private_note='Test note', token=token
        )

        with self.assertRaises(IntegrityError):
            m.AgencyInvite.objects.create(
                email='test@test.com', private_note='Test note', token=token
            )

    def test_used_by_not_editable(self):
        """Agency invite used by field is not editable."""
        used_by_field = m.AgencyInvite._meta.get_field('used_by')

        self.assertFalse(used_by_field.editable)

    def test_deleted_along_with_agency(self):
        """Agency invite token is deleted along with Agency."""
        agency = f.create_agency()

        invite = m.AgencyInvite.objects.create(
            email='test@test.com', private_note='Test note', used_by=agency
        )

        agency.delete()

        self.assertIsNone(m.AgencyInvite.objects.filter(pk=invite.pk).first())


class TeamTests(TestCase):
    def setUp(self):
        super().setUp()
        self.agency = f.create_agency()

    def test_agency_team_created(self):
        """Team successfully created."""
        team = m.Team.objects.create(name='TestTeam', organization=self.agency)

        self.assertEqual(m.Team.objects.get(pk=team.pk), team)

    def test_agency_team_unique_together(self):
        """Integrity Error raised when passed not unique pair of objects."""
        m.Team.objects.create(name='TestTeam', organization=self.agency)
        with self.assertRaises(IntegrityError):
            m.Team.objects.create(name='TestTeam', organization=self.agency)

    def test_agency_team_str(self):
        team = m.Team.objects.create(name='TestTeam', organization=self.agency)

        self.assertEqual(str(team), team.name)


class ContractTests(TestCase):
    """Tests related to the Contract model."""

    def setUp(self):
        """Create Client and Agency during setup process."""
        super().setUp()
        self.agency = f.create_agency()
        self.client_obj = f.create_client()

    def test_contract_created(self):
        """Contract successfully created."""
        contract = m.Contract.objects.create(agency=self.agency, client=self.client_obj)
        self.assertEqual(m.Contract.objects.get(pk=contract.pk), contract)

    def test_contract_without_agency(self):
        """Integrity Error raised when no Agency passed."""
        with self.assertRaises(IntegrityError):
            m.Contract.objects.create(client=self.client_obj)

    def test_contract_without_client(self):
        """Integrity Error raised when no Client passed."""
        with self.assertRaises(IntegrityError):
            m.Contract.objects.create(agency=self.agency)

    def test_contract_unique_together(self):
        """Integrity Error raised when passed not unique pair of objects."""
        m.Contract.objects.create(agency=self.agency, client=self.client_obj)
        with self.assertRaises(IntegrityError):
            m.Contract.objects.create(agency=self.agency, client=self.client_obj)

    def test_contract_str(self):
        """Contract string representation should contain agency and client."""
        contract = m.Contract.objects.create(agency=self.agency, client=self.client_obj)
        self.assertEqual(
            str(contract), '{} with {}'.format(contract.agency, contract.client)
        )

    def test_deleted_with_client(self):
        """Contract deleted when Client is deleted."""
        client = f.create_client()
        m.Contract.objects.create(agency=self.agency, client=client)
        client.delete()

        self.assertEqual(m.Contract.objects.count(), 0)

    def test_deleted_with_agency(self):
        """Contract deleted when Agency is deleted."""
        agency = f.create_agency()
        m.Contract.objects.create(agency=agency, client=self.client_obj)
        agency.delete()

        self.assertEqual(m.Contract.objects.count(), 0)


class LanguageTests(TestCase):
    """Tests related to the Language model."""

    def test_language_created(self):
        """Language successfully created."""
        language = m.Language.objects.create(language='test', level=0)

        self.assertEqual(m.Language.objects.get(pk=language.pk), language)

    def test_language_unique(self):
        """Language with duplicated language and level not created."""
        m.Language.objects.create(language='test', level=0)

        with self.assertRaises(IntegrityError):
            m.Language.objects.create(language='test', level=0)

    def test_language_level_default(self):
        """Language level field default value is 0."""
        language = m.Language.objects.create(language='test', level=0)

        self.assertEqual(language.level, 0)

    def test_language_length_17(self):
        """Language with language length 17 not created."""
        with self.assertRaises(DataError):
            m.Language.objects.create(language='a' * 17, level=0)

    def test_language_str_english(self):
        """Language string representation contains the language name."""
        language = m.Language.objects.get(language='en', level=0)

        self.assertEqual(str(language), 'Survival English')


class AgencyAdministratorTests(TestCase):
    """Tests related to the Agency Administrator model."""

    def setUp(self):
        """Create Agency and User during initialization."""
        super().setUp()
        self.agency = f.create_agency()
        self.user = f.create_user()

    def test_created(self):
        """Agency Administrator successfully created."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)

        self.assertEqual(m.AgencyAdministrator.objects.get(pk=aa.pk), aa)

    def test_without_agency(self):
        """Integrity Error raised when no Agency passed."""
        with self.assertRaises(IntegrityError):
            m.AgencyAdministrator.objects.create(user=self.user)

    def test_without_user(self):
        """Integrity Error raised when no User passed."""
        with self.assertRaises(IntegrityError):
            m.AgencyAdministrator.objects.create(agency=self.agency)

    def test_recruiter_str(self):
        """Agency Administrator string representation contains Agency name."""
        r = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)

        self.assertEqual(
            str(r), 'Agency Administrator of "{}"'.format(self.agency.name)
        )

    def test_own_candidates_filter(self):
        """Candidate of own Agency should be in own candidates."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        candidate = f.create_candidate(self.agency)

        self.assertTrue(
            candidate in aa.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_own_candidates_filter_client(self):
        """Candidate of a Client should not be in own candidates."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        candidate_other = f.create_candidate(f.create_client())

        self.assertFalse(
            candidate_other in aa.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_own_candidates_filter_other_agency(self):
        """Candidate of other Agency should not be in own candidates."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        agency_other = f.create_agency()
        candidate_other = f.create_candidate(agency_other)

        self.assertFalse(
            candidate_other in aa.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter(self):
        """Candidate of own Agency should be in candidates."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        candidate = f.create_candidate(self.agency)

        self.assertTrue(
            candidate in aa.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter_client(self):
        """Candidate of a Client should not be in candidates."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        candidate_other = f.create_candidate(f.create_client())

        self.assertFalse(
            candidate_other in aa.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter_other_agency(self):
        """Candidate of other Agency should not be in candidates."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        agency_other = f.create_agency()
        candidate_other = f.create_candidate(agency_other)

        self.assertFalse(
            candidate_other in aa.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_apply_jobs_filter_agency_assigned(self):
        """Job assigned to own Agency should be in jobs."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        job = f.get_job_assigned_to_agency(self.agency)

        self.assertTrue(job in aa.apply_jobs_filter(m.Job.objects.all()).all())

    def test_apply_jobs_filter_member_assigned(self):
        """Job assigned to the Agency Member should not be in jobs."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        r = f.create_recruiter(self.agency)
        client = f.create_client()
        job = f.create_job(client)
        job.assign_member(r)

        self.assertFalse(job in aa.apply_jobs_filter(m.Job.objects.all()).all())

    def test_apply_jobs_filter_not_assigned(self):
        """Job not assigned to own Agency should not be in jobs."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        job = f.create_job(client)

        self.assertFalse(job in aa.apply_jobs_filter(m.Job.objects.all()).all())

    def test_apply_jobs_filter_other_agency(self):
        """Job assigned to other Agency should not be in jobs."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        agency_other = f.create_agency()
        client = f.create_client()
        job = f.create_job(client)
        job.assign_agency(agency_other)

        self.assertFalse(job in aa.apply_jobs_filter(m.Job.objects.all()).all())

    def test_apply_proposals_filter(self):
        """Proposal created by themselves should be in the list."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        job = f.create_job(client)
        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, self.user)

        self.assertTrue(proposal in aa.apply_proposals_filter(m.Proposal.objects.all()))

    def test_apply_proposals_filter_by_own_recruiter(self):
        """Proposal created by R. of own Agency should be in the list."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        job = f.create_job(client)
        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, f.create_recruiter(self.agency))

        self.assertTrue(proposal in aa.apply_proposals_filter(m.Proposal.objects.all()))

    def test_apply_proposals_filter_by_own_agency_administrator(self):
        """Proposal created by AA of own Agency should be in the list."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        job = f.create_job(client)
        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(
            job, candidate, f.create_agency_administrator(self.agency)
        )

        self.assertTrue(proposal in aa.apply_proposals_filter(m.Proposal.objects.all()))

    def test_apply_proposals_filter_by_other_recruiter(self):
        """Proposal created by R. of other Agency shouldn't be in the list."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        job = f.create_job(client)
        candidate = f.create_candidate(f.create_agency())
        proposal = f.create_proposal(job, candidate, f.create_recruiter(self.agency))

        self.assertFalse(
            proposal in aa.apply_proposals_filter(m.Proposal.objects.all())
        )

    def test_apply_proposals_filter_by_other_agency_administrator(self):
        """Proposal created by AA of other Agency shouldn't be in the list."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        job = f.create_job(client)
        candidate = f.create_candidate(f.create_agency())
        proposal = f.create_proposal(
            job, candidate, f.create_agency_administrator(self.agency)
        )

        self.assertFalse(
            proposal in aa.apply_proposals_filter(m.Proposal.objects.all())
        )

    def test_apply_proposals_filter_other_agency(self):
        """Proposal created for othe Agency's Candidate not in the list."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        job = f.create_job(client)
        agency_other = f.create_agency()
        candidate_other = f.create_candidate(agency_other)
        proposal = f.create_proposal(job, candidate_other, self.user)

        self.assertFalse(
            proposal in aa.apply_proposals_filter(m.Proposal.objects.all())
        )

    def test_contracts_filter(self):
        """Contracts for the own Agency should be in the list."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        contract = f.create_contract(self.agency, client)

        self.assertTrue(
            contract in m.Contract.objects.filter(aa.contracts_filter).all()
        )

    def test_contracts_filter_other_agency(self):
        """Contracts for other Agency should not be in the list."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        agency_other = f.create_agency()
        client = f.create_client()
        contract = f.create_contract(agency_other, client)

        self.assertFalse(
            contract in m.Contract.objects.filter(aa.contracts_filter).all()
        )

    def test_org(self):
        """Should return the Agency."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)

        self.assertEqual(aa.org, aa.agency)

    @skip("TODO(ZOO-977)")
    def test_notification_types(self):
        """Should return NotificationTypeEnum enum."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)

        self.assertTrue(isinstance(aa.notification_types, list))
        self.assertTrue(len(aa.notification_types) > 0)

    def test_can_create_proposal_own_candidate_agency_assigned(self):
        """Should return True for own Candidate if Agency assigned."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)

        self.assertTrue(aa.can_create_proposal(job, f.create_candidate(self.agency)))

    def test_can_create_proposal_own_candidate_not_assigned(self):
        """Should return False for own Candidate and not assigned Job."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)

        self.assertFalse(
            aa.can_create_proposal(
                f.create_job(f.create_client()), f.create_candidate(self.agency),
            )
        )

    def test_can_create_proposal_other_candidate_agency_assigned(self):
        """Should return False for other Candidate and assigned Job."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)

        self.assertFalse(
            aa.can_create_proposal(job, f.create_candidate(f.create_agency()))
        )

    def test_can_create_proposal_other_candidate_not_assigned(self):
        """Should return False for other Candidate and not assigned Job."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)

        self.assertFalse(
            aa.can_create_proposal(
                f.create_job(f.create_client()), f.create_candidate(f.create_agency()),
            )
        )

    def test_can_create_job_file(self):
        """Should return False."""
        aa = m.AgencyAdministrator.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        job = f.create_job(client)
        job.assign_agency(self.agency)

        self.assertFalse(aa.can_create_job_file(job))

    def test_deleted_when_agency_deleted(self):
        """Agency Administrator deleted when Agency is deleted."""
        agency = f.create_agency()
        aa = m.AgencyAdministrator.objects.create(agency=agency, user=self.user)
        agency.delete()

        self.assertIsNone(m.AgencyAdministrator.objects.filter(pk=aa.pk).first())


class AgencyManagerTests(TestCase):
    """Tests related to the Agency Manager model."""

    def setUp(self):
        """Create Agency and User during initialization."""
        super().setUp()
        self.agency = f.create_agency()
        self.user = f.create_user()

    def test_created(self):
        """Agency Manager successfully created."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)

        self.assertEqual(m.AgencyManager.objects.get(pk=am.pk), am)

    def test_without_agency(self):
        """Integrity Error raised when no Agency passed."""
        with self.assertRaises(IntegrityError):
            m.AgencyManager.objects.create(user=self.user)

    def test_without_user(self):
        """Integrity Error raised when no User passed."""
        with self.assertRaises(IntegrityError):
            m.AgencyManager.objects.create(agency=self.agency)

    def test_recruiter_str(self):
        """Agency Manager string representation contains Agency name."""
        r = m.AgencyManager.objects.create(agency=self.agency, user=self.user)

        self.assertEqual(str(r), 'Agency Manager of "{}"'.format(self.agency.name))

    def test_own_candidates_filter(self):
        """Candidate of own Agency should be in own candidates."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        candidate = f.create_candidate(self.agency)

        self.assertTrue(
            candidate in am.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_own_candidates_filter_client(self):
        """Candidate of a Client should not be in own candidates."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        candidate_other = f.create_candidate(f.create_client())

        self.assertFalse(
            candidate_other in am.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_own_candidates_filter_other_agency(self):
        """Candidate of other Agency should not be in own candidates."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        agency_other = f.create_agency()
        candidate_other = f.create_candidate(agency_other)

        self.assertFalse(
            candidate_other in am.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter(self):
        """Candidate of own Agency should be in candidates."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        candidate = f.create_candidate(self.agency)

        self.assertTrue(
            candidate in am.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter_client(self):
        """Candidate of a Client should not be in candidates."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        candidate_other = f.create_candidate(f.create_client())

        self.assertFalse(
            candidate_other in am.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter_other_agency(self):
        """Candidate of other Agency should not be in candidates."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        agency_other = f.create_agency()
        candidate_other = f.create_candidate(agency_other)

        self.assertFalse(
            candidate_other in am.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_apply_jobs_filter_agency_assigned(self):
        """Job assigned to own Agency should be in jobs."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        job = f.get_job_assigned_to_agency(self.agency)

        self.assertTrue(job in am.apply_jobs_filter(m.Job.objects.all()).all())

    def test_apply_jobs_filter_member_assigned(self):
        """Job assigned to the Agency Member should not be in jobs."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        r = f.create_recruiter(self.agency)
        client = f.create_client()
        job = f.create_job(client)
        job.assign_member(r)

        self.assertFalse(job in am.apply_jobs_filter(m.Job.objects.all()).all())

    def test_apply_jobs_filter_not_assigned(self):
        """Job not assigned to own Agency should not be in jobs."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        job = f.create_job(client)

        self.assertFalse(job in am.apply_jobs_filter(m.Job.objects.all()).all())

    def test_apply_jobs_filter_other_agency(self):
        """Job assigned to other Agency should not be in jobs."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        agency_other = f.create_agency()
        client = f.create_client()
        job = f.create_job(client)
        job.assign_agency(agency_other)

        self.assertFalse(job in am.apply_jobs_filter(m.Job.objects.all()).all())

    def test_apply_proposals_filter(self):
        """Proposal linked via own Candidate should be in the list."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        job = f.create_job(client)
        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, self.user)

        self.assertTrue(proposal in am.apply_proposals_filter(m.Proposal.objects.all()))

    def test_apply_proposals_filter_own_recruiter(self):
        """Proposal created by own Recruiter should be in the list."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        job = f.create_job(client)
        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, f.create_recruiter(self.agency))

        self.assertTrue(proposal in am.apply_proposals_filter(m.Proposal.objects.all()))

    def test_apply_proposals_filter_other_agency(self):
        """Proposal created for othe Agency's Candidate not in the list."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        job = f.create_job(client)
        agency_other = f.create_agency()
        candidate_other = f.create_candidate(agency_other)
        proposal = f.create_proposal(job, candidate_other, self.user)

        self.assertFalse(
            proposal in am.apply_proposals_filter(m.Proposal.objects.all())
        )

    def test_contracts_filter(self):
        """Contracts for the own Agency should be in the list."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        contract = f.create_contract(self.agency, client)

        self.assertTrue(
            contract in m.Contract.objects.filter(am.contracts_filter).all()
        )

    def test_contracts_filter_other_agency(self):
        """Contracts for other Agency should not be in the list."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        agency_other = f.create_agency()
        client = f.create_client()
        contract = f.create_contract(agency_other, client)

        self.assertFalse(
            contract in m.Contract.objects.filter(am.contracts_filter).all()
        )

    def test_org(self):
        """Should return the Agency."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)

        self.assertEqual(am.org, am.agency)

    @skip("TODO(ZOO-977)")
    def test_notification_types(self):
        """Should return NotificationTypeEnum enum."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)

        self.assertTrue(isinstance(am.notification_types, list))
        self.assertTrue(len(am.notification_types) > 0)

    def test_can_create_proposal_own_candidate_agency_assigned(self):
        """Should return True for own Candidate if Agency assigned."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)

        self.assertTrue(am.can_create_proposal(job, f.create_candidate(self.agency)))

    def test_can_create_proposal_own_candidate_not_assigned(self):
        """Should return False for own Candidate and not assigned Job."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)

        self.assertFalse(
            am.can_create_proposal(
                f.create_job(f.create_client()), f.create_candidate(self.agency),
            )
        )

    def test_can_create_proposal_other_candidate_agency_assigned(self):
        """Should return False for other Candidate and assigned Job."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        job = f.create_job(f.create_client())
        job.assign_agency(self.agency)

        self.assertFalse(
            am.can_create_proposal(job, f.create_candidate(f.create_agency()))
        )

    def test_can_create_proposal_other_candidate_not_assigned(self):
        """Should return False for other Candidate and not assigned Job."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)

        self.assertFalse(
            am.can_create_proposal(
                f.create_job(f.create_client()), f.create_candidate(f.create_agency()),
            )
        )

    def test_can_create_job_file(self):
        """Should return False."""
        am = m.AgencyManager.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        job = f.create_job(client)
        job.assign_agency(self.agency)

        self.assertFalse(am.can_create_job_file(job))

    def test_deleted_when_agency_deleted(self):
        """Agency Manager deleted when Agency is deleted."""
        agency = f.create_agency()
        am = m.AgencyManager.objects.create(agency=agency, user=self.user)
        agency.delete()

        self.assertIsNone(m.AgencyManager.objects.filter(pk=am.pk).first())


class RecruiterTests(TestCase):
    """Tests related to the Recruiter model."""

    def setUp(self):
        """Create Agency and User during initialization."""
        super().setUp()
        self.agency = f.create_agency()
        self.user = f.create_user()

    def test_recruiter_created(self):
        """Recruiter successfully created."""
        recruiter = m.Recruiter.objects.create(agency=self.agency, user=self.user)

        self.assertEqual(m.Recruiter.objects.get(pk=recruiter.pk), recruiter)

    def test_recruiter_without_agency(self):
        """Integrity Error raised when no Agency passed."""
        with self.assertRaises(IntegrityError):
            m.Recruiter.objects.create(user=self.user)

    def test_recruiter_without_user(self):
        """Integrity Error raised when no User passed."""
        with self.assertRaises(IntegrityError):
            m.Recruiter.objects.create(agency=self.agency)

    def test_recruiter_str(self):
        """Recruiter string representation contains Agency name."""
        r = m.Recruiter.objects.create(agency=self.agency, user=self.user)

        self.assertEqual(str(r), 'Recruiter of "{}"'.format(self.agency.name))

    def test_own_candidates_filter(self):
        """Candidate of own Agency should be in own candidates."""
        r = m.Recruiter.objects.create(agency=self.agency, user=self.user)
        candidate = f.create_candidate(self.agency)

        self.assertTrue(
            candidate in r.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_own_candidates_filter_client(self):
        """Candidate of a Client should not be in own candidates."""
        r = m.Recruiter.objects.create(agency=self.agency, user=self.user)
        candidate_other = f.create_candidate(f.create_client())

        self.assertFalse(
            candidate_other in r.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_own_candidates_filter_other_agency(self):
        """Candidate of other Agency should not be in own candidates."""
        r = m.Recruiter.objects.create(agency=self.agency, user=self.user)
        agency_other = f.create_agency()
        candidate_other = f.create_candidate(agency_other)

        self.assertFalse(
            candidate_other in r.apply_own_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter(self):
        """Candidate of own Agency should be in candidates."""
        r = m.Recruiter.objects.create(agency=self.agency, user=self.user)
        candidate = f.create_candidate(self.agency)

        self.assertTrue(
            candidate in r.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter_client(self):
        """Candidate of a Client should not be in candidates."""
        r = m.Recruiter.objects.create(agency=self.agency, user=self.user)
        candidate_other = f.create_candidate(f.create_client())

        self.assertFalse(
            candidate_other in r.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_candidates_filter_other_agency(self):
        """Candidate of other Agency should not be in candidates."""
        r = m.Recruiter.objects.create(agency=self.agency, user=self.user)
        agency_other = f.create_agency()
        candidate_other = f.create_candidate(agency_other)

        self.assertFalse(
            candidate_other in r.apply_candidates_filter(m.Candidate.objects).all()
        )

    def test_apply_jobs_filter_agency_assigned(self):
        """Recruiter can't see jobs his agency were assigned to"""
        r = f.create_recruiter(self.agency)
        job = f.get_job_assigned_to_agency(self.agency)
        self.assertFalse(job in r.profile.apply_jobs_filter(m.Job.objects))

    def test_apply_jobs_filter_recruiter_assigned_to_job(self):
        """Recruiter can see jobs he was assigned to by his agency"""
        r = f.create_recruiter(self.agency)
        job = f.get_job_assigned_to_agency(self.agency)
        job.assign_member(r)

        self.assertTrue(job in r.profile.apply_jobs_filter(m.Job.objects))

    def test_apply_jobs_filter_member_assigned_to_multiple_jobs(self):
        """Multiple Jobs assigned to the Agency Member should be in jobs."""
        r = f.create_recruiter(self.agency)
        client = f.create_client()
        job = f.get_job_assigned_to_agency(self.agency)
        job.assign_member(r)
        job_2 = f.get_job_assigned_to_agency(self.agency)
        job_2.assign_member(r)

        result = r.profile.apply_jobs_filter(m.Job.objects)

        self.assertEqual(len(result), 2)
        self.assertTrue(job in result)
        self.assertTrue(job_2 in result)

    def test_apply_jobs_filter_not_assigned(self):
        """Job not assigned to own Agency should not be in jobs."""
        r = f.create_recruiter(self.agency)
        client = f.create_client()
        job = f.create_job(client)

        self.assertFalse(job in r.profile.apply_jobs_filter(m.Job.objects))

    def test_apply_jobs_filter_other_agency(self):
        """Job assigned to other Agency should not be in jobs."""
        r = f.create_recruiter(self.agency)
        agency_other = f.create_agency()
        job = f.get_job_assigned_to_agency(agency_other)

        self.assertFalse(job in r.profile.apply_jobs_filter(m.Job.objects))

    def test_apply_proposals_filter(self):
        """Proposal linked via own Candidate should be in the list."""
        r = f.create_recruiter(self.agency)
        candidate = f.create_candidate(self.agency)

        job = f.get_job_assigned_to_agency(self.agency)
        job.assign_member(r)
        proposal = f.create_proposal(job, candidate, r)

        self.assertTrue(
            proposal in r.profile.apply_proposals_filter(m.Proposal.objects)
        )

    def test_apply_proposals_filter_other_recruiter(self):
        """Proposal created by other Recruiter should be in the list."""
        r = f.create_recruiter(self.agency)
        client = f.create_client()
        f.create_contract(self.agency, client)
        job = f.create_job(client)
        job.assign_agency(self.agency)
        job.assign_member(r)
        candidate = f.create_candidate(self.agency)
        proposal = f.create_proposal(job, candidate, f.create_recruiter(self.agency))

        self.assertIn(proposal, r.profile.apply_proposals_filter(m.Proposal.objects))

    def test_apply_proposals_filter_other_agency(self):
        """Proposal created for other Agency's Candidate not in the list."""
        r = f.create_recruiter(self.agency)
        client = f.create_client()
        job = f.create_job(client)
        agency_other = f.create_agency()
        candidate_other = f.create_candidate(agency_other)
        proposal = f.create_proposal(job, candidate_other, self.user)

        self.assertFalse(
            proposal in r.profile.apply_proposals_filter(m.Proposal.objects)
        )

    def test_contracts_filter(self):
        """Contracts for the own Agency should be in the list."""
        r = m.Recruiter.objects.create(agency=self.agency, user=self.user)
        client = f.create_client()
        contract = f.create_contract(self.agency, client)

        self.assertTrue(contract in m.Contract.objects.filter(r.contracts_filter).all())

    def test_contracts_filter_other_agency(self):
        """Contracts for other Agency should not be in the list."""
        r = m.Recruiter.objects.create(agency=self.agency, user=self.user)
        agency_other = f.create_agency()
        client = f.create_client()
        contract = f.create_contract(agency_other, client)

        self.assertFalse(
            contract in m.Contract.objects.filter(r.contracts_filter).all()
        )

    def test_org(self):
        """Should return the Agency."""
        r = m.Recruiter.objects.create(agency=self.agency, user=self.user)

        self.assertEqual(r.org, r.agency)

    @skip("TODO(ZOO-977)")
    def test_notification_types(self):
        """Should return NotificationTypeEnum enum."""
        r = m.Recruiter.objects.create(agency=self.agency, user=self.user)

        self.assertTrue(isinstance(r.notification_types, list))
        self.assertTrue(len(r.notification_types) > 0)

    def test_can_create_proposal_own_candidate_member_assigned(self):
        """Should return False if Agency Member is assigned but agency is not."""
        r = f.create_recruiter(self.agency)
        candidate = f.create_candidate(self.agency)
        job = f.create_job(f.create_client())
        job.assign_member(r)

        self.assertFalse(r.profile.can_create_proposal(job, candidate))

    def test_can_create_proposal_own_candidate_member_and_agency_assigned(self):
        """Should return True for own Candidate if both assigned."""
        r = f.create_recruiter(self.agency)
        candidate = f.create_candidate(self.agency)
        job = f.get_job_assigned_to_agency(self.agency)
        job.assign_member(r)

        self.assertTrue(r.profile.can_create_proposal(job, candidate))

    def test_can_create_proposal_own_candidate_agency_assigned(self):
        """Should return False for own Candidate if Agency assigned and member is not"""
        r = f.create_recruiter(self.agency)
        candidate = f.create_candidate(self.agency)
        job = f.get_job_assigned_to_agency(self.agency)

        self.assertFalse(r.profile.can_create_proposal(job, candidate))

    def test_can_create_proposal_own_candidate_not_assigned(self):
        """Should return False for own Candidate and not assigned Job."""
        r = f.create_recruiter(self.agency)
        candidate = f.create_candidate(self.agency)
        job = f.create_job(f.create_client())

        self.assertFalse(r.profile.can_create_proposal(job, candidate))

    def test_can_create_proposal_other_candidate_agency_assigned(self):
        """Should return False for other Candidate and assigned Job."""
        r = f.create_recruiter(self.agency)
        job = f.get_job_assigned_to_agency(self.agency)
        candidate = f.create_candidate(f.create_agency())

        self.assertFalse(r.profile.can_create_proposal(job, candidate))

    def test_can_create_proposal_other_candidate_not_assigned(self):
        """Should return False for other Candidate and not assigned Job."""
        r = f.create_recruiter(self.agency)
        job = f.create_job(f.create_client())
        candidate = f.create_candidate(f.create_agency())

        self.assertFalse(r.profile.can_create_proposal(job, candidate))

    def test_can_create_job_file(self):
        """Should return False."""
        r = f.create_recruiter(self.agency)
        job = f.get_job_assigned_to_agency(self.agency)
        job.assign_member(r)

        self.assertFalse(r.profile.can_create_job_file(job))

    def test_deleted_when_agency_deleted(self):
        """Recruiter deleted when Agency is deleted."""
        agency = f.create_agency()
        m.Recruiter.objects.create(agency=agency, user=self.user)
        agency.delete()

        self.assertEqual(m.Recruiter.objects.count(), 0)


class CandidateTests(TestCase):
    """Tests related to the Candidate model."""

    def setUp(self):
        """Create an Agency during setup process of a test object."""
        super().setUp()
        self.agency = f.create_agency()

    def test_candidate_created(self):
        """Candidate succesfully created."""
        candidate = f.create_candidate(self.agency)

        self.assertEqual(m.Candidate.objects.get(pk=candidate.pk), candidate)

    def test_candidate_name_length_128(self):
        """Candidate successfully created when the name is 128 length."""
        candidate = f.create_candidate(self.agency, first_name='a' * 128,)

        self.assertEqual(m.Candidate.objects.get(pk=candidate.pk), candidate)

    def test_candidate_name_length_129(self):
        """Data Error raised when the name is more than 128 length."""
        with self.assertRaises(ValidationError):
            f.create_candidate(self.agency, first_name='a' * 129)

    def test_candidate_str(self):
        """Candidate string representation should contain their name."""
        candidate = f.create_candidate(
            self.agency, first_name='Test', last_name='Candidate'
        )

        self.assertEqual('Test Candidate', str(candidate))

    def test_get_note(self):
        """Returns the CandidateNote related to Candidate and Organization."""
        candidate = f.create_candidate(self.agency)
        f.create_candidate_note(candidate, self.agency)

        self.assertEqual(
            candidate.get_note(self.agency), f.DEFAULT_CANDIDATE_NOTE['text']
        )

    def test_get_note_without_note(self):
        """Returns empty str if no note for Candidate and Organization."""
        candidate = f.create_candidate(self.agency)

        self.assertEqual(candidate.get_note(self.agency), '')

    def test_set_note_create(self):
        """Creates a note if does not exist."""
        candidate = f.create_candidate(self.agency)
        candidate.set_note(self.agency, 'Some note')

        self.assertEqual(m.CandidateNote.objects.count(), 1)
        self.assertEqual(m.CandidateNote.objects.first().text, 'Some note')

    def test_set_note_create_text_none(self):
        """Creates a note with an empty string if the text is None."""
        candidate = f.create_candidate(self.agency)
        candidate.set_note(self.agency, None)

        self.assertEqual(m.CandidateNote.objects.count(), 1)
        self.assertEqual(m.CandidateNote.objects.first().text, '')

    def test_set_note_update(self):
        """Note text updated if note exists and different text passed."""
        candidate = f.create_candidate(self.agency)
        f.create_candidate_note(candidate, self.agency)
        candidate.set_note(self.agency, 'New text 42')

        self.assertEqual(m.CandidateNote.objects.first().text, 'New text 42')

    def test_set_note_update_same_text(self):
        """Note text not changed if the same text passed."""
        candidate = f.create_candidate(self.agency)
        note = f.create_candidate_note(candidate, self.agency, 'Note text')
        candidate.set_note(self.agency, 'Note text')

        self.assertEqual(m.CandidateNote.objects.count(), 1)
        self.assertEqual(note.text, m.CandidateNote.objects.first().text)

    def test_set_note_update_text_none(self):
        """Updates a note with an empty string if the text is None."""
        candidate = f.create_candidate(self.agency)
        f.create_candidate_note(candidate, self.agency, 'Note text')
        candidate.set_note(self.agency, None)

        self.assertEqual(m.CandidateNote.objects.count(), 1)
        self.assertEqual(m.CandidateNote.objects.first().text, '')

    def test_deleted_when_agency_deleted(self):
        """Candidate deleted when Agency is deleted."""
        agency = f.create_agency()
        f.create_candidate(agency)
        agency.delete()

        self.assertEqual(m.Candidate.objects.count(), 0)

    def test_default_values(self):
        """Check Candidate default values."""
        candidate = f.create_candidate(
            organization=self.agency,
            first_name='Test',
            last_name='name',
            summary='Test Resume',
        )

        self.assertFalse(candidate.fulltime)
        self.assertFalse(candidate.parttime)
        self.assertFalse(candidate.local)
        self.assertFalse(candidate.remote)

    def test_linkedin_slug(self):
        """Check linkedin_slug set on save."""
        linkedin_url = 'https://linkedin.com/in/some-slug/'
        linkedin_slug = parse_linkedin_slug(linkedin_url)

        candidate = f.create_candidate(
            organization=self.agency,
            first_name='Test',
            last_name='name',
            summary='Test Resume',
            linkedin_url=linkedin_url,
        )

        self.assertEqual(candidate.linkedin_slug, linkedin_slug)

    def test_linkedin_data(self):
        """Check linkedin_data property."""
        candidate = f.create_candidate(
            organization=self.agency,
            first_name='Test',
            last_name='name',
            summary='Test Resume',
        )
        d = {'x': 1}
        m.CandidateLinkedinData.objects.create(candidate=candidate, data=d)

        self.assertEqual(candidate.linkedin_data, d)

    def test_linkedin_data_none(self):
        """Check linkedin_data property when no data."""
        candidate = f.create_candidate(self.agency)

        self.assertEqual(candidate.linkedin_data, None)

    def test_candidates_objects_manager(self):
        """Should return only non-archived candidated"""
        agency = f.create_agency()
        candidate = f.create_candidate(agency)

        candidate.archived = True
        candidate.save()

        self.assertEqual(m.Candidate.objects.count(), 0)

    def test_candidates_archived_objects_manager(self):
        """Archived candidates should be in the queryset"""
        agency = f.create_agency()
        candidate = f.create_candidate(agency)
        candidate_2 = f.create_candidate(agency)

        candidate.archived = True
        candidate.save()

        self.assertEqual(m.Candidate.archived_objects.count(), 2)

    def test_candidates_email_exists(self):
        """Email must be unique"""
        candidate = f.create_candidate(self.agency)
        with self.assertRaises(ValidationError) as e:
            f.create_candidate(self.agency, email=candidate.email)
            self.assertEqual(e.message_dict, {'email': 'Email already in use.'})

    def test_candidates_secondary_email_exists(self):
        """Secondary email should be unique"""
        candidate = f.create_candidate(self.agency)
        with self.assertRaises(ValidationError) as e:
            f.create_candidate(self.agency, secondary_email=candidate.email)
            self.assertEqual(
                e.message_dict, {'secondaty_email': 'Email already in use.'}
            )

    def test_equal_emails(self):
        """Both of emails must be unique"""
        email = f.generate_email()
        with self.assertRaises(ValidationError) as e:
            f.create_candidate(self.agency, email=email, secondary_email=email)
            self.assertEqual(
                e.message_dict,
                {
                    'email': 'Emails must be unique.',
                    'secondary_email': 'Emails must be unique.',
                },
            )

    def test_zoho_id_exists(self):
        """Zoho ID must be unique"""
        zoho_id = 128256512
        f.create_candidate(self.agency, zoho_id=zoho_id)
        with self.assertRaises(ValidationError) as e:
            f.create_candidate(self.agency, zoho_id=zoho_id)
            self.assertEqual(
                e.message_dict,
                {'zoho_id': 'Candidate with this Zoho ID already exists.'},
            )

    def test_linkedin_url_exists(self):
        """LinkedIn url must be unique"""
        linkedin_url = 'https://www.linkedin.com/in/richardthelionheart/'
        f.create_candidate(self.agency, linkedin_url=linkedin_url)
        with self.assertRaises(ValidationError) as e:
            f.create_candidate(self.agency, linkedin_url=linkedin_url)
            self.assertEqual(
                e.message_dict,
                {'linkedin_url': 'Candidate with this LinkedIn already exists.'},
            )


class CandidateNoteTests(TestCase):
    """Tests related to the CandidateNote model."""

    def setUp(self):
        """Create Agency and Candidate during setup process."""
        super().setUp()
        self.agency = f.create_agency()
        self.client = f.create_client()
        self.candidate = f.create_candidate(self.agency)

    def test_candidate_note_for_agency_created(self):
        """Candidate note for the Agency successfully created."""
        note = m.CandidateNote.objects.create(
            candidate=self.candidate, organization=self.agency, text='Test note'
        )

        self.assertEqual(m.CandidateNote.objects.get(pk=note.pk), note)

    def test_candidate_note_for_client_created(self):
        """Candidate note for the Client successfully created."""
        note = m.CandidateNote.objects.create(
            candidate=self.candidate, organization=self.client, text='Test note'
        )

        self.assertEqual(m.CandidateNote.objects.get(pk=note.pk), note)

    def test_candidate_note_without_candidate_not_created(self):
        """Integirty error raised when creating without Candidate."""
        with self.assertRaises(IntegrityError):
            m.CandidateNote.objects.create(organization=self.client, text='Test note')

    def test_candidate_note_without_organization_not_created(self):
        """Integrity error raised when creating without Organization."""
        with self.assertRaises(IntegrityError):
            m.CandidateNote.objects.create(candidate=self.candidate, text='Test note')

    def test_candidate_note_without_text_created(self):
        """Candidate note without text successfully created."""
        note = m.CandidateNote.objects.create(
            candidate=self.candidate, organization=self.client,
        )

        self.assertEqual(m.CandidateNote.objects.get(pk=note.pk), note)
        self.assertEqual(note.text, '')

    def test_candidate_note_unique(self):
        """Integrity error raised for 2nd note with same Org and Candidate."""
        m.CandidateNote.objects.create(
            candidate=self.candidate, organization=self.agency, text='Test note'
        )

        with self.assertRaises(IntegrityError):
            m.CandidateNote.objects.create(
                candidate=self.candidate,
                organization=self.agency,
                text='Other test note',
            )

    def test_candidate_str(self):
        """Candidate note string should contain Organization and Candidate."""
        note = m.CandidateNote.objects.create(
            candidate=self.candidate, organization=self.agency, text='Test note'
        )

        self.assertEqual(
            str(note), 'Note for {} by {}'.format(self.candidate, self.agency)
        )

    def test_deleted_when_candidate_deleted(self):
        """Candidate Note deleted when Candidate is deleted."""
        candidate = f.create_candidate(self.agency)
        f.create_candidate_note(candidate, self.agency)
        candidate.delete()

        self.assertEqual(m.CandidateNote.objects.count(), 0)

    def test_deleted_when_organization_deleted(self):
        """Candiate Note deleted when Organization is deleted."""
        agency = f.create_agency()
        f.create_candidate_note(self.candidate, agency)
        agency.delete()

        self.assertEqual(m.CandidateNote.objects.count(), 0)


class ProposalTests(TestCase):
    """Tests related to the Proposal model."""

    def setUp(self):
        """Create Client and Job during setup process of a test object."""
        super().setUp()

        self.client = f.create_client()
        self.job = f.create_job(self.client)

        self.agency = f.create_agency()
        self.recruiter = f.create_recruiter(self.agency)
        self.candidate = f.create_candidate(self.agency)

    def test_proposal_without_approved_created(self):
        """Proposal successfully created when all required arguments passed."""
        proposal = m.Proposal.objects.create(
            job=self.job, candidate=self.candidate, created_by=self.recruiter
        )

        self.assertEqual(m.Proposal.objects.get(pk=proposal.pk), proposal)

    def test_proposal_without_job(self):
        """Intergrity Error raised when the job not passed."""
        with self.assertRaises(IntegrityError):
            m.Proposal.objects.create(candidate=self.candidate)

    def test_proposal_without_candidate(self):
        """Intergirity Error rasised when the candidate not passed."""
        with self.assertRaises(IntegrityError):
            m.Proposal.objects.create(job=self.job)

    def test_proposal_unique_together(self):
        """Integrity Error raised when passed not unique pair of objects."""
        m.Proposal.objects.create(
            job=self.job, candidate=self.candidate, created_by=self.recruiter
        )
        with self.assertRaises(IntegrityError):
            m.Proposal.objects.create(
                job=self.job, candidate=self.candidate, created_by=self.recruiter
            )

    def test_proposal_str(self):
        """Proposal string representation should Job and Candidate names."""
        proposal = f.create_proposal(self.job, self.candidate, self.recruiter)

        self.assertEqual(str(proposal), '{} - {}'.format(self.job, self.candidate))

    def test_proposal_source_property(self):
        """Should return Candidate's Agency."""
        proposal = f.create_proposal(self.job, self.candidate, self.recruiter)

        self.assertEqual(proposal.source, self.candidate.organization)

    def test_status_default_on_save(self):
        """Should set "new" proposal status."""
        default_status = (
            self.client.proposal_statuses.filter(
                status__stage=m.ProposalStatusStage.ASSOCIATED.key
            )
            .first()
            .status
        )

        proposal = m.Proposal.objects.create(
            job=self.job, candidate=self.candidate, created_by=self.recruiter
        )

        self.assertEqual(proposal.status, default_status)

    def test_deleted_when_job_deleted(self):
        """Proposal deleted when Job is deleted."""
        job = f.create_job(self.client)
        f.create_proposal(job, self.candidate, self.recruiter)
        job.delete()

        self.assertEqual(m.Proposal.objects.count(), 0)

    def test_deleted_when_candidate_deleted(self):
        """Proposal deleted when Candidate is deleted."""
        candidate = f.create_candidate(self.agency)
        f.create_proposal(self.job, candidate, self.recruiter)
        candidate.delete()

        self.assertEqual(m.Proposal.objects.count(), 0)

    def test_decline_same_candidate_proposals(self):
        job_1 = f.create_job(self.agency)
        job_2 = f.create_job(self.agency)
        job_3 = f.create_job(self.agency)
        candidate_1 = f.create_candidate(self.agency)

        proposal_1 = f.create_proposal(job_1, candidate_1, self.recruiter)
        proposal_2 = f.create_proposal(job_2, candidate_1, self.recruiter)
        proposal_3 = f.create_proposal(job_3, candidate_1, self.recruiter)

        offer_accepted_status = m.ProposalStatus.objects.filter(
            group=m.ProposalStatusGroup.PENDING_START.key
        ).first()

        # candidate became hired
        proposal_3.status = offer_accepted_status
        proposal_3.save()
        proposal_3.decline_same_candidate_proposals(self.recruiter)

        proposal_1.refresh_from_db()
        proposal_2.refresh_from_db()

        self.assertTrue(proposal_1.is_rejected)
        self.assertTrue(proposal_2.is_rejected)
        self.assertFalse(proposal_3.is_rejected)


class NotificationTests(TestCase):
    """Tests related to Notification."""

    def setUp(self):
        """Create required objects during setup process."""
        self.client = f.create_client()
        self.user = f.create_recruiter(f.create_agency())
        self.agency = f.create_agency()

    @patch('core.tasks.send_email.delay')
    def test_send(self, send_email_mock):
        """Should send notification."""
        n = m.Notification.send(
            self.user,
            m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
            actor=self.client,
            action_object=self.agency,
        )

        self.assertIsNotNone(n)
        self.assertEqual(self.user.unread_notifications_count, 1)

        send_email_mock.assert_called_with(
            subject='Notification',
            body=n.email_text,
            html_body='<p>Test Client has invited you to view '
            'their open positions on the ZooKeep platform.</p>\n\n',
            to=[self.user.email],
            reply_to=[None],
            attachments=None,
        )

    def test_link(self):
        """Should return link."""
        job = f.create_job(self.client)

        n = m.Notification.send(
            self.user,
            m.NotificationTypeEnum.CLIENT_ASSIGNED_AGENCY_FOR_JOB,
            actor=self.client,
            target=job,
        )

        self.assertEqual(n.link, job.get_absolute_url())


class ProposalStatusTests(TestCase):
    """Tests related to ProposalStatus."""

    def test_default_statuses_are_created(self):
        """Default proposal statuses should be created."""
        for group in m.ProposalStatusGroup.get_keys():
            self.assertTrue(
                m.ProposalStatus.objects.filter(group=group, default=True,).count() > 0
            )

    def test_clean_default_order(self):
        """Should raise an error, if default, but no default order."""
        s = m.ProposalStatus(
            group=m.PROPOSAL_STATUS_GROUP_CHOICES[0][0], status='123', default=True
        )

        with self.assertRaises(ValidationError):
            s.clean()

    def test_default_statuses_are_ordered(self):
        """Default proposal statuses should have default order."""
        self.assertEqual(
            m.ProposalStatus.objects.filter(default=True).count(),
            m.ProposalStatus.objects.filter(default_order__isnull=False).count(),
        )


class ProposalCommentTests(TestCase):
    """Tests for ProposalComment model."""

    def setUp(self):
        """Create required objects for proposa comments."""
        super().setUp()

        self.client = f.create_client()
        self.job = f.create_job(self.client)

        self.agency = f.create_agency()
        self.recruiter = f.create_recruiter(self.agency)
        self.candidate = f.create_candidate(self.agency)
        self.proposal = f.create_proposal(
            self.job, self.candidate, f.create_client_administrator(self.client)
        )

    def test_proposal_comment_created(self):
        """Proposal comment successfully created."""
        comment = m.ProposalComment.objects.create(
            author=self.recruiter,
            proposal=self.proposal,
            text='Test comment',
            public=True,
        )

        self.assertEqual(m.ProposalComment.objects.get(pk=comment.pk), comment)

    def test_proposal_comment_public_default(self):
        """Proposal comment default is not public."""
        comment = m.ProposalComment.objects.create(
            author=self.recruiter, proposal=self.proposal, text='Test comment'
        )

        self.assertFalse(comment.public)

    def test_deleted_with_proposal(self):
        """Proposal comment deleted along with Proposal."""
        comment = m.ProposalComment.objects.create(
            author=self.recruiter, proposal=self.proposal, text='Test comment'
        )

        self.proposal.delete()

        with self.assertRaises(m.ProposalComment.DoesNotExist):
            m.ProposalComment.objects.get(pk=comment.pk)

    def test_author_set_null_when_deleted(self):
        """Proposal comment User field set to None when User deleted."""
        comment = m.ProposalComment.objects.create(
            author=self.recruiter, proposal=self.proposal, text='Test comment'
        )

        self.recruiter.delete()

        comment.refresh_from_db()
        self.assertIsNone(comment.author)

    def test_proposal_status_set_null_when_deleted(self):
        """Proposal comment proposal_status field set to None when deleted."""
        status = m.ProposalStatus.objects.create(group='new', status='test')
        old_status = self.proposal.status
        self.proposal.status = status
        self.proposal.save()

        comment = m.ProposalComment.objects.create(
            author=self.recruiter, proposal=self.proposal, text='Test comment'
        )

        self.proposal.status = old_status
        self.proposal.save()
        status.delete()

        comment.refresh_from_db()
        self.assertIsNone(comment.proposal_status)

    def test_str(self):
        """Propoal comment str should include Proposal in it."""
        comment = m.ProposalComment.objects.create(
            author=self.recruiter, proposal=self.proposal, text='Test comment'
        )

        self.assertEqual(str(comment), 'Comment on {}'.format(self.proposal))


class NoteActivityTests(TestCase):
    def setUp(self):
        super().setUp()
        self.proposal = fa.ClientProposalFactory()
        self.job = self.proposal.job
        self.candidate = self.proposal.candidate
        self.admin = self.proposal.job.owner

    def test_create_proposal_note(self):
        note = fa.NoteActivityFactory(
            author=self.admin,
            proposal=self.proposal,
            candidate=self.candidate,
            job=self.job,
        )
        self.assertIsNotNone(note)

    def test_create_proposal_note_missing_fields(self):
        """passed proposal with missing candidate or job"""
        required_fields_if_proposal = ['candidate', 'job']
        for field in required_fields_if_proposal:
            with transaction.atomic():
                note = fa.NoteActivityFactory.build(
                    author=self.admin,
                    proposal=self.proposal,
                    candidate=self.candidate,
                    job=self.job,
                )
                setattr(note, field, None)
                note.save()
                self.assertEqual(getattr(self, field), getattr(note, field))

    def test_create_candidate_note(self):
        note = fa.NoteActivityFactory(author=self.admin, candidate=self.candidate)
        self.assertIsNotNone(note)

    def test_create_job_note(self):
        note = fa.NoteActivityFactory(author=self.admin, job=self.job)
        self.assertIsNotNone(note)

    def test_create_job_maybe_candidate_note(self):
        """passed both candidate and job"""
        note = fa.NoteActivityFactory.build(
            author=self.admin, candidate=self.candidate, job=self.job
        )
        with self.assertRaises(IntegrityError):
            note.save()
