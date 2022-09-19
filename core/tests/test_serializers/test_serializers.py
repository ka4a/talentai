"""Tests related to serializers of the core Django app."""
from datetime import timedelta
import tempfile
from unittest.mock import Mock, call, patch

from django.utils.timezone import datetime, utc
from django.utils import translation
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.test import TestCase, RequestFactory, override_settings
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.serializers import ValidationError, PrimaryKeyRelatedField
from rest_framework.test import APITestCase, APIRequestFactory

from core import fixtures as f
from core import models as m
from core import serializers as s
from core.annotations import (
    annotate_job_agency_member_have_access_since,
    annotate_job_hired_count,
    annotate_proposal_deal_pipeline_metrics,
)
from core import factories as fa
from core.serializer_fields import (
    CandidatePrimaryKeyRelatedField,
    JobPrimaryKeyRelatedField,
)

User = get_user_model()
factory = APIRequestFactory()


def get_contract_serializer_result(
    contract,
    client,
    agency,
    jobs_queryset=None,
    is_client_signed=False,
    is_agency_signed=False,
):
    jobs = []
    if jobs_queryset is not None:
        jobs = (
            {'id': job[0], 'title': job[1]}
            for job in jobs_queryset.values('id', 'title')
        )

    response_data = {
        'id': contract.id,
        'status': contract.status,
        'agency': {'id': agency.id, 'name': agency.name},
        'client': {'id': client.id, 'name': client.name},
        'jobs': jobs,
        'start_at': '2019-01-01',
        'end_at': '2119-01-01',
        'fee_currency': 'JPY',
        'initial_fee': None,
        'fee_rate': None,
        'is_client_signed': is_client_signed,
        'is_agency_signed': is_agency_signed,
        'days_until_invitation_expire': m.CONTRACT_DEFAULT_INVITATION_DURATION,
    }
    return response_data


class UserLoginTests(APITestCase):
    """Tests related to the UserLogin serializer."""

    def setUp(self):
        """Create a User during set up process."""
        self.password = 'password'
        self.user = f.create_user(
            'a@test.com', self.password, first_name='First', last_name='Last',
        )

    def test_user_login_serializer(self):
        """Serializer should not return any data."""
        serializer = s.UserLoginSerializer(
            {'email': self.user.email, 'password': self.password}
        )

        self.assertEqual(serializer.data, {})

    def test_user_login_user_property(self):
        """User property returns a User with the given email."""
        serializer = s.UserLoginSerializer(
            data={'email': self.user.email, 'password': self.password}
        )

        self.assertEqual(serializer.user, self.user)

    def test_user_login_user_property_wrong_password(self):
        """User property returns None if password is not valid."""
        serializer = s.UserLoginSerializer(
            data={'email': self.user.email, 'password': 'incorrect'}
        )

        self.assertIsNone(serializer.user)

    def test_user_login_user_property_not_existing_email(self):
        """User property returns None is User with given email not exist."""
        serializer = s.UserLoginSerializer(
            data={'email': 'no@test.com', 'password': self.password}
        )

        self.assertIsNone(serializer.user)


class StaffTests(APITestCase):
    """Tests for the Staff serializer."""

    def setUp(self):
        """Create Agency user during test class initialization."""
        super().setUp()
        self.recruiter = f.create_recruiter(f.create_agency())

    def test_agency_staff_serializer(self):
        """Should contain the correct data form the related model."""
        serializer = s.StaffSerializer(self.recruiter)

        self.assertDictEqual(
            serializer.data,
            {
                'id': self.recruiter.id,
                'first_name': self.recruiter.first_name,
                'last_name': self.recruiter.last_name,
                'email': self.recruiter.email,
                'is_active': self.recruiter.is_active,
                'photo': None,
                'group': self.recruiter.profile.group_name,
            },
        )


class RetrieveStaffTests(APITestCase):
    """Tests for the Staff serializer."""

    def setUp(self):
        """Create Agency user during test class initialization."""
        super().setUp()
        self.recruiter = f.create_client_internal_recruiter(f.create_client())

    def test_agency_staff_serializer(self):
        """Should contain the correct data form the related model."""
        dummy_date = datetime(2021, 1, 1)

        self.recruiter.date_joined = dummy_date
        self.recruiter.last_login = dummy_date

        serializer = s.RetrieveStaffSerializer(self.recruiter)

        self.assertDictEqual(
            serializer.data,
            {
                'id': self.recruiter.id,
                'first_name': self.recruiter.first_name,
                'last_name': self.recruiter.last_name,
                'email': self.recruiter.email,
                'is_active': self.recruiter.is_active,
                'locale': self.recruiter.locale,
                'country': self.recruiter.country,
                'photo': None,
                'group': self.recruiter.profile.group_name,
                'date_joined': '2021-01-01T00:00:00Z',
                'last_login': '2021-01-01T00:00:00Z',
            },
        )


class ClientTests(APITestCase):
    """Tests related to the Client serializer."""

    def setUp(self):
        """Create Client during test class initialization."""
        super().setUp()
        self.client_obj = f.create_client()

        self.agency = f.create_agency()
        self.recruiter = f.create_recruiter(self.agency)

    def test_client_serializer(self):
        """Should contain the correct data from the related model."""
        request = RequestFactory().post('/')
        request.user = self.recruiter

        serializer = s.ClientSerializer(self.client_obj, context={'request': request})

        self.assertDictEqual(
            serializer.data,
            {
                'id': self.client_obj.pk,
                'name': f.DEFAULT_CLIENT['name'],
                'proposals_count': 0,
                'open_jobs_count': 0,
                'owner_agency_id': None,
                'country': self.client_obj.country,
            },
        )

    def test_get_proposals_count_agency_user(self):
        """Should return number of proposals for client by current agency."""
        candidate = f.create_candidate(self.agency)

        for i in range(3):
            job = f.create_job(self.client_obj)
            f.create_proposal(job, candidate, self.recruiter)

        another_agency = f.create_agency()
        another_candidate = f.create_candidate(another_agency)
        f.create_contract(another_agency, self.client_obj)
        job = f.create_job(self.client_obj)
        f.create_proposal(job, another_candidate, f.create_recruiter(another_agency))

        request = RequestFactory().post('/')
        request.user = self.recruiter

        serializer = s.ClientSerializer(self.client_obj, context={'request': request})

        self.assertEqual(serializer.data['proposals_count'], 3)

    def test_get_proposals_count_client_user(self):
        """Should not return number of proposals."""
        candidate = f.create_candidate(self.agency)

        job = f.create_job(self.client_obj)
        f.create_proposal(job, candidate, self.recruiter)

        request = RequestFactory().post('/')
        request.user = f.create_client_administrator(self.client_obj)

        serializer = s.ClientSerializer(self.client_obj, context={'request': request})

        self.assertIsNone(serializer.data['proposals_count'])

    def test_get_open_jobs_count_agency_user(self):
        """Should return number of open jobs."""
        for i in range(3):
            job = f.get_job_assigned_to_agency(self.agency, self.client_obj)
            job.assign_member(self.recruiter)

        another_agency = f.create_agency()
        f.get_job_assigned_to_agency(another_agency, self.client_obj)

        request = RequestFactory().post('/')
        request.user = self.recruiter

        serializer = s.ClientSerializer(self.client_obj, context={'request': request})

        self.assertEqual(serializer.data['open_jobs_count'], 3)

    def test_get_open_jobs_count_client_user(self):
        """Should not return number of open jobs."""
        candidate = f.create_candidate(self.agency)

        job = f.create_job(self.client_obj)
        f.create_proposal(job, candidate, self.recruiter)

        request = RequestFactory().post('/')
        request.user = f.create_client_administrator(self.client_obj)

        serializer = s.ClientSerializer(self.client_obj, context={'request': request})

        self.assertIsNone(serializer.data['open_jobs_count'])


class JobPublicTests(APITestCase):
    """Tests related to the Job Public serializer."""

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def setUp(self):
        """Create Client and Job during test class initialization."""
        super().setUp()
        self.agency = f.create_agency()
        self.recruiter = f.create_recruiter(self.agency)
        client = f.create_client()
        self.job = f.create_job(client)
        self.job.assign_agency(self.agency)
        self.language = m.Language.objects.get(language='en', level=0)
        self.job.required_languages.add(self.language)
        self.candidate = f.create_candidate(self.agency)
        self.proposal = f.create_proposal(self.job, self.candidate, self.recruiter)
        self.hm = f.create_hiring_manager(f.create_client())
        self.job.assign_manager(self.hm)

        m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=self.job
        )

    def test_job_public_serializer(self):
        """Should contain the correct data from the related model."""
        serializer = s.JobPublicSerializer(self.job)

        with translation.override('en'):
            job_location = self.job.location

        self.assertDictEqual(
            serializer.data,
            {
                'id': self.job.pk,
                'organization': {
                    'id': self.job.org_id,
                    'type': 'client',
                    'name': self.job.organization.name,
                    'name_ja': self.job.organization.name_ja,
                    'logo': None,
                },
                'title': self.job.title,
                'country': self.job.country,
                'employment_type': self.job.employment_type,
                'questions': s.JobQuestionSerializer(
                    self.job.questions, many=True
                ).data,
                'status': self.job.status,
                'published': self.job.published,
                'files': s.JobFileSerializer(self.job.jobfile_set, many=True).data,
                'location': job_location,
                'function': self.job.function,
                'mission': self.job.mission,
                'responsibilities': self.job.responsibilities,
                'requirements': self.job.requirements,
                'skills': [],
                'required_languages': [s.LanguageSerializer(self.language).data],
                'salary_currency': self.job.salary_currency,
                'salary_from': self.job.salary_from,
                'salary_to': self.job.salary_to,
                'salary_per': self.job.salary_per,
                'bonus_system': self.job.bonus_system,
                'probation_period_months': self.job.probation_period_months,
                'work_location': self.job.work_location,
                'working_hours': self.job.working_hours,
                'break_time_mins': self.job.break_time_mins,
                'flexitime_eligibility': self.job.flexitime_eligibility,
                'telework_eligibility': self.job.telework_eligibility,
                'overtime_conditions': self.job.overtime_conditions,
                'paid_leaves': self.job.paid_leaves,
                'additional_leaves': self.job.additional_leaves,
                'social_insurances': self.job.social_insurances,
                'commutation_allowance': self.job.commutation_allowance,
                'other_benefits': self.job.other_benefits,
            },
        )


