from django.test import TestCase

from core.annotations import annotate_job_hired_count
from core import fixtures as f, models as m


TITLE = 'test_annotate_job_hired_count'

JOB_HIRED_COUNTS = {
    f'{TITLE}_5': 5,
    f'{TITLE}_3': 3,
    f'{TITLE}_7': 7,
    f'{TITLE}_0': 0,
}

IRRELEVANT_COUNT = 5


class TestAnnotateJobHiredCount(TestCase):
    def setUp(self):
        self.client_obj = f.create_client()
        self.client_obj.primary_contact = f.create_client_administrator(self.client_obj)

    def init_jobs(self, expected_counts, org=None):
        if org is None:
            org = self.client_obj
        user = org.primary_contact
        hired_status = m.ProposalStatus.objects.get(
            group=m.ProposalStatusGroup.PENDING_START.key
        )

        job_map = dict()
        for title, hired_count in expected_counts.items():
            job = f.create_job(self.client_obj, title=title)
            job_map[title] = job

            def create_proposal(stage, status=None):
                kwargs = {'status': status} if status else dict()
                return f.create_proposal(
                    stage=stage,
                    candidate=f.create_candidate(org),
                    job=job,
                    created_by=user,
                    **kwargs,
                )

            for i in range(hired_count):
                create_proposal('shortlist', hired_status)

            for i in range(IRRELEVANT_COUNT):
                create_proposal('longlist')

            for i in range(IRRELEVANT_COUNT):
                create_proposal('shortlist')

        return job_map

    def test_annotation(self):
        title = 'test_annotation'
        expected = {
            f'{title}_5': 5,
            f'{title}_3': 3,
            f'{title}_7': 7,
            f'{title}_0': 0,
        }
        self.init_jobs(expected)

        job_qs = annotate_job_hired_count(m.Job.objects.filter(title__startswith=title))

        for job in job_qs:
            self.assertEqual(
                expected[job.title], job.hired_count, msg=f'in {job.title}'
            )

    def test_annotation_with_members_assigned(self):
        title = 'test_annotation_with_members_assigned'
        title_recruiters = f'{title}_recruiters'
        title_agency_managers = f'{title}_agency_managers'

        expected = {
            title_recruiters: 5,
            title_agency_managers: 3,
            f'{title}_7': 7,
            f'{title}_0': 0,
        }

        jobs = self.init_jobs(expected)

        agency = f.create_agency()
        agency_2 = f.create_agency()

        recruiters = [
            f.create_recruiter(agency),
            f.create_recruiter(agency),
        ]
        jobs[title_recruiters].assign_agency(agency_2)
        jobs[title_recruiters].assign_agency(agency)
        for recruiter in recruiters:
            jobs[title_recruiters].assign_member(recruiter)

        agency_manager = f.create_agency_manager(agency)

        jobs[title_agency_managers].assign_agency(agency)
        jobs[title_agency_managers].assign_member(agency_manager)

        job_qs = annotate_job_hired_count(m.Job.objects.filter(title__startswith=title))

        for job in job_qs:
            self.assertEqual(
                expected[job.title], job.hired_count, msg=f'in {job.title}'
            )
