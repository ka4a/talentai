from django.test import TestCase
from django.utils.datetime_safe import datetime
from django.utils.timezone import utc

from core import fixtures as f, models as m
from core.annotations import annotate_job_agency_member_have_access_since


def get_date(month):
    return datetime(2019, month, 1, tzinfo=utc)


def set_created_at(item, month):
    item.created_at = get_date(month)
    item.save()


def add_agency(job, agency, month):
    job_agency = m.JobAgencyContract.objects.create(job=job, agency=agency,)
    set_created_at(job_agency, month)


def add_members(job, assignees_month):
    for user, month in assignees_month:
        job_assignee = m.JobAssignee.objects.create(user=user, job=job,)
        set_created_at(job_assignee, month)


class TestAnnotateJobAgencyMemberHaveAccessSince(TestCase):
    def setUp(self):
        self.client_obj = f.create_client()
        self.agency = f.create_agency()
        self.puppet_client = f.create_client(owner_agency=self.agency)

        self.user = f.create_recruiter(self.agency)

    def create_job(self, org, client, title, month, assign_members=None):
        job = f.create_job(title=title, org=org, client=client)
        set_created_at(job, month)

        if assign_members:
            add_members(job, assign_members)

        return job

    def create_client_job(self, title, month, assign_agency=None, assign_members=None):

        job = self.create_job(
            self.client_obj, self.client_obj, title, month, assign_members
        )

        if assign_agency:
            add_agency(job, *assign_agency)

        return job

    def create_agency_job(self, title, month, assign_members=None):
        return self.create_job(
            self.agency, self.puppet_client, title, month, assign_members
        )

    def test_annotation(self):

        expected_months = {
            'Agency': 1,
            'With members': 2,
            'No members': 2,
            'Recent agency assignment': 2,
        }

        expected_dates = {
            title: get_date(month) for title, month in expected_months.items()
        }

        self.create_agency_job(title='Agency', month=1, assign_members=[(self.user, 2)])

        self.create_client_job(
            title='With members',
            month=1,
            assign_agency=(self.agency, 2),
            assign_members=[
                (self.user, 3),
                (f.create_recruiter(self.agency), 4),
                (f.create_recruiter(self.agency), 5),
            ],
        )

        self.create_client_job(
            title='No members', month=1, assign_agency=(self.agency, 2),
        )

        self.create_client_job(
            title='Recent agency assignment',
            month=1,
            assign_agency=(self.agency, 3),
            assign_members=[(self.user, 2)],
        )

        qs = annotate_job_agency_member_have_access_since(
            m.Job.objects.all(), self.user,
        )

        for job in qs:
            self.assertEqual(
                expected_dates[job.title], job.have_access_since, msg=job.title
            )