class ManagerAssignDismissTests(APITestCase):
    """Tests related to ManagerASsignDismiss serializer."""

    def setUp(self):
        """Create Hiring Manager and the Job."""
        super().setUp()
        self.client_obj = f.create_client()
        self.hm = f.create_hiring_manager(self.client_obj)
        self.job = f.create_job(self.client_obj)

        self.request = factory.get('/')
        self.request.user = f.create_client_administrator(self.client_obj)

    def test_data(self):
        """Should contain not contain any readable fields."""
        serializer = s.ManagerAssignRemoveFromJobSerializer(
            {'user': self.hm.pk, 'job': self.job.pk}, context={'request': self.request}
        )

        self.assertEqual(serializer.data, {})

    def test_user_validation_client_admin(self):
        """Should not raise any errors if Client Admin passed."""
        client_admin = f.create_client_administrator(self.client_obj)
        serializer = s.ManagerAssignRemoveFromJobSerializer(
            data={'user': client_admin.pk, 'job': self.job.pk},
            context={'request': self.request},
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_user_validation_client_internal_recruiter(self):
        """Should not raise any errors if Client Internal Recruiter passed."""
        client_recruiter = f.create_client_internal_recruiter(self.client_obj)
        serializer = s.ManagerAssignRemoveFromJobSerializer(
            data={'user': client_recruiter.pk, 'job': self.job.pk},
            context={'request': self.request},
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_user_validation_recruiter(self):
        """Should raise ValidationError if Recruiter passed."""
        r = f.create_recruiter(f.create_agency())

        serializer = s.ManagerAssignRemoveFromJobSerializer(
            data={'user': r.pk, 'job': self.job.pk}, context={'request': self.request}
        )

        error_msg = 'Invalid pk "{}" - object does not exist.'.format(r.pk)
        with self.assertRaisesMessage(ValidationError, error_msg):
            serializer.is_valid(raise_exception=True)

    def test_user_validation_hiring_manager(self):
        """Should not raise any errors if Hiring Manager passed."""
        serializer = s.ManagerAssignRemoveFromJobSerializer(
            data={'user': self.hm.pk, 'job': self.job.pk},
            context={'request': self.request},
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_validation_user_and_job_different_clients(self):
        """Should raise ValidationError for not matching Job and User."""
        job_other = f.create_job(f.create_client())
        serializer = s.ManagerAssignRemoveFromJobSerializer(
            data={'user': self.hm.pk, 'job': job_other.pk},
            context={'request': self.request},
        )

        error_msg = 'User and Job should belong to the same Organization.'
        with self.assertRaisesMessage(ValidationError, error_msg):
            serializer.is_valid(raise_exception=True)

    def test_validation_user_and_job_same_client(self):
        """Should not raise ValidationError for matching Job and User."""
        serializer = s.ManagerAssignRemoveFromJobSerializer(
            data={'user': self.hm.pk, 'job': self.job.pk},
            context={'request': self.request},
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))


class ManagerInviteTests(APITestCase):
    """Tests related to ManagerInvite serializer."""

    def test_manager_invite_serializer(self):
        """Should be valid if first and last name, email passed."""
        serializer = s.ManagerInviteSerializer(
            data={
                'first_name': 'Test',
                'last_name': 'Manager',
                'email': 'testmail@localhost',
            }
        )

        self.assertTrue(serializer.is_valid())


class JobAgencyTests(TestCase):
    """Tests related to JobManagerSerializers."""

    def setUp(self):
        """Create Agency during test class initialization."""
        super().setUp()
        self.agency = f.create_agency()

    def test_job_manager_serializer_talent_associate(self):
        """Talent Associate should get the list of Agencies."""
        request = factory.get('/')
        request.user = f.create_client_administrator(f.create_client())

        data = s.JobAgencySerializer(
            [self.agency], context={'request': request}, many=True
        ).data

        self.assertEqual(len(data), 1)

    def test_job_manager_serializer_hiring_manager(self):
        """Hiring Manager should not get the list of Agencies."""
        request = factory.get('/')
        request.user = f.create_hiring_manager(f.create_client())

        data = s.JobAgencySerializer(
            [self.agency], context={'request': request}, many=True
        ).data

        self.assertEqual(len(data), 1)

    def test_job_manager_serializer_recruiter(self):
        """Recruiter shouldn't get the list of Agencies."""
        request = factory.get('/')
        request.user = f.create_recruiter(f.create_agency())

        data = s.JobAgencySerializer(
            [self.agency], context={'request': request}, many=True
        ).data

        self.assertEqual(len(data), 0)

    def test_job_manager_serializer_agency_administator(self):
        """Agency Administrator shouldn't get the list of Agencies."""
        request = factory.get('/')
        request.user = f.create_agency_administrator(f.create_agency())

        data = s.JobAgencySerializer(
            [self.agency], context={'request': request}, many=True
        ).data

        self.assertEqual(len(data), 0)

    def test_job_manager_serializer_agency_manager(self):
        """Agency Manager shouldn't get the list of Agencies."""
        request = factory.get('/')
        request.user = f.create_agency_manager(f.create_agency())

        data = s.JobAgencySerializer(
            [self.agency], context={'request': request}, many=True
        ).data

        self.assertEqual(len(data), 0)


class JobSerializerTests(APITestCase):
    """JobSerializer tests."""

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def setUp(self):
        """Create Client and Job during test class initialization."""
        super().setUp()
        self.agency = f.create_agency()
        self.recruiter = f.create_recruiter(self.agency)

        self.client_obj = f.create_client()

        self.job = f.get_job_assigned_to_agency(self.agency, self.client_obj)

        self.language = m.Language.objects.get(language='en', level=0)
        self.job.required_languages.add(self.language)
        self.candidate = f.create_candidate(self.agency)
        self.proposal = f.create_proposal(self.job, self.candidate, self.recruiter)
        self.hm = f.create_hiring_manager(self.client_obj)
        self.client_admin = f.create_client_administrator(self.client_obj)
        self.job.assign_manager(self.hm)
        self.job.assign_member(self.recruiter)

        m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'), job=self.job
        )

        self.request = factory.get('/')
        self.request.user = self.client_admin
        self.maxDiff = None

    def test_job_serializer(self):
        """Should contain the correct data from the related model."""
        job_qs = annotate_job_hired_count(m.Job.objects.filter(id=self.job.id))
        job = job_qs[0]

        with translation.override('en'):
            job_location = self.job.location
            serializer = s.JobSerializer(job, context={'request': self.request})
            serializer_data = serializer.data

        expected = {
            'id': job.pk,
            'organization': {
                'id': job.org_id,
                'name': job.organization.name,
                'name_ja': job.organization.name_ja,
                'type': 'client',
                'logo': None,
            },
            'agency_contracts': [
                {
                    'id': item.id,
                    'contract_type': item.contract_type,
                    'is_filled_in': item.is_filled_in,
                    'signed_at': item.signed_at,
                }
                for item in job.agency_contracts.all()
            ],
            'client_id': job.client.id,
            'client_name': job.client.name,
            'openings_count': job.openings_count,
            'hired_count': job.hired_count,
            'function': job.function_id,
            'title': job.title,
            'work_location': job.work_location,
            'responsibilities': job.responsibilities,
            'requirements': job.requirements,
            'salary_currency': job.salary_currency,
            'salary_from': job.salary_from,
            'salary_to': job.salary_to,
            'salary_per': job.salary_per,
            'telework_eligibility': job.telework_eligibility,
            'employment_type': job.employment_type,
            'required_languages': [s.LanguageSerializer(self.language).data],
            'questions': s.JobQuestionSerializer(job.questions, many=True).data,
            'published': job.published,
            'files': s.JobFileSerializer(
                job.jobfile_set, context={'request': self.request}, many=True
            ).data,
            'priority': job.priority,
            'status': job.status,
            'agencies': [s.JobAgencySerializer(self.agency).data],
            'assignees': s.JobAssigneeSerializer(
                job.assignees, context={'request': self.request}, many=True
            ).data,
            'talent_associates': [],
            'managers': [
                s.PublicUserSerializer(self.hm, context={'request': self.request}).data
            ],
            'updated_at': f.to_iso_datetime(self.job.updated_at),
            'candidate_proposed': None,
            'user_has_access': None,
            'published_at': job.published_at,
            'closed_at': job.closed_at,
            'created_at': f.to_iso_datetime(self.job.created_at),
            'created_by': s.PublicUserSerializer(
                job.created_by, context={'request': self.request}
            ).data,
            'country': 'jp',
            'location': job_location,
            'recruiters': [],
            'work_experience': m.JobWorkExperience.NONE.key,
            'target_hiring_date': None,
            'department': self.job.department,
            'reason_for_opening': self.job.reason_for_opening,
            'mission': self.job.mission,
            'educational_level': self.job.educational_level,
            'bonus_system': self.job.bonus_system,
            'probation_period_months': self.job.probation_period_months,
            'working_hours': self.job.working_hours,
            'flexitime_eligibility': self.job.flexitime_eligibility,
            'break_time_mins': self.job.break_time_mins,
            'paid_leaves': self.job.paid_leaves,
            'additional_leaves': self.job.additional_leaves,
            'overtime_conditions': self.job.overtime_conditions,
            'social_insurances': set(),
            'commutation_allowance': self.job.commutation_allowance,
            'other_benefits': set(),
            'hiring_process': self.job.hiring_process,
            'hiring_criteria': s.HiringCriterionSerializer(
                self.job.hiring_criteria, many=True
            ).data,
            'skills': [],
            'proposals_pipeline': None,
            'interview_templates': [],
        }

        self.assertCountEqual(serializer_data, expected)

        self.assertDictEqual(serializer_data, expected)

    def test_validate_required_languages(self):
        """Should not be valid if Languages are not unique."""
        data = {
            'title': 'Test Job',
            'client': self.client_obj.pk,
            'position': 'Test Position',
            'work_location': 'Test Location',
            'responsibilities': 'Test Responsibilities',
            'questions': [],
            'required_languages': [
                {'language': 'en', 'level': 0},
                {'language': 'en', 'level': 1},
            ],
        }
        serializer = s.JobSerializer(data=data, context={'request': self.request})

        message = 'Should have only one level of each language.'
        self.assertFalse(serializer.is_valid())
        self.assertTrue(message in serializer.errors['required_languages'])

    def test_managers_talent_associate(self):
        """Talent Associate should get a list of managers."""
        request = factory.get('/')
        request.user = f.create_client_administrator(self.client_obj)

        serializer = s.JobSerializer(self.job, context={'request': request})

        self.assertEqual(
            serializer.data['managers'],
            s.PublicUserSerializer(
                self.job.managers, many=True, context={'request': self.request}
            ).data,
        )

    def test_managers_hiring_manager(self):
        """Hiring Manager should get a list of managers."""
        request = factory.get('/')
        request.user = self.hm

        serializer = s.JobSerializer(self.job, context={'request': request})

        self.assertEqual(
            serializer.data['managers'],
            s.PublicUserSerializer(self.job.managers, many=True).data,
        )

    def test_managers_recruiter(self):
        """Recruiter should get a list of managers."""
        request = factory.get('/')
        request.user = self.recruiter

        serializer = s.JobSerializer(self.job, context={'request': request})

        self.assertEqual(
            serializer.data['managers'],
            s.PublicUserSerializer(self.job.managers, many=True).data,
        )

    def test_talent_associates_recruiter(self):
        """Recruiter should get a list of talent associates."""
        request = factory.get('/')
        request.user = self.recruiter

        serializer = s.JobSerializer(self.job, context={'request': request})

        self.assertEqual(
            serializer.data['talent_associates'],
            s.PublicUserSerializer(
                self.job.organization.members.filter(talentassociate__isnull=False),
                many=True,
            ).data,
        )

    def test_get_candidate_proposed_true(self):
        """Should return candidate_proposed - True, if proposed."""
        serializer = s.JobSerializer(
            self.job,
            context={
                'request': self.request,
                'check_candidate_proposed': self.candidate,
            },
        )

        self.assertTrue(serializer.data['candidate_proposed'])

    def test_get_candidate_proposed_false(self):
        """Should return candidate_proposed - False, if not proposed."""
        another_candidate = f.create_candidate(self.agency)
        another_job = f.create_job(self.client_obj)
        f.create_proposal(another_job, another_candidate, self.recruiter)

        serializer = s.JobSerializer(
            self.job,
            context={
                'request': self.request,
                'check_candidate_proposed': another_candidate,
            },
        )

        self.assertFalse(serializer.data['candidate_proposed'])

    def test_get_user_has_access_true(self):
        """Should return user_has_access - True, if has access."""
        serializer = s.JobSerializer(
            self.job,
            context={'request': self.request, 'check_user_has_access': self.recruiter},
        )

        self.assertTrue(serializer.data['user_has_access'])

    def test_get_user_has_access_false(self):
        """Should return user_has_access - False, if has no access."""
        another_agency = f.create_agency()
        another_recruiter = f.create_recruiter(another_agency)

        serializer = s.JobSerializer(
            self.job,
            context={
                'request': self.request,
                'check_user_has_access': another_recruiter,
            },
        )

        self.assertFalse(serializer.data['user_has_access'])

    def test_get_user_has_access_not_client_member(self):
        """Should return user_has_access - None, if not client member."""
        request = factory.get('/')
        request.user = self.recruiter

        serializer = s.JobSerializer(
            self.job,
            context={'request': request, 'check_user_has_access': self.client_admin},
        )

        self.assertIsNone(serializer.data['user_has_access'])

    def test_agency_only_job_fields_agency(self):
        """Agency should has an access to the Agency-only job fields."""
        agency_admin = f.create_agency_administrator(self.agency)
        request = factory.get('/')
        request.user = agency_admin

        serializer = s.JobSerializer(self.job, context={'request': request})

        for field in s.AGENCY_ONLY_JOB_FIELDS:
            self.assertIn(field, serializer.data)

    def test_agency_only_job_fields_client(self):
        """Client can't see agency only job fields"""
        request = factory.get('/')
        request.user = self.client_admin

        serializer = s.JobSerializer(self.job, context={'request': request})

        for field in s.AGENCY_ONLY_JOB_FIELDS:
            self.assertNotIn(field, serializer.data)


class JobSerializerListTests(TestCase):
    """JobSerializerList tests."""

    def setUp(self):
        """Create related objects during test class initialization."""
        super().setUp()
        self.agency = f.create_agency()
        self.recruiter = f.create_recruiter(self.agency)

        self.client_obj = f.create_client()

        self.job = f.create_job(self.client_obj)

        self.request = factory.get('/')
        self.request.user = self.recruiter

    def get_have_access_since(self):
        job = annotate_job_agency_member_have_access_since(
            m.Job.objects, self.recruiter
        ).get(id=self.job.id)
        serializer = s.JobListSerializer(job, context={'request': self.request})
        return serializer['have_access_since'].value

    def test_have_access_since_recruiter_agency_assigned(self):
        """Recruiter should get have_access_since field."""
        self.job.assign_agency(self.agency)

        dt = self.get_have_access_since()
        job_agency = m.JobAgencyContract.objects.filter(
            job=self.job, agency=self.agency
        ).first()

        self.assertEqual(dt, s.represent_dt(job_agency.created_at))

    def test_have_access_since_assignee_member_assigned(self):
        """Recruiter should get have_access_since field."""
        self.job.assign_member(self.recruiter)

        dt = self.get_have_access_since()
        job_assignee = m.JobAssignee.objects.filter(
            job=self.job, user=self.recruiter
        ).first()

        self.assertEqual(dt, s.represent_dt(job_assignee.created_at))

    def test_have_access_since_assignee_both_assigned(self):
        """Assignee should get have_access_since field."""
        self.job.assign_agency(self.agency)
        self.job.assign_member(self.recruiter)

        dt = self.get_have_access_since()
        job_agency = m.JobAgencyContract.objects.filter(
            job=self.job, agency=self.agency
        ).first()

        self.assertEqual(dt, s.represent_dt(job_agency.created_at))

    def test_have_access_since_not_assignee(self):
        """Should not break for non-recruiters."""
        self.request.user = f.create_client_administrator(self.client_obj)

        dt = self.get_have_access_since()
        self.assertIsNone(dt)


class JobFileTests(TestCase):
    """Tests related to the JobFile serializer."""

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def setUp(self):
        """Create Job and Job file during initialization."""
        super().setUp()
        self.job = f.create_job(f.create_client())
        self.job_file = m.JobFile.objects.create(
            file=SimpleUploadedFile('file.txt', b'contents'),
            job=self.job,
            title='new file',
        )

    def test_job_file_serializer(self):
        """Should contain the correct data from the related model."""
        serializer = s.JobFileSerializer(self.job_file)

        self.assertDictEqual(
            serializer.data,
            {
                'id': self.job_file.pk,
                'file': self.job_file.file.url,
                'title': self.job_file.title,
                'job': self.job.pk,
                'thumbnail': None,
            },
        )


class CreateUpdateJobSerializerTests(APITestCase):
    """Tests related CreateUpdateJobSerializer."""

    def setUp(self):
        """Create Client and Job during test class initialization."""
        super().setUp()
        self.agency = f.create_agency()
        self.client = f.create_client()
        self.job = f.create_job(self.client)

    def test_update_question_ids(self):
        """Should not change IDs of changed questions."""
        question = m.JobQuestion.objects.create(job=self.job, text='1')
        data = {'questions': s.JobQuestionSerializer([question], many=True).data}

        request = RequestFactory().post('/doesntmatter')
        request.user = f.create_client_administrator(self.client)

        serializer = s.CreateUpdateJobSerializer(
            self.job, data=data, partial=True, context={'request': request}
        )
        serializer.is_valid()
        serializer.update(self.job, serializer.validated_data)
        self.job.save()

        try:
            question.refresh_from_db()
        except m.JobQuestion.DoesNotExist:
            self.fail('Original question row was deleted')

    def test_job_managers_change(self):
        """Should update managers."""
        request = RequestFactory().post('/doesntmatter')
        request.user = f.create_client_administrator(self.client)

        manager = f.create_hiring_manager(self.client)
        serializer = s.CreateUpdateJobSerializer(
            self.job,
            data={'managers': [manager.id]},
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()


class AgencySerializerTests(APITestCase):
    """AgencySerializer tests."""

    def setUp(self):
        """Create related objects during test class initialization."""
        super().setUp()
        self.agency = f.create_agency()

    def test_agency_serializer(self):
        """Should contain the correct data from the related model."""
        serializer = s.AgencySerializer(self.agency)

        self.assertDictEqual(
            serializer.data,
            {
                'id': self.agency.pk,
                'name': self.agency.name,
                'members': s.AgencyMemberSerializer(
                    self.agency.members, many=True
                ).data,
                'country': self.agency.country,
            },
        )


class TeamSerializerTests(TestCase):
    def setUp(self):
        super().setUp()
        self.team = m.Team.objects.create(
            name='Test team', organization=f.create_agency()
        )

    def test_agency_team_serializer(self):
        """Should contain the correct data from the related model."""
        serializer = s.TeamSerializer(self.team)

        self.assertDictEqual(
            serializer.data, {'id': self.team.pk, 'name': self.team.name,},
        )


class AgencyMemberSerializerTests(TestCase):
    """Tests for the AgencyRecruiter serializer."""

    def setUp(self):
        """Create related objects during test class initialization."""
        super().setUp()
        agency = f.create_agency()
        self.recruiter = f.create_recruiter(agency)

        team = m.Team.objects.create(name='Test team', organization=agency)
        self.recruiter.profile.teams.add(team)

    def test_agency_recruiter_serializer(self):
        """Should contain the correct data from the related model."""
        serializer = s.AgencyMemberSerializer(self.recruiter)

        self.assertDictEqual(
            serializer.data,
            {
                'id': self.recruiter.pk,
                'first_name': self.recruiter.first_name,
                'last_name': self.recruiter.last_name,
                'email': self.recruiter.email,
                'teams': s.TeamSerializer(self.recruiter.profile.teams, many=True).data,
            },
        )


class AgencyListSerializerTests(TestCase):
    """Tests related to AgencyListSerializer."""

    def setUp(self):
        """Create related objects during test class initialization."""
        super().setUp()
        self.agency = f.create_agency()
        self.recruiter = f.create_recruiter(self.agency)
        self.client_obj = f.create_client()
        self.contract = f.create_contract(self.agency, self.client_obj)

    def get_response_contract_details(self, *args, **kwargs):
        return get_contract_serializer_result(
            self.contract, self.client_obj, self.agency,
        )

    def test_agency_serializer(self):
        """Should contain the correct data from the related model."""
        request = RequestFactory().post('/doesntmatter')
        request.user = f.create_client_administrator(self.client_obj)

        function_focus = m.Function.objects.first()
        agency_category = m.AgencyCategory.objects.first()

        self.agency.website = 'https://example.com'
        self.agency.description = 'Lorem ipsum'
        self.agency.categories.add(agency_category)
        self.agency.function_focus.add(function_focus)
        self.agency.save()

        serializer = s.AgencyListSerializer(self.agency, context={'request': request})

        self.assertDictEqual(
            serializer.data,
            {
                'id': self.agency.pk,
                'name': self.agency.name,
                'name_ja': self.agency.name_ja,
                'website': self.agency.website,
                'logo': None,
                'description': self.agency.description,
                'contract': self.get_response_contract_details(),
                'proposals_count': 0,
                'members': s.AgencyMemberSerializer(
                    self.agency.members, many=True
                ).data,
                'categories': [agency_category.id],
                'function_focus': [function_focus.id],
            },
        )

    def test_agency_contracts_recruiter(self):
        """Should return Contract info for Recruiter."""
        serializer = s.AgencyListSerializer(self.agency)

        user = f.create_user('test@test.com', 'password')
        self.agency.assign_recruiter(user)

        request = Request(HttpRequest())
        request.user = user
        serializer.context['request'] = request

        self.assertDictEqual(
            serializer.data.get('contract'), self.get_response_contract_details()
        )

    def test_agency_contracts_talent_associate(self):
        """Should return Contract info for Talent Associate."""
        serializer = s.AgencyListSerializer(self.agency)

        user = f.create_user('test@test.com', 'password')
        self.client_obj.assign_administrator(user)

        request = Request(HttpRequest())
        request.user = user
        serializer.context['request'] = request

        self.assertDictEqual(
            serializer.data.get('contract'), self.get_response_contract_details()
        )

    def test_agency_contracts_hiring_manager(self):
        """Should return Contract info for Hiring Manager."""
        serializer = s.AgencyListSerializer(self.agency)

        user = f.create_user('test@test.com', 'password')
        self.client_obj.assign_standard_user(user)

        request = Request(HttpRequest())
        request.user = user
        serializer.context['request'] = request

        self.assertDictEqual(
            serializer.data.get('contract'), self.get_response_contract_details()
        )

    def test_agency_contracts_admin(self):
        """Should return no Contract info for Admin."""
        serializer = s.AgencyListSerializer(self.agency)

        user = f.create_superuser('test@test.com', 'password')

        request = Request(HttpRequest())
        request.user = user
        serializer.context['request'] = request

        self.assertEqual(serializer.data.get('contract'), None)

    def test_agency_proposals_count(self):
        """Should return number of proposals for particular client's jobs."""
        request = RequestFactory().post('/doesntmatter')
        request.user = f.create_client_administrator(self.client_obj)

        candidate = f.create_candidate(self.agency)

        for i in range(3):
            job = f.create_job(self.client_obj)
            f.create_proposal(job, candidate, self.recruiter)

        another_agency = f.create_agency()
        another_candidate = f.create_candidate(another_agency)
        f.create_contract(another_agency, self.client_obj)
        job = f.create_job(self.client_obj)
        f.create_proposal(job, another_candidate, f.create_recruiter(another_agency))

        serializer = s.AgencyListSerializer(self.agency, context={'request': request})

        self.assertEqual(serializer.data.get('proposals_count'), 3)


class LanguageSerializerTests(TestCase):
    """Tests related to the Language serializer."""

    def test_language_serializer(self):
        """Should contain the correct data from the related model."""
        language = m.Language.objects.get(language='en', level=0)
        serializer = s.LanguageSerializer(language)

        self.assertDictEqual(
            serializer.data,
            {
                'id': language.pk,
                'language': 'en',
                'level': 0,
                'formatted': 'Survival English',
            },
        )


class ContractTests(APITestCase):
    """Tests related to the Contract serializer."""

    def setUp(self):
        """Create Agency and Client during test class initialization."""
        super().setUp()
        self.agency = f.create_agency()

        self.client_obj = f.create_client()
        self.client_obj.primary_contact = f.create_client_administrator(self.client_obj)
        self.client_obj.save()
        self.maxDiff = None

        self.contract = f.create_contract(self.agency, self.client_obj)

    def get_response_contract_details(self, *args, **kwargs):
        return get_contract_serializer_result(
            self.contract, self.client, self.agency * args, **kwargs,
        )

    def test_contract_serializer(self):
        """Should contain the correct data from the related model."""

        serializer = s.ContractSerializer(self.contract)

        self.assertDictEqual(
            serializer.data,
            get_contract_serializer_result(
                contract=self.contract, client=self.client_obj, agency=self.agency,
            ),
        )


class CandidateTests(TestCase):
    """Tests related to the Candidate serializer."""

    def setUp(self):
        """Create Agnecy and Candidate during test class initialization."""
        super().setUp()
        self.agency = f.create_agency()
        self.recruiter = f.create_recruiter(self.agency)
        self.candidate = f.create_candidate(self.agency, li_data={'test': 42})

        self.client_obj = f.create_client()

        self.request = factory.get('/')
        self.request.user = f.create_client_administrator(self.client_obj)

    def test_candidate_serializer(self):
        self.maxDiff = None
        """Should contain the correct data from the related model."""

        files = {
            key: f.create_candidate_file(
                candidate=self.candidate,
                org=self.client_obj,
                prefix=key,
                is_shared=key == 'shared',
            )
            for key in ('shared', 'private')
        }

        self.candidate.zoho_id = '12345'
        self.candidate.save()
        _id = self.candidate.id

        serializer = s.CandidateSerializer(
            self.candidate, context={'request': self.request}
        )

        try:
            self.assertDictEqual(
                serializer.data,
                {
                    'id': self.candidate.pk,
                    'original': None,
                    'photo': None,
                    'source': '',
                    'source_details': '',
                    'name': self.candidate.name,
                    'first_name': f.DEFAULT_CANDIDATE['first_name'],
                    'middle_name': '',
                    'last_name': f.DEFAULT_CANDIDATE['last_name'],
                    'first_name_kanji': '',
                    'last_name_kanji': '',
                    'first_name_katakana': '',
                    'last_name_katakana': '',
                    'email': self.candidate.email,
                    'phone': '',
                    'current_company': '',
                    'current_position': '',
                    'current_city': '',
                    'potential_locations': '',
                    'employment_status': '',
                    'linkedin_url': '',
                    'github_url': '',
                    'website_url': '',
                    'twitter_url': '',
                    'summary': f.DEFAULT_CANDIDATE['summary'],
                    'fulltime': False,
                    'parttime': False,
                    'local': False,
                    'remote': False,
                    'salary_currency': 'JPY',
                    'salary': None,
                    'reason_for_job_changes': '',
                    'secondary_email': '',
                    'languages': [],
                    'resume': None,
                    'resume_thumbnail': None,
                    'resume_ja': None,
                    'resume_ja_thumbnail': None,
                    'cv_ja': None,
                    'cv_ja_thumbnail': None,
                    # Can't figure out without request
                    'note': '',
                    'proposed': None,
                    'linkedin_data': None,
                    'zoho_id': '12345',
                    'created_at': serializer.data['created_at'],
                    'updated_at': serializer.data['updated_at'],
                    'archived': False,
                    'education_details': [],
                    'experience_details': [],
                    'name_ja': '',
                    'tags': [],
                    'is_missing_required_fields': True,
                    'is_met': False,
                    'internal_status': m.CandidateInternalStatus.NOT_CONTACTED.key,
                    'owner': self.candidate.owner.pk,
                    'created_by': serializer.data['created_by'],
                    'updated_by': serializer.data['updated_by'],
                    'current_salary_currency': 'JPY',
                    'current_salary': '0',
                    'current_salary_variable': None,
                    'total_annual_salary': None,
                    'current_salary_breakdown': '',
                    'current_country': 'jp',
                    'referred_by': None,
                    'industry': '',
                    'department': '',
                    'client_expertise': '',
                    'push_factors': '',
                    'pull_factors': '',
                    'companies_already_applied_to': '',
                    'companies_applied_to': '',
                    'age': None,
                    'nationality': '',
                    'secondary_phone': '',
                    'certifications': [],
                    'proposals': [],
                    'birthdate': None,
                    'current_postal_code': '',
                    'current_prefecture': '',
                    'current_street': '',
                    'expectations_details': '',
                    'gender': '',
                    'job_change_urgency': '',
                    'max_num_people_managed': None,
                    'notice_period': '',
                    'other_desired_benefits': [],
                    'other_desired_benefits_others_detail': '',
                    'tax_equalization': None,
                    'address': 'Japan',
                    'platform': '',
                    'platform_other_details': '',
                },
            )
        finally:
            for file in files.values():
                file.file.delete()

    @patch('core.signals.create_candidate_file_preview_and_thumbnail.delay')
    def test_retrieve_candidate_with_files_serializer(self, *args):
        """Should contain the correct data from the related model."""

        files = {
            key: f.create_candidate_file(
                candidate=self.candidate,
                org=self.client_obj,
                prefix=key,
                is_shared=key == 'shared',
            )
            for key in ('shared', 'private')
        }

        self.candidate.zoho_id = '12345'
        self.candidate.save()
        _id = self.candidate.id

        serializer = s.RetrieveCandidateSerializer(
            self.candidate, context={'request': self.request}
        )

        try:
            self.assertCountEqual(
                serializer.data,
                {
                    'id': self.candidate.pk,
                    'original': None,
                    'photo': None,
                    'source': '',
                    'source_details': '',
                    'name': self.candidate.name,
                    'first_name': f.DEFAULT_CANDIDATE['first_name'],
                    'middle_name': '',
                    'last_name': f.DEFAULT_CANDIDATE['last_name'],
                    'first_name_kanji': '',
                    'last_name_kanji': '',
                    'first_name_katakana': '',
                    'last_name_katakana': '',
                    'email': self.candidate.email,
                    'secondary_email': '',
                    'phone': '',
                    'current_company': '',
                    'current_position': '',
                    'current_city': '',
                    'potential_locations': '',
                    'employment_status': '',
                    'linkedin_url': '',
                    'github_url': '',
                    'website_url': '',
                    'twitter_url': '',
                    'summary': f.DEFAULT_CANDIDATE['summary'],
                    'fulltime': False,
                    'parttime': False,
                    'local': False,
                    'remote': False,
                    'salary_currency': 'JPY',
                    'salary': None,
                    'reason_for_job_changes': '',
                    'languages': [],
                    'files': [
                        {
                            'id': files['private'].id,
                            'file': f'http://testserver/media/candidate/{_id}/private/file.txt',
                            'is_shared': False,
                            'thumbnail': None,
                            'preview': None,
                        },
                        {
                            'id': files['shared'].id,
                            'file': f'http://testserver/media/candidate/{_id}/shared/file.txt',
                            'is_shared': True,
                            'thumbnail': None,
                            'preview': None,
                        },
                    ],
                    'resume': None,
                    'resume_thumbnail': None,
                    'resume_ja': None,
                    'resume_ja_thumbnail': None,
                    'cv_ja': None,
                    'cv_ja_thumbnail': None,
                    # Can't figure out without request
                    'note': '',
                    'proposed': None,
                    'linkedin_data': None,
                    'zoho_id': '12345',
                    'created_at': serializer.data['created_at'],
                    'updated_at': serializer.data['updated_at'],
                    'archived': False,
                    'is_missing_required_fields': False,
                    'education_details': [],
                    'experience_details': [],
                    'name_ja': '',
                    'tags': [],
                    'is_met': False,
                    'internal_status': m.CandidateInternalStatus.NOT_CONTACTED.key,
                    'import_source': None,
                    'owner': self.candidate.owner.pk,
                    'created_by': serializer.data['created_by'],
                    'updated_by': serializer.data['updated_by'],
                    'current_salary_currency': 'JPY',
                    'current_salary': None,
                    'current_salary_variable': None,
                    'total_annual_salary': None,
                    'current_salary_breakdown': '',
                    'current_country': '',
                    'referred_by': None,
                    'industry': '',
                    'department': '',
                    'client_expertise': '',
                    'push_factors': '',
                    'pull_factors': '',
                    'companies_already_applied_to': '',
                    'companies_applied_to': '',
                    'age': None,
                    'nationality': '',
                    'secondary_phone': '',
                    'certifications': [],
                    'proposals': [],
                    'birthdate': None,
                    'current_postal_code': '',
                    'current_prefecture': '',
                    'current_street': '',
                    'expectations_details': '',
                    'gender': 'other',
                    'job_change_urgency': '',
                    'max_num_people_managed': None,
                    'notice_period': '',
                    'other_desired_benefits': [],
                    'other_desired_benefits_others_detail': '',
                    'tax_equalization': None,
                    'address': 'Japan',
                    'platform': '',
                    'platform_other_details': '',
                },
            )
        finally:
            for file in files.values():
                file.file.delete()

    def test_get_proposed_true(self):
        """Should return proposed - True, if proposed."""
        job = f.create_job(self.client_obj)
        job.assign_member(self.recruiter)
        f.create_proposal(job, self.candidate, self.recruiter)

        request = factory.get('/', {'check_proposed_to': job.id})
        request.user = self.recruiter

        serializer = s.CandidateSerializer(
            self.candidate, context={'request': request, 'check_proposed_to': job}
        )

        self.assertTrue(serializer.data['proposed'])

    def test_get_proposed_false(self):
        """Should return proposed - False, if not proposed."""
        job = f.create_job(self.client_obj)
        job.assign_member(self.recruiter)
        request = factory.get('/', {'check_proposed_to': job.id})
        request.user = self.recruiter

        serializer = s.CandidateSerializer(
            self.candidate, context={'request': request, 'check_proposed_to': job}
        )

        self.assertFalse(serializer.data['proposed'])

    def test_validate_languages(self):
        """Should not be valid if Languages are not unique."""
        data = {
            'first_name': 'Test',
            'last_name': 'Candidate',
            'email': 'test@test.com',
            'summary': 'Test summary',
            'languages': [
                {'language': 'en', 'level': 0},
                {'language': 'en', 'level': 1},
            ],
        }
        serializer = s.CandidateSerializer(data=data, context={'request': self.request})

        message = 'Should have only one level of each language.'
        self.assertFalse(serializer.is_valid())
        self.assertTrue(message in serializer.errors['languages'])

    def test_get_linkedin_data_client_user(self):
        """Should return an empty string if not an Agency User."""
        self.request.user = f.create_client_administrator(self.client_obj)
        serializer = s.CandidateSerializer(
            self.candidate, context={'request': self.request}
        )

        self.assertEqual(serializer.data['linkedin_data'], None)

    def test_get_linkedin_data_agency_user_with_permission(self):
        """Should return linkedin_data if listed in the settings."""
        self.request.user = self.recruiter
        agency_pk = self.recruiter.profile.agency.pk

        with override_settings(CANDIDATE_RAW_DATA_AGENCY_IDS=[agency_pk]):
            serializer = s.CandidateSerializer(
                self.candidate, context={'request': self.request}
            )

            self.assertEqual(
                serializer.data['linkedin_data'], self.candidate.linkedin_data
            )

    def test_validate_linkedin_url(self):
        """Should be valid."""
        self.request.user = self.recruiter
        serializer = s.CandidateSerializer(
            data={'linkedin_url': 'https://www.linkedin.com/in/someslug/'},
            context={'request': self.request},
            partial=True,
        )
        self.assertTrue(serializer.is_valid())

    def test_validate_linkedin_url_invalid(self):
        """Should return error if linkedin url is not valid."""
        self.request.user = self.recruiter
        serializer = s.CandidateSerializer(
            data={'linkedin_url': 'invalid url'},
            context={'request': self.request},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue('linkedin_url' in serializer.errors)

    def test_linkedin_url_same(self):
        """Should return no error if linkedin url is updated."""
        self.candidate.linkedin_url = 'https://www.linkedin.com/in/someslug/'
        self.candidate.save()

        self.request = factory.get('/')
        self.request.user = self.recruiter

        serializer = s.CandidateSerializer(
            instance=self.candidate,
            data={'linkedin_url': 'https://linkedin.com/in/someslug/'},
            context={'request': self.request},
            partial=True,
        )
        self.assertTrue(serializer.is_valid())

    def test_linkedin_url_already_exists_another_agency(self):
        """Should return no error if candidate in another agency."""
        candidate = f.create_candidate(f.create_agency())
        candidate.linkedin_url = 'https://www.linkedin.com/in/someslug/'
        candidate.save()

        self.request = factory.get('/')
        self.request.user = self.recruiter

        serializer = s.CandidateSerializer(
            data={'linkedin_url': 'https://www.linkedin.com/in/someslug/'},
            context={'request': self.request},
            partial=True,
        )
        self.assertTrue(serializer.is_valid())

    def test_linkedin_url_removing_query(self):
        """Should remove query str from linkedin_url."""
        request = factory.get('/')
        request.user = self.recruiter

        serializer = s.CandidateSerializer(
            data={'linkedin_url': 'https://www.linkedin.com/in/someslug/?x=1'},
            context={'request': request},
            partial=True,
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data['linkedin_url'],
            'https://www.linkedin.com/in/someslug/',
        )

    def test_linkedin_url_max_length_without_query_str(self):
        """Should check length of linkedin_url without query str."""
        request = factory.get('/')
        request.user = self.recruiter

        serializer = s.CandidateSerializer(
            data={
                'linkedin_url': (
                    'https://www.linkedin.com/in/someslug/?x='.format('a' * 200)
                )
            },
            context={'request': request},
            partial=True,
        )

        self.assertTrue(serializer.is_valid())

    def test_linkedin_url_max_length(self):
        """Should check length of linkedin_url."""
        request = factory.get('/')
        request.user = self.recruiter

        serializer = s.CandidateSerializer(
            data={
                'linkedin_url': (
                    'https://www.linkedin.com/in/someslug/{}'.format('a' * 200)
                )
            },
            context={'request': request},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertTrue('linkedin_url' in serializer.errors)

    def test_education_details_serializer(self):
        detail = f.create_candidate_education_detail(self.candidate)

        serializer = s.FormEducationDetailSerializer(detail)

        self.assertEqual(serializer.data, f.DEFAULT_CANDIDATE_EDUCATION)

    def test_experience_details_serializer(self):
        detail = f.create_candidate_experience_detail(self.candidate)

        serializer = s.FormExperienceDetailSerializer(detail)

        self.assertEqual(serializer.data, f.DEFAULT_CANDIDATE_EXPERIENCE)

    def test_get_researcher_data(self):
        """Should return correct data for featured organization"""
        agency = f.create_agency()
        agency.enable_researcher_field_feature = True
        agency_manager = f.create_agency_manager(agency)
        agency_admin = f.create_agency_administrator(agency)
        candidate = f.create_candidate(agency, name_collect=agency_manager)

        request = factory.get('/')
        request.user = agency_admin

        serializer = s.CandidateSerializer(candidate, context={'request': request})

        self.assertEqual(serializer.data['name_collect'], agency_manager.pk)
        self.assertIsNone(serializer.data['mobile_collect'])

    def test_get_researcher_data_by_non_featured_org(self):
        """Shouldn't return researcher data for non-featured org"""
        agency = f.create_agency()
        agency.enable_researcher_field_feature = True
        candidate = f.create_candidate(agency)

        another_agency = f.create_agency()
        another_agency_admin = f.create_agency_administrator(another_agency)
        client = f.create_client()
        talent_associate = f.create_client_administrator(client)

        request_1 = factory.get('/')
        request_1.user = another_agency_admin

        request_2 = factory.get('/')
        request_2.user = talent_associate

        serializer_1 = s.CandidateSerializer(candidate, context={'request': request_1})

        serializer_2 = s.CandidateSerializer(candidate, context={'request': request_2})

        for field in s.CANDIDATE_FEATURE_FIELDS['researcher_feature']:
            self.assertIsNone(serializer_1.data.get(field))
            self.assertIsNone(serializer_2.data.get(field))

    def test_agency_only_candidate_fields_agency(self):
        """Agency should has an access to Agency-only candidate fields"""
        agency_admin = f.create_agency_administrator(self.agency)
        request = factory.get('/')
        request.user = agency_admin

        serializer = s.CandidateSerializer(self.candidate, context={'request': request})

        for field in s.AGENCY_ONLY_CANDIDATE_FIELDS:
            self.assertIn(field, serializer.data)

    def test_agency_only_candidate_fields_client(self):
        """Client can't see Agency-only candidate fields"""
        client_admin = f.create_client_administrator(self.client_obj)
        request = factory.get('/')
        request.user = client_admin

        serializer = s.CandidateSerializer(self.candidate, context={'request': request})

        for field in s.AGENCY_ONLY_CANDIDATE_FIELDS:
            self.assertNotIn(field, serializer.data)

    def test_agency_candidate_fields_only_agency_alien_candidate(self):
        """Agency can't see Agency only fields of alien candidate"""
        agency_admin = f.create_agency_administrator(self.agency)
        candidate = f.create_candidate(f.create_agency())
        request = factory.get('/')
        request.user = agency_admin

        serializer = s.CandidateSerializer(candidate, context={'request': request})

        for field in s.AGENCY_ONLY_CANDIDATE_FIELDS:
            self.assertNotIn(field, serializer.data)


class ProposalTests(APITestCase):
    """Tests related to the Proposal serializer."""

    def setUp(self):
        """Create all the required objects and also the Proposal."""
        super().setUp()
        agency = f.create_agency()
        recruiter = f.create_recruiter(agency)
        candidate = f.create_candidate(agency)

        self.client = f.create_client()
        self.job = f.create_job(self.client)

        self.proposal = f.create_proposal(self.job, candidate, recruiter)

    def test_proposal_serializer(self):
        """Should contain the correct data from the related model."""
        serializer = s.CreateProposalSerializer(self.proposal)

        self.assertDictEqual(
            serializer.data,
            {
                'id': self.proposal.pk,
                'job': self.proposal.job.pk,
                'candidate': self.proposal.candidate.pk,
            },
        )


class PublicProposalTests(APITestCase):
    """Tests related to the Public Proposal serializer."""

    def setUp(self):
        """Create all the required objects."""
        super().setUp()

        self.client = f.create_client()
        self.candidate = f.create_candidate(self.client)
        self.job = f.create_job(self.client)
        fa.PrivateJobPostingFactory(job=self.job)

    @patch('core.serializers.requests.post')
    def test_create_public_candidate_serializer_not_existing_candidate(
        self, mock_request
    ):
        data = {
            'job': self.job.id,
            'candidate': {
                'first_name': 'jo',
                'last_name': 'jo',
                'email': 'jay@jo.com',
                'phone': '',
                'resume': None,
                'new_resume': None,
            },
            'posting': 'private_posting',
            'token': '10000000-aaaa-bbbb-cccc-000000000001',
        }
        serializer = s.PublicCreateProposalSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        proposal = serializer.save()

        self.assertEqual(proposal.job, self.job)
        self.assertEqual(proposal.candidate.email, data['candidate']['email'])
        self.assertEqual(proposal.candidate.source, 'Direct Apply')
        self.assertEqual(proposal.status.stage, m.ProposalStatusStage.ASSOCIATED.key)
        self.assertTrue(proposal.is_direct_application)
        mock_request.assert_called()

    @patch('core.serializers.requests.post')
    def test_validate_public_candidate_serializer(self, mock_request):
        data = {
            'job': self.job.id,
            'candidate': {
                'first_name': 'jo',
                'last_name': 'jo',
                'email': 'jay@jo.com',
                'phone': '',
                'resume': None,
                'new_resume': None,
            },
            'posting': 'private_posting',
            'token': '10000000-aaaa-bbbb-cccc-000000000001',
        }
        serializer = s.PublicCreateProposalSerializer(
            data=data, context={'is_create': False}
        )
        self.assertTrue(serializer.is_valid())
        mock_request.assert_not_called()

    @patch(
        'core.serializers.requests.post',
        return_value=Mock(json=lambda: {'success': True}),
    )
    def test_create_public_candidate_serializer_existing_candidate(self, post_mock):
        data = {
            'job': self.job.id,
            'candidate': {
                'first_name': self.candidate.first_name,
                'last_name': self.candidate.last_name,
                'email': self.candidate.email,
                'phone': '',
                'resume': None,
                'new_resume': None,
            },
            'posting': 'private_posting',
            'token': '10000000-aaaa-bbbb-cccc-000000000001',
        }
        serializer = s.PublicCreateProposalSerializer(data=data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        proposal = serializer.save()

        self.assertEqual(proposal.job, self.job)
        self.assertEqual(proposal.candidate, self.candidate)
        self.assertEqual(proposal.status.stage, m.ProposalStatusStage.ASSOCIATED.key)
        self.assertTrue(proposal.is_direct_application)
        self.assertIsNot(proposal.candidate.source, 'Applicants (Direct)')
        post_mock.assert_called()

    @patch(
        'core.serializers.requests.post',
        return_value=Mock(json=lambda: {'success': True}),
    )
    def test_create_public_candidate_serializer_existing_proposal(self, post_mock):
        old_proposal = f.create_proposal(self.job, self.candidate, self.job.owner)
        data = {
            'job': self.job.id,
            'candidate': {
                'first_name': self.candidate.first_name,
                'last_name': self.candidate.last_name,
                'email': self.candidate.email,
                'phone': '',
                'resume': None,
                'new_resume': None,
            },
            'posting': 'private_posting',
            'token': '10000000-aaaa-bbbb-cccc-000000000001',
        }
        serializer = s.PublicCreateProposalSerializer(data=data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        proposal = serializer.save()

        self.assertEqual(proposal.job, self.job)
        self.assertEqual(proposal.candidate, self.candidate)
        self.assertEqual(proposal.status.stage, m.ProposalStatusStage.SUBMISSIONS.key)
        self.assertEqual(proposal.id, old_proposal.id)
        self.assertFalse(proposal.is_direct_application)
        self.assertIsNot(proposal.candidate.source, 'Applicants (Direct)')
        post_mock.assert_called()


class ProposalSourceSerializer(APITestCase):
    """Tests for the ProposalSource serializer."""

    def test_proposal_source_serializer_agency(self):
        """Organization type should be agency when an Agency passed."""
        agency = f.create_agency()
        serializer = s.ProposalSourceSerializer(agency)

        self.assertDictEqual(
            serializer.data,
            {'id': agency.pk, 'name': agency.name, 'organization_type': 'agency'},
        )

    def test_proposal_source_serializer_client(self):
        """Organization type should be client when a Client passed."""
        client = f.create_client()
        serializer = s.ProposalSourceSerializer(client)

        self.assertDictEqual(
            serializer.data,
            {'id': client.pk, 'name': client.name, 'organization_type': 'client'},
        )

    def test_proposal_source_serializer_not_organization(self):
        """Organization type should be None when not a Client or Agency."""
        data = {'id': 0, 'name': 'Test'}
        serializer = s.ProposalSourceSerializer(data)

        self.assertDictEqual(
            serializer.data,
            {'id': data['id'], 'name': data['name'], 'organization_type': None},
        )


class ProposalCommentTests(APITestCase):
    """Tests for ProposalComment serializer."""

    def setUp(self):
        """Create required objects for proposa comments."""
        super().setUp()

        client = f.create_client()
        agency = f.create_agency()
        client_admin = f.create_client_administrator(client)

        self.proposal_comment = f.create_proposal_comment(
            client_admin,
            f.create_proposal(
                f.create_job(client), f.create_candidate(agency), client_admin
            ),
        )

    @patch('core.serializers.ProposalCommentSerializer.get_author')
    def test_proposal_comment_serializer(self, mock_get_author):
        """Should contain the correct data from the related model."""
        serializer = s.ProposalCommentSerializer(self.proposal_comment)

        self.assertDictEqual(
            serializer.data,
            {
                'id': self.proposal_comment.pk,
                'author': mock_get_author(),
                'proposal': self.proposal_comment.proposal.pk,
                'text': self.proposal_comment.text,
                'system': False,
                'created_at': f.to_iso_datetime(self.proposal_comment.created_at),
            },
        )


class CreateProposalCommentTests(APITestCase):
    """Tests for ProposalComment create serializer."""

    def setUp(self):
        """Create required objects for proposa comments."""
        super().setUp()

        client = f.create_client()
        agency = f.create_agency()
        client_admin = f.create_client_administrator(client)

        self.request = factory.get('/')
        self.request.user = client_admin

        self.proposal = f.create_proposal(
            f.create_job(client), f.create_candidate(agency), client_admin
        )

    def test_create_proposal_comment_serializer(self):
        """Should set Comment's User and Proposal status field values."""
        data = {'proposal': self.proposal.pk, 'text': 'Test comment', 'public': False}

        serializer = s.CreateProposalCommentSerializer(
            data=data, context={'request': self.request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        proposal_comment = m.ProposalComment.objects.get(pk=serializer.data['id'])

        self.assertEqual(proposal_comment.author, self.request.user)
        self.assertEqual(proposal_comment.proposal_status, self.proposal.status)

    def test_validate_proposal_with_access(self):
        """Should be valid if User has an access to the Proposal."""
        data = {'proposal': self.proposal.pk, 'text': 'Test comment', 'public': False}

        serializer = s.CreateProposalCommentSerializer(
            data=data, context={'request': self.request}
        )

        serializer.is_valid(raise_exception=True)

    def test_validate_proposal_without_access(self):
        """Should not be valid if User has no access to the Proposal"""
        other_agency = f.create_agency()
        other_proposal = f.create_proposal(
            f.create_job(f.create_client()),
            f.create_candidate(other_agency),
            f.create_recruiter(other_agency),
        )

        data = {'proposal': other_proposal.pk, 'text': 'Test comment', 'public': False}

        serializer = s.CreateProposalCommentSerializer(
            data=data, context={'request': self.request}
        )

        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


class CandidatePrimaryKeyRelatedFieldTest(TestCase):
    """CandidatePrimaryKeyRelatedField tests."""

    def test_get_queryset(self):
        """Should call profile.apply_candidates_filter."""

        class DummySerializer(serializers.Serializer):
            f = CandidatePrimaryKeyRelatedField()

        mock = Mock()
        mock.return_value = m.Candidate.objects

        s = DummySerializer(data={'f': 1}, context={'request': mock})
        s.is_valid()

        self.assertEqual(len(mock.method_calls), 1)
        expected_call = call.user.profile.apply_candidates_filter(m.Candidate.objects)

        self.assertEqual(mock.method_calls[0], expected_call)


class JobPrimaryKeyRelatedFieldTest(TestCase):
    """JobPrimaryKeyRelatedField tests."""

    def test_get_queryset(self):
        """Should call profile.apply_jobs_filter."""

        class DummySerializer(serializers.Serializer):
            f = JobPrimaryKeyRelatedField()

        mock = Mock()
        mock.return_value = m.Job.objects

        s = DummySerializer(data={'f': 1}, context={'request': mock})
        s.is_valid()

        self.assertEqual(len(mock.method_calls), 1)
        expected_call = call.user.profile.apply_jobs_filter(m.Job.objects)

        self.assertEqual(mock.method_calls[0], expected_call)


def to_invitations(iterable):
    for item in iterable:
        yield {
            'email': item.email,
            'user': item.id,
        }


class InterviewSchedulingSerializersTest(TestCase):
    """Tests for serializers related to interview scheduling"""

    @classmethod
    def setUpTestData(cls):
        cls.client_obj = fa.ClientFactory()
        cls.admin = fa.ClientAdministratorFactory().user
        cls.job = fa.ClientJobFactory()

        request = factory.get('/')
        request.user = cls.admin
        cls.context = {'request': request}

    def setUp(self):
        self.candidate = fa.ClientCandidateFactory()
        self.proposal = fa.ClientProposalFactory(job=self.job, candidate=self.candidate)
        self.interview = self.proposal.current_interview
        self.start_date = datetime(2100, 1, 1, 12, 0, tzinfo=utc)
        self.end_date = datetime(2100, 1, 1, 13, 0, tzinfo=utc)
        self.base_request_data = {
            'interviewer': self.admin.pk,
            'notes': '',
            'id': self.interview.pk,
            'timeslots': [
                {
                    'start_at': self.start_date,
                    'end_at': self.end_date,
                    'is_rejected': False,
                }
            ],
            'description': '',
        }
        self.simple_scheduling_data = self.base_request_data.copy()
        self.simple_scheduling_data |= {
            'scheduling_type': 'simple_scheduling',
            'status': 'scheduled',
            'start_at': self.start_date,
            'end_at': self.end_date,
        }
        self.interview_proposal_data = self.base_request_data.copy()
        self.interview_proposal_data |= {
            'scheduling_type': 'interview_proposal',
            'status': 'pending',
        }
        self.past_scheduling_data = self.base_request_data.copy()
        self.past_scheduling_data |= {
            'scheduling_type': 'past_scheduling',
            'status': 'scheduled',
            'start_at': self.start_date,
            'end_at': self.end_date,
        }

    def check_serializer_save(
        self, serializer, status, schedule_count, scheduling_type=None
    ):
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        self.assertIsInstance(serializer.save(), m.ProposalInterview)
        self.assertEqual(self.interview.get_status(), status)
        self.assertEqual(self.interview.schedules.count(), schedule_count)

        if scheduling_type is not None:
            self.assertEqual(
                self.interview.current_schedule.scheduling_type, scheduling_type
            )

    def test_create_scheduled_interview(self):
        request_data = self.simple_scheduling_data

        serializer = s.CreateUpdateProposalInterviewSerializer(
            instance=self.interview, data=request_data, context=self.context
        )
        self.check_serializer_save(
            serializer,
            status='scheduled',
            schedule_count=1,
            scheduling_type='simple_scheduling',
        )

    def test_create_scheduled_interview_wrong_data(self):
        required_fields = ['start_at', 'end_at', 'interviewer']
        for field in required_fields:
            request_data = self.simple_scheduling_data.copy()
            request_data.pop(field)
            serializer = s.CreateUpdateProposalInterviewSerializer(
                instance=self.interview, data=request_data, context=self.context
            )
            self.assertFalse(serializer.is_valid(), msg=f'{field} not a required field')

    def test_create_schedule_proposal(self):
        request_data = self.interview_proposal_data

        serializer = s.CreateUpdateProposalInterviewSerializer(
            instance=self.interview, data=request_data, context=self.context
        )
        self.check_serializer_save(
            serializer,
            status='pending',
            schedule_count=1,
            scheduling_type='interview_proposal',
        )

    def test_create_schedule_proposal_wrong_data(self):
        required_fields = ['timeslots', 'interviewer']
        for field in required_fields:
            request_data = self.interview_proposal_data.copy()
            request_data.pop(field)
            serializer = s.CreateUpdateProposalInterviewSerializer(
                instance=self.interview, data=request_data, context=self.context
            )
            self.assertFalse(serializer.is_valid(), msg=f'{field} not a required field')

    def test_create_schedule_mismatch_flags(self):
        request_data = self.interview_proposal_data
        request_data['status'] = 'scheduled'

        serializer = s.CreateUpdateProposalInterviewSerializer(
            instance=self.interview, data=request_data, context=self.context
        )
        self.assertFalse(serializer.is_valid(), msg=serializer.errors)
        self.assertIn('status', serializer.errors)

    def test_create_past_schedule(self):
        request_data = self.past_scheduling_data

        serializer = s.CreateUpdateProposalInterviewSerializer(
            instance=self.interview, data=request_data, context=self.context
        )
        self.check_serializer_save(
            serializer,
            status='scheduled',
            schedule_count=1,
            scheduling_type='past_scheduling',
        ),

    def test_create_past_schedule_wrong_data(self):
        required_fields = ['start_at', 'end_at']
        for field in required_fields:
            request_data = self.past_scheduling_data.copy()
            request_data.pop(field)
            serializer = s.CreateUpdateProposalInterviewSerializer(
                instance=self.interview, data=request_data, context=self.context
            )
            self.assertFalse(serializer.is_valid(), msg=f'{field} not a required field')

    def serialize(self, interview, data):
        return s.CreateUpdateProposalInterviewSerializer(
            instance=interview, data=data, context=self.context,
        )

    def _test_reschedule(
        self, init_payload, reschedule_payload=None, cancel_status='canceled'
    ):
        scheduling_type = init_payload['scheduling_type']

        serializer = self.serialize(self.interview, init_payload)
        self.check_serializer_save(serializer, 'pending', 1, scheduling_type)

        self.interview.refresh_from_db()

        cancel_payload = {
            'status': cancel_status,
            'pre_schedule_msg': 'Im on break',
        }
        serializer = self.serialize(self.interview, cancel_payload)
        self.check_serializer_save(serializer, cancel_status, 1, scheduling_type)
        self.assertEqual(
            self.interview.current_schedule.pre_schedule_msg,
            cancel_payload['pre_schedule_msg'],
        )

        self.interview.refresh_from_db()
        canceled_schedule = self.interview.current_schedule

        if reschedule_payload is None:
            reschedule_payload = init_payload

        serializer = self.serialize(self.interview, reschedule_payload)
        self.check_serializer_save(
            serializer,
            reschedule_payload['status'],
            2,
            reschedule_payload['scheduling_type'],
        )
        self.interview.refresh_from_db()

        current_schedule = self.interview.current_schedule
        self.assertNotEqual(canceled_schedule.id, current_schedule.id)

        prev_schedule = self.interview.schedules.exclude(id=current_schedule.id).first()
        self.assertEqual(canceled_schedule.id, prev_schedule.id)

    def test_create_cancel_reschedule_scheduled_interview(self):
        request_data = {
            'status': 'scheduled',
            'scheduling_type': 'simple_scheduling',
            'interviewer': self.base_request_data['interviewer'],
            'start_at': self.start_date + timedelta(days=1),
            'end_at': self.end_date + timedelta(days=1),
        }
        self._test_reschedule(self.interview_proposal_data, request_data)

    def test_create_cancel_reschedule_interview_proposal(self):
        self._test_reschedule(self.interview_proposal_data)


class ProposalInterviewSerializersTest(TestCase):
    """ProposalInterview serializer test"""

    def setUp(self):
        self.client_obj = f.create_client()

        self.hiring_manager = f.create_hiring_manager(
            self.client_obj, 'john.snow@test.net'
        )

        agency, self.agency_members = f.create_agency_with_members(
            f.create_recruiter, f.create_agency_manager,
        )
        user = self.client_obj.primary_contact
        job = f.create_job(self.client_obj)

        self.proposal = f.create_proposal_with_candidate(job, agency.primary_contact)
        self.proposal2 = f.create_proposal_with_candidate(job, agency.primary_contact)
        self.invited = [self.agency_members[0], self.agency_members[1]]

        request = factory.get('/')
        request.user = user
        self.context = {'request': request}

        self.interview = f.create_proposal_interview_with_timeslots(
            proposal=self.proposal2,
            created_by=user,
            invited=to_invitations(self.invited),
            timeslot_intervals=[
                (
                    datetime(2100, 1, 1, 12, 0, tzinfo=utc),
                    datetime(2100, 1, 1, 12, 30, tzinfo=utc),
                ),
                (
                    datetime(2100, 1, 1, 12, 30, tzinfo=utc),
                    datetime(2100, 1, 1, 13, 30, tzinfo=utc),
                ),
                (
                    datetime(2100, 1, 1, 13, 0, tzinfo=utc),
                    datetime(2100, 1, 1, 13, 30, tzinfo=utc),
                ),
            ],
        )

    def tearDown(self):
        self.interview.current_schedule.scheduled_timeslot.delete()
        super().tearDown()

    def test_output(self):
        interview = m.ProposalInterview.objects.get(id=self.interview.id)
        expected = {
            'id': interview.id,
            'status': interview.get_status(),
            'status_display': interview.current_schedule.get_status_display(),
            'proposal': interview.proposal.id,
            'start_at': s.represent_dt(interview.start_at),
            'end_at': s.represent_dt(interview.end_at),
            'pre_schedule_msg': '',
            'scheduling_type': '',
            'timeslots': [
                {
                    'id': timeslot.id,
                    'start_at': s.represent_dt(timeslot.start_at),
                    'end_at': s.represent_dt(timeslot.end_at),
                }
                for timeslot in interview.current_schedule.timeslots.all()
            ],
            'invited': [
                {
                    'id': item.id,
                    'user': item.user.id,
                    'email': item.email,
                    'name': item.name,
                }
                for item in interview.invited.all()
            ],
            'description': interview.description,
            'notes': interview.notes,
            'interviewer': None,
            'order': interview.order,
            'interview_type': interview.interview_type,
            'assessment': None,
            'schedules': [
                {
                    'id': schedule.id,
                    'interview': interview.id,
                    'creator_timezone': schedule.creator_timezone,
                    'timeslots': [
                        {
                            'id': timeslot.id,
                            'start_at': s.represent_dt(timeslot.start_at),
                            'end_at': s.represent_dt(timeslot.end_at),
                        }
                        for timeslot in schedule.timeslots.all()
                    ],
                }
                for schedule in interview.schedules.all()
            ],
        }

        serializer = s.ProposalInterviewSerializer(interview, context=self.context)
        self.assertDictEqual(expected, serializer.data)

    def check_serializer_change(
        self,
        invited=None,
        expect_invited=None,
        is_create=False,
        instance=None,
        proposal=None,
        expected_validation_errors=None,
    ):
        if not invited:
            invited = []
        input_data = {
            'status': m.ProposalInterviewSchedule.Status.TO_BE_SCHEDULED,
            'timeslots': [
                {
                    'start_at': datetime(2100, 2, 1, 12, 0, tzinfo=utc),
                    'end_at': datetime(2100, 2, 1, 12, 30, tzinfo=utc),
                },
                {
                    'start_at': datetime(2100, 2, 1, 13, 0, tzinfo=utc),
                    'end_at': datetime(2100, 2, 1, 13, 30, tzinfo=utc),
                },
                {
                    'start_at': datetime(2100, 2, 1, 14, 0, tzinfo=utc),
                    'end_at': datetime(2100, 2, 1, 14, 30, tzinfo=utc),
                },
            ],
            'description': 'A long time ago in galaxy far far away',
        }
        if len(invited) > 0:
            input_data['invited'] = list(to_invitations(invited))
        serializer_args = {
            'data': input_data,
            'context': self.context,
        }
        if is_create:
            if proposal:
                input_data['proposal'] = proposal.id
        else:
            serializer_args['instance'] = instance

        serializer = s.CreateUpdateProposalInterviewSerializer(**serializer_args)
        self.assertEqual(
            serializer.is_valid(),
            expected_validation_errors is None,
            msg=str(serializer.errors),
        )

        if expected_validation_errors:
            self.assertEqual(serializer.errors, expected_validation_errors)
            return

        serializer.save()

        if is_create:
            user = self.context['request'].user
            self.assertTrue(
                m.ProposalInterview.objects.filter(
                    created_by=user, proposal=self.proposal
                ).exists(),
                msg='Interview for proposal doesn\'t exist',
            )

            interview = m.ProposalInterview.objects.get(
                created_by=user, proposal=self.proposal,
            )
        else:
            interview = instance

        invited_set = set(expect_invited or invited)
        self.assertSetEqual(
            invited_set,
            set(item.user for item in interview.invited.all()),
            msg='List of invited users doesn\'t match',
        )

        self.assertEqual(input_data['status'], interview.get_status())
        self.assertEqual(
            len(input_data['timeslots']), interview.current_schedule.timeslots.count()
        )
        for timeslot in input_data['timeslots']:
            start_at = timeslot['start_at']
            end_at = timeslot['end_at']
            qs = interview.current_schedule.timeslots.filter(
                start_at=start_at, end_at=end_at,
            )
            self.assertEqual(qs.count(), 1)
        self.assertEqual(input_data['description'], interview.description)

    def test_create(self):
        self.check_serializer_change(
            is_create=True, proposal=self.proposal, invited=self.invited,
        )

    def test_create_no_proposal(self):
        self.check_serializer_change(
            is_create=True,
            invited=self.invited,
            expected_validation_errors={
                'proposal': [PrimaryKeyRelatedField.default_error_messages['required']]
            },
        )

    def test_update(self):
        self.check_serializer_change(
            instance=self.interview, invited=self.invited,
        )

    def test_create_no_invites(self):
        self.check_serializer_change(
            is_create=True, proposal=self.proposal, expect_invited=[],
        )

    def test_update_no_invites(self):
        self.check_serializer_change(
            instance=self.interview, expect_invited=self.invited
        )

    def test_create_other_org_user_invited(self):
        self.check_serializer_change(
            is_create=True,
            proposal=self.proposal,
            invited=[self.agency_members[0], self.hiring_manager],
            expected_validation_errors={
                'invited': [
                    s.CreateUpdateProposalInterviewSerializer.custom_error_messages[
                        'non_member'
                    ]
                ]
            },
        )

    def test_update_other_org_user_invited(self):
        self.check_serializer_change(
            instance=self.interview,
            invited=[self.agency_members[0], self.hiring_manager],
            expected_validation_errors={
                'invited': [
                    s.CreateUpdateProposalInterviewSerializer.custom_error_messages[
                        'non_member'
                    ]
                ]
            },
        )

    def test_update_specific_order(self):
        interview2 = f.create_proposal_interview(
            self.proposal2, self.context['request'].user
        )
        interview3 = f.create_proposal_interview(
            self.proposal2, self.context['request'].user
        )
        self.assertEqual(self.interview.order, 0)
        self.assertEqual(interview2.order, 1)
        self.assertEqual(interview3.order, 2)
        kwargs = {
            'data': {'to_order': 2},
            'context': self.context,
            'instance': self.interview,
        }
        updated = s.CreateUpdateProposalInterviewSerializer(**kwargs)
        self.assertTrue(updated.is_valid())
        updated.save()
        interview2.refresh_from_db()
        interview3.refresh_from_db()
        self.assertEqual(self.interview.order, 2)
        self.assertEqual(interview2.order, 0)
        self.assertEqual(interview3.order, 1)


class ProposalInterviewPublicSerializer(TestCase):
    def setUp(self):
        self.client_obj = f.create_client()

        self.hiring_manager = f.create_hiring_manager(
            self.client_obj, 'john.snow@test.net'
        )

        agency, self.agency_members = f.create_agency_with_members(
            f.create_recruiter, f.create_agency_manager,
        )
        user = self.client_obj.primary_contact
        job = f.create_job(self.client_obj)

        self.proposal = f.create_proposal_with_candidate(job, agency.primary_contact)
        self.proposal2 = f.create_proposal_with_candidate(job, agency.primary_contact)
        self.proposal_longlist = f.create_proposal_with_candidate(
            job, agency.primary_contact, stage='longlist'
        )

        request = factory.get('/')
        request.user = user
        self.context = {'request': request}

        self.interview = f.create_proposal_interview_with_timeslots(
            proposal=self.proposal2,
            created_by=user,
            timeslot_intervals=[
                (
                    datetime(2100, 1, 1, 12, 0, tzinfo=utc),
                    datetime(2100, 1, 1, 12, 30, tzinfo=utc),
                ),
                (
                    datetime(2100, 1, 1, 12, 30, tzinfo=utc),
                    datetime(2100, 1, 1, 13, 30, tzinfo=utc),
                ),
                (
                    datetime(2100, 1, 1, 13, 0, tzinfo=utc),
                    datetime(2100, 1, 1, 13, 30, tzinfo=utc),
                ),
            ],
        )

    def test_output(self):
        self.maxDiff = None
        interview = m.ProposalInterview.objects.get(id=self.interview.id)
        job = interview.proposal.job
        expected = {
            'status': interview.get_status(),
            'notes': interview.notes,
            'start_at': s.represent_dt(interview.start_at),
            'end_at': s.represent_dt(interview.end_at),
            'pre_schedule_msg': '',
            'timeslots': [
                {
                    'id': timeslot.id,
                    'start_at': s.represent_dt(timeslot.start_at),
                    'end_at': s.represent_dt(timeslot.end_at),
                }
                for timeslot in interview.current_schedule.timeslots.all()
            ],
            'inviter': self.client_obj.name,
            'job': s.ProposalInterviewPublicSerializer._JobSerializer(
                instance=job
            ).data,
            'candidate_name': interview.proposal.candidate.name,
        }

        serializer = s.ProposalInterviewPublicSerializer(
            interview, context=self.context
        )
        self.assertDictEqual(expected, serializer.data)
        self.maxDiff = None

    def create_context(self, interview):
        request = factory.post('/')
        request.user = interview.proposal.created_by
        return {'request': request}

    def _test_confirm_success(self, proposal):
        interview = f.create_proposal_interview_with_timeslots(
            proposal=proposal,
            created_by=self.hiring_manager,
            start_at=None,
            timeslot_intervals=[
                (
                    datetime(2100, 1, 1, 12, 0, tzinfo=utc),
                    datetime(2100, 1, 1, 12, 30, tzinfo=utc),
                ),
                (
                    datetime(2100, 1, 1, 12, 30, tzinfo=utc),
                    datetime(2100, 1, 1, 13, 30, tzinfo=utc),
                ),
                (
                    datetime(2100, 1, 1, 13, 0, tzinfo=utc),
                    datetime(2100, 1, 1, 13, 30, tzinfo=utc),
                ),
            ],
        )

        timeslot = interview.current_schedule.timeslots.all()[0]
        serializer = s.ProposalInterviewPublicSerializer(
            instance=interview,
            data={'chosen_timeslot': timeslot.id},
            context=self.create_context(interview),
        )

        self.assertTrue(
            serializer.is_valid(raise_exception=True), msg=serializer.errors
        )
        serializer.save()
        self.assertEqual(interview.start_at, timeslot.start_at)
        self.assertEqual(interview.end_at, timeslot.end_at)
        self.assertEqual(
            interview.get_status(), m.ProposalInterviewSchedule.Status.SCHEDULED
        )

        return interview

    def test_confirm_success_longlist(self):
        interview = self._test_confirm_success(self.proposal_longlist)

        self.assertEqual(
            interview.proposal.status.group,
            m.ProposalStatusGroup.ASSOCIATED_TO_JOB.key,
        )

    def test_confirm_success_shortlist(self):
        interview = self._test_confirm_success(self.proposal2)

        self.assertNotEqual(
            interview.proposal.status.group,
            m.ProposalStatusGroup.ASSOCIATED_TO_JOB.key,
        )

    def check_confirm_error(self, timeslot, get_expected_validation_errors):
        serializer = s.ProposalInterviewPublicSerializer(
            instance=self.interview, data={'chosen_timeslot': timeslot.id},
        )

        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(
            serializer.errors, get_expected_validation_errors(serializer)
        )

    def test_confirm_timeslot_was_selected(self):
        self.check_confirm_error(
            timeslot=self.interview.current_schedule.timeslots.all()[0],
            get_expected_validation_errors=lambda serializer: {
                'chosen_timeslot': [serializer.custom_error_messages['timeslot_chosen']]
            },
        )

    def test_confirm_wrong_timeslot(self):
        other_interview = f.create_proposal_interview_with_timeslots(
            proposal=self.proposal,
            created_by=self.hiring_manager,
            timeslot_intervals=[
                (
                    datetime(2100, 1, 1, 12, 0, tzinfo=utc),
                    datetime(2100, 1, 1, 12, 30, tzinfo=utc),
                ),
            ],
        )
        timeslot = other_interview.current_schedule.timeslots.all()[0]

        self.check_confirm_error(
            timeslot=timeslot,
            get_expected_validation_errors=lambda serializer: {
                'chosen_timeslot': [
                    serializer.fields['chosen_timeslot']
                    .default_error_messages['does_not_exist']
                    .format(pk_value=timeslot.id)
                ]
            },
        )

    def test_reject_success(self):
        serializer = s.ProposalInterviewPublicSerializer(
            instance=self.interview,
            data={'is_rejected': True},
            context=self.create_context(self.interview),
        )
        self.assertTrue(
            serializer.is_valid(raise_exception=True), msg=serializer.errors
        )
        serializer.save()
        self.assertEqual(
            self.interview.get_status(), m.ProposalInterviewSchedule.Status.REJECTED
        )

    def test_create(self):
        # should not be able to create with this serializer
        serializer = s.ProposalInterviewPublicSerializer(data={'is_rejected': True},)
        serializer.is_valid(raise_exception=True)

        with self.assertRaises(ValidationError):
            serializer.save()


class FeedbackTests(TestCase):
    def test_feedback_serializer(self):
        user = f.create_client_administrator(f.create_client())

        fb = m.Feedback.objects.create(**f.DEFAULT_FEEDBACK, created_by=user)

        serializer = s.FeedbackSerializer(fb)
        self.assertDictEqual(
            serializer.data,
            {
                "page_html": f.DEFAULT_FEEDBACK['page_html'],
                "page_url": f.DEFAULT_FEEDBACK['page_url'],
                "redux_state": f.DEFAULT_FEEDBACK['redux_state'],
                "text": f.DEFAULT_FEEDBACK['text'],
            },
        )


class DealPipelineTests(TestCase):
    def test_deal_pipeline_proposals_serializer(self):
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        client = f.create_client()

        request = factory.get('/')
        request.user = agency_admin
        context = {'request': request}

        candidate = f.create_candidate(agency, current_salary=1000)
        job = f.create_job(agency, client)
        proposal = f.create_proposal(job, candidate, agency_admin)
        proposal.status = m.ProposalStatus.objects.filter(deal_stage='offer').first()
        proposal.save()

        total_value = int(
            float(candidate.current_salary.amount) * agency.deal_hiring_fee_coefficient
        )
        realistic_value = int(
            float(candidate.current_salary.amount)
            * agency.deal_hiring_fee_coefficient
            * agency.deal_offer_sc
        )

        serializer = s.DealPipelineProposalSerializer(
            annotate_proposal_deal_pipeline_metrics(
                m.Proposal.objects.filter(pk=proposal.pk), agency
            ),
            many=True,
            context=context,
        )
        self.assertEqual(
            serializer.data,
            [
                {
                    'id': proposal.id,
                    'candidate': s.ProposalCandidateSerializer(
                        candidate, context=context
                    ).data,
                    'job': s.ProposalJobSerializer(job).data,
                    'deal_stage': proposal.status.deal_stage,
                    'total_value': total_value,
                    'realistic_value': realistic_value,
                    'client_name': client.name,
                }
            ],
        )


class AgencyClientInfoSerializerTests(TestCase):
    def test_agency_client_info_serializer(self):
        client = f.create_client()
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)

        request = factory.get('/')
        request.user = agency_admin

        agency_client_info = m.AgencyClientInfo.objects.create(
            agency=agency, client=client
        )

        serializer = s.AgencyClientInfoSerializer(
            instance=agency_client_info, context={'request': request}
        )

        self.assertEqual(
            serializer.data,
            {
                'industry': '',
                'type': '',
                'originator': None,
                'info': '',
                'notes': '',
                'account_manager': None,
                'updated_at': serializer.data['updated_at'],
                'updated_by': None,
                'billing_address': '',
                'portal_url': '',
                'portal_login': '',
                'portal_password': '',
                'primary_contact_number': '',
                'website': '',
            },
        )


class PrivateJobPostingSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ca = fa.ClientAdministratorFactory()
        cls.request = factory.get('/')
        cls.request.user = cls.ca.user

    def setUp(self):
        self.job = fa.ClientJobFactory(client=self.ca.client)

    def test_create_private_job_posting_serializer(self):
        data = s.BaseJobSerializer(self.job).data
        data['is_enabled'] = True
        serializer = s.PrivateJobPostingSerializer(
            data=data, context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        posting = serializer.save()
        self.assertIsNotNone(posting.public_uuid)
        self.assertTrue(posting.is_enabled)

        # subsequent creates should error
        serializer2 = s.PrivateJobPostingSerializer(
            data=data, context={'request': self.request}
        )
        self.assertFalse(serializer2.is_valid())

    def test_update_private_job_posting_serializer_disable_enable(self):
        """disabling then enabling should shuffle the public_uuid"""
        data = s.BaseJobSerializer(self.job).data
        data['is_enabled'] = True
        serializer = s.PrivateJobPostingSerializer(
            data=data, context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        posting = serializer.save()
        self.assertIsNotNone(posting.public_uuid)
        self.assertTrue(posting.is_enabled)
        old_public_uuid = posting.public_uuid

        data['is_enabled'] = False
        serializer2 = s.PrivateJobPostingSerializer(
            instance=posting, data=data, context={'request': self.request}
        )
        self.assertTrue(serializer2.is_valid())
        posting = serializer2.save()
        self.assertIsNone(posting.public_uuid)
        self.assertFalse(posting.is_enabled)

        data['is_enabled'] = True
        serializer3 = s.PrivateJobPostingSerializer(
            instance=posting, data=data, context={'request': self.request}
        )
        self.assertTrue(serializer3.is_valid())
        posting = serializer3.save()
        self.assertIsNotNone(posting.public_uuid)
        self.assertTrue(posting.is_enabled)
        self.assertNotEqual(posting.public_uuid, old_public_uuid)

    def test_update_private_job_posting_serializer_enable_enable(self):
        """enabling then enabling should NOT shuffle the public_uuid"""
        data = s.BaseJobSerializer(self.job).data
        data['is_enabled'] = True
        serializer = s.PrivateJobPostingSerializer(
            data=data, context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        posting = serializer.save()
        self.assertIsNotNone(posting.public_uuid)
        self.assertTrue(posting.is_enabled)
        old_public_uuid = posting.public_uuid

        data['is_enabled'] = True
        serializer2 = s.PrivateJobPostingSerializer(
            instance=posting, data=data, context={'request': self.request}
        )
        self.assertTrue(serializer2.is_valid())
        posting = serializer2.save()
        self.assertIsNotNone(posting.public_uuid)
        self.assertTrue(posting.is_enabled)
        self.assertEqual(posting.public_uuid, old_public_uuid)


class PrivateJobPostingPublicSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ca = fa.ClientAdministratorFactory()

    def setUp(self):
        self.job = fa.ClientJobFactory(client=self.ca.client)
        self.private_job_posting = fa.PrivateJobPostingFactory(job=self.job)

    def test_get(self):
        serializer = s.PrivateJobPostingPublicSerializer(
            instance=self.private_job_posting
        )
        self.assertEqual(
            set(s.PrivateJobPostingPublicSerializer.Meta.fields),
            set(serializer.data.keys()),
        )


class CareerSiteJobPostingSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ca = fa.ClientAdministratorFactory()
        cls.request = factory.get('/')
        cls.request.user = cls.ca.user

    def setUp(self):
        self.job = fa.ClientJobFactory(client=self.ca.client)

    def test_create(self):
        data = s.BaseJobSerializer(self.job).data
        data['is_enabled'] = True
        serializer = s.CareerSiteJobPostingSerializer(
            data=data, context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        posting = serializer.save()
        self.assertTrue(posting.is_enabled)
        self.assertEqual(serializer.data['slug'], posting.slug)

        # subsequent creates should error
        serializer2 = s.CareerSiteJobPostingSerializer(
            data=data, context={'request': self.request}
        )
        self.assertFalse(serializer2.is_valid())

    def test_update(self):
        data = s.BaseJobSerializer(self.job).data
        data['is_enabled'] = True
        serializer = s.CareerSiteJobPostingSerializer(
            data=data, context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        posting = serializer.save()
        self.assertEqual(serializer.data['slug'], posting.slug)
        self.assertTrue(posting.is_enabled)

        data['title'] = 'New title'
        serializer2 = s.CareerSiteJobPostingSerializer(
            instance=posting, data=data, context={'request': self.request}
        )
        self.assertTrue(serializer2.is_valid())
        posting = serializer2.save()
        self.assertTrue(posting.is_enabled)
        self.assertEqual(data['title'], serializer2.validated_data['title'])


class CareerSiteJobPostingPublicSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ca = fa.ClientAdministratorFactory()

    def setUp(self):
        self.job = fa.ClientJobFactory(client=self.ca.client)
        self.career_site_job_posting = fa.CareerSiteJobPostingFactory(job=self.job)

    def test_get(self):
        serializer = s.CareerSiteJobPostingPublicSerializer(
            instance=self.career_site_job_posting
        )
        self.assertEqual(
            set(s.CareerSiteJobPostingPublicSerializer.Meta.fields),
            set(serializer.data.keys()),
        )


class NoteActivitySerializerTests(TestCase):
    def setUp(self):
        super().setUp()
        self.proposal = fa.ClientProposalFactory()
        self.job = self.proposal.job
        self.candidate = self.proposal.candidate
        self.admin = self.proposal.job.owner

        request = factory.get('/')
        request.user = self.admin
        self.context = {'request': request}

    def test_create_proposal_note(self):
        data = {
            'proposal': self.proposal.id,
            'content': 'testext',
            'author': self.admin.id,
        }
        serializer = s.NoteActivitySerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        note = serializer.save()
        self.assertIsInstance(note, m.NoteActivity)
        self.assertEqual(note.proposal, self.proposal)
        self.assertEqual(note.candidate, self.candidate)
        self.assertEqual(note.job, self.job)

    def test_create_note_multiple_relations(self):
        base_data = {
            'job': self.job.id,
            'candidate': self.candidate.id,
            'proposal': self.proposal.id,
            'content': 'testext',
            'author': self.admin.id,
        }
        for field in ['job', 'candidate', 'proposal', 'nothing']:
            data = base_data.copy()
            data.pop(field, None)
            serializer = s.NoteActivitySerializer(data=data, context=self.context)
            self.assertFalse(serializer.is_valid(), msg=f'{field} case succeeds')
            self.assertIn('non_field_errors', serializer.errors)
