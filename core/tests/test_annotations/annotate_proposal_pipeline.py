from unittest import skip
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from core import (
    fixtures as f,
    models as m,
)
from core.annotations import annotate_job_proposal_pipeline


def create_primary_contact_and_user(create_org, assign_method):
    user = f.create_user()
    org = create_org(primary_contact=user)
    getattr(org, assign_method)(user)
    return user, org


def create_client_administrator_and_client():
    return create_primary_contact_and_user(f.create_client, 'assign_administrator')


def create_agency_admin_and_agency():
    return create_primary_contact_and_user(
        f.create_agency, 'assign_agency_administrator'
    )


@skip("TODO(ZOO-914)")
class TestAnnotateProposalPipeline(TestCase):
    def setUp(self):
        self.client_admin, self.client_obj = create_client_administrator_and_client()
        self.hiring_manager = f.create_hiring_manager(self.client_obj)

        self.agency_admin, self.agency = create_agency_admin_and_agency()
        self.agency_manager = f.create_agency_manager(self.agency)
        self.recruiter = f.create_recruiter(self.agency)
        self.maxDiff = None

        f.create_contract(self.agency, self.client_obj)

        orgs = {'client': self.client_obj, 'agency': self.agency}

        users = {
            'client': (self.client_admin, self.hiring_manager,),
            'agency': (self.agency_admin, self.agency_manager, self.recruiter,),
        }

        job_counts = {
            'client': 2,
            'agency': 1,
        }

        job_client = {
            'client': self.client_obj,
            'agency': f.create_client(owner_agency=self.agency),
        }

        status_groups = m.ProposalStatusGroup.get_keys()

        statuses = dict()

        # User with each role of each organization
        # will create a proposal for each tracked proposal status
        # for each job

        for org_name, org in orgs.items():
            org_content_type = ContentType.objects.get_for_model(org)
            statuses[org_name] = {
                group: m.OrganizationProposalStatus.objects.filter(
                    status__group=group,
                    org_id=org.id,
                    org_content_type=org_content_type,
                )
                .first()
                .status
                for group in status_groups
            }

        for org_name, org in orgs.items():
            for i in range(job_counts[org_name]):
                job = f.create_job(
                    org, client=job_client[org_name], title=f'{org_name}_{i}',
                )

                if org_name == 'client' and i == 0:
                    job.assign_agency(self.agency)

                for candidate_org_name, org_statuses in statuses.items():
                    for group, status in org_statuses.items():
                        for user in users[candidate_org_name]:
                            candidate = f.create_candidate(
                                orgs[candidate_org_name],
                                first_name=f'{type(user.profile).__name__}_{candidate_org_name}_{job.title}',
                                last_name=f'{group}',
                            )
                            f.create_proposal(job, candidate, user, status=status)

    def assert_pipeline_equals(self, user, expected):
        jobs = list(
            annotate_job_proposal_pipeline(
                m.Job.objects.all().order_by('title'), user.profile,
            )
        )

        self.assertEqual(len(jobs), len(expected))

        fields = (
            'title',
            'proposals_count',
            'proposals_associated_count',
            'proposals_pre_screening_count',
            'proposals_submissions_count',
            'proposals_screening_count',
            'proposals_interviewing_count',
            'proposals_offering_count',
            'proposals_hired_count',
            'proposals_rejected_count',
        )

        expected_iter = iter(expected)

        for job in jobs:
            expected_item = next(expected_iter)
            job_dict = {field: getattr(job, field) for field in fields}

            self.assertDictEqual(job_dict, expected_item)

    def assert_default_client_pipeline(self, user):
        self.assert_pipeline_equals(
            user,
            [
                {
                    'title': 'agency_0',
                    'proposals_count': 52,
                    'proposals_associated_count': 6,
                    'proposals_pre_screening_count': 4,
                    'proposals_submissions_count': 12,
                    'proposals_screening_count': 4,
                    'proposals_interviewing_count': 10,
                    'proposals_offering_count': 8,
                    'proposals_hired_count': 18,
                    'proposals_rejected_count': 0,
                },
                {
                    'title': 'client_0',
                    'proposals_count': 130,
                    'proposals_associated_count': 15,
                    'proposals_pre_screening_count': 10,
                    'proposals_submissions_count': 30,
                    'proposals_screening_count': 10,
                    'proposals_interviewing_count': 25,
                    'proposals_offering_count': 20,
                    'proposals_hired_count': 45,
                    'proposals_rejected_count': 0,
                },
                {
                    'title': 'client_1',
                    'proposals_count': 130,
                    'proposals_associated_count': 15,
                    'proposals_pre_screening_count': 10,
                    'proposals_submissions_count': 30,
                    'proposals_screening_count': 10,
                    'proposals_interviewing_count': 25,
                    'proposals_offering_count': 20,
                    'proposals_hired_count': 45,
                    'proposals_rejected_count': 0,
                },
            ],
        )

    def test_talent_associate(self):
        self.assert_default_client_pipeline(self.client_admin)

    def test_hiring_manager(self):
        self.assert_default_client_pipeline(self.hiring_manager)

    def assert_default_agency_pipeline(self, user):
        self.assert_pipeline_equals(
            user,
            [
                {
                    'title': 'agency_0',
                    'proposals_count': 130,
                    'proposals_associated_count': 15,
                    'proposals_pre_screening_count': 10,
                    'proposals_submissions_count': 30,
                    'proposals_screening_count': 10,
                    'proposals_interviewing_count': 25,
                    'proposals_offering_count': 20,
                    'proposals_hired_count': 45,
                    'proposals_rejected_count': 0,
                },
                {
                    'title': 'client_0',
                    'proposals_count': 78,
                    'proposals_associated_count': 9,
                    'proposals_pre_screening_count': 6,
                    'proposals_submissions_count': 18,
                    'proposals_screening_count': 6,
                    'proposals_interviewing_count': 15,
                    'proposals_offering_count': 12,
                    'proposals_hired_count': 27,
                    'proposals_rejected_count': 0,
                },
                {
                    'title': 'client_1',
                    'proposals_count': 78,
                    'proposals_associated_count': 9,
                    'proposals_pre_screening_count': 6,
                    'proposals_submissions_count': 18,
                    'proposals_screening_count': 6,
                    'proposals_interviewing_count': 15,
                    'proposals_offering_count': 12,
                    'proposals_hired_count': 27,
                    'proposals_rejected_count': 0,
                },
            ],
        )

    def test_agency_admin(self):
        self.assert_default_agency_pipeline(self.agency_admin)

    def test_agency_manager(self):
        self.assert_default_agency_pipeline(self.agency_manager)

    def test_recruiter(self):
        self.assert_default_agency_pipeline(self.recruiter)
