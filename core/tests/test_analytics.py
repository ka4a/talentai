import random
from datetime import timedelta
from unittest import skip

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.timezone import now, datetime, utc
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from djangorestframework_camel_case.util import underscoreize

from core import fixtures as f
from core import serializers as s
from core.models import (
    Job,
    Proposal,
    Candidate,
    ProposalStatusHistory,
    ProposalStatus,
    Function,
    ProposalStatusStage,
    ProposalStatusGroup,
)
from core.views.analytics import (
    get_job_open_average,
    get_conversion_ratios,
)

User = get_user_model()


def gen_repeat_if_reached_end(iterator, limit=100):
    """Creates iterator which doesn't stop then we run out of items and starts over"""
    i = 0
    while True:
        for item in iterator:
            yield item
            i += 1
            if i >= limit:
                return


def is_even(i):
    return i % 2


@skip("TODO(ZOO-829)")
class AnalyticsTests(APITestCase):
    """Tests related to User endpoints."""

    def setUp(self):
        """Create a User during set up process."""
        super().setUp()

        self.client_obj = f.create_client()

        self.client_admin = f.create_client_administrator(self.client_obj)
        self.default_login()

        agency = f.create_agency()
        candidate = f.create_candidate(organization=agency)

        hiring_managers_init_data = {
            'alice@hiring.com': {
                'name': 'Alice Doe',
                'team': 'A',
                'jobs': {'function': 'Architecture', 'open_duration': (10, 7, 9)},
                'proposals': [
                    ('offer', ['new', 'offer', 'interviewing']),
                    (
                        'offer_accepted',
                        ['offer_accepted', 'offer', 'new', 'interviewing'],
                    ),
                ],
            },
            'bob@hiring.com': {
                'name': 'Bob Doe',
                'team': 'B',
                'jobs': {'function': 'Building', 'open_duration': (2, 24, 6)},
                'proposals': [('offer', ['new', 'offer', 'interviewing'])],
            },
            'charley@hiring.com': {
                'name': 'Charley Doe',
                'jobs': {'function': 'Construction', 'open_duration': (5, 36, 10)},
                'proposals': [
                    (
                        'offer_accepted',
                        ['offer_accepted', 'offer', 'new', 'interviewing'],
                    ),
                    ('interviewing', ['new', 'interviewing']),
                ],
            },
        }

        job_functions = dict()
        for email, hm_init in hiring_managers_init_data.items():
            # init hiring manager
            hiring_manager = f.create_hiring_manager(self.client_obj, email)
            f_name, l_name = hm_init['name'].split(' ')
            hiring_manager.first_name = f_name
            hiring_manager.last_name = l_name
            hiring_manager.save()

            if 'team' in hm_init:
                hiring_manager.profile.teams.add(
                    f.create_team(self.client_obj, hm_init['team'])
                )

            # init jobs
            jobs_init = hm_init['jobs']
            job_function_name = hm_init['jobs']['function']

            function = job_functions.get(job_function_name)

            if not function:
                function = Function.objects.create(title=job_function_name)

            jobs = []
            for open_days in jobs_init['open_duration']:
                jobs.append(
                    self.create_job(
                        self.client_obj,
                        open_days,
                        manager=hiring_manager,
                        function=function,
                    )
                )

            # init proposals
            proposals_init = hm_init['proposals']
            job_iterator = gen_repeat_if_reached_end(jobs, len(proposals_init))
            for status_group, history in proposals_init:
                job = next(job_iterator)

                status = f.get_or_create_proposal_status(status_group)
                proposal = f.create_proposal(
                    job, candidate, hiring_manager, status=status
                )

                for archived_status_group in history:
                    f.create_proposal_status_history(
                        proposal, group=archived_status_group
                    )

    def get_default_request_params(self, filter_type):
        return {
            'filter_type': filter_type,
            'date_start': ((timezone.now() - timedelta(days=90)).strftime('%Y-%m-%d')),
            'date_end': timezone.now().date().strftime('%Y-%m-%d'),
        }

    def default_login(self):
        self.client.force_login(self.client_admin)

    def create_job(
        self, client, open_days, closed_at=None, manager=None, function=None
    ):
        if closed_at is None:
            closed_at = timezone.now()

        job = f.create_job(
            org=client,
            published_at=closed_at - timedelta(days=open_days),
            closed_at=closed_at,
            owner=manager,
            function=function,
        )
        return job

    def test_get_job_open_average(self):
        self.assertAlmostEqual(get_job_open_average(Job.objects.all()), 12.1111111)

    def check_job_open_average_view(self, filter_type, expected):
        response = self.client.get(
            '/api/stats/job_average_open/', self.get_default_request_params(filter_type)
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(expected), len(response.data))

        for r in response.data:
            self.assertIn(r['name'], expected.keys())
            self.assertAlmostEqual(r['open_period_avg'], expected[r['name']])

    def test_job_open_average_view_by_team(self):
        self.check_job_open_average_view(
            filter_type='team',
            expected={'A': 8.6666667, 'B': 10.6666667, 'Unassigned department': 17},
        )

    def test_job_open_average_view_by_owner(self):
        self.check_job_open_average_view(
            filter_type='owner',
            expected={'Alice Doe': 8.6666667, 'Bob Doe': 10.6666667, 'Charley Doe': 17},
        )

    def test_job_open_average_view_by_function(self):
        self.check_job_open_average_view(
            filter_type='function',
            expected={
                'Architecture': 8.6666667,
                'Building': 10.6666667,
                'Construction': 17,
            },
        )

    def check_proposal_status_count_view(self, filter_type, expected):
        response = self.client.get(
            '/api/stats/proposal_status_count/',
            self.get_default_request_params(filter_type),
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.data), len(expected))

        for r in response.data:
            self.assertIn(r['name'], expected)
            self.assertEqual(
                expected[r['name']],
                r['proposal_pipeline'],
                msg=f"Resulted pipeline for {r['name']}",
            )

    def test_proposal_status_count_view_by_team(self):
        self.check_proposal_status_count_view(
            filter_type='team',
            expected={
                'Unassigned department': {
                    'approved': 0,
                    'received': 2,
                    'interviewing': 1,
                    'offer': 0,
                    'offer_accepted': 1,
                },
                'A': {
                    'approved': 0,
                    'received': 2,
                    'interviewing': 0,
                    'offer': 1,
                    'offer_accepted': 1,
                },
                'B': {
                    'received': 1,
                    'approved': 0,
                    'interviewing': 0,
                    'offer': 1,
                    'offer_accepted': 0,
                },
            },
        )

    def test_proposal_status_count_view_by_owner(self):
        self.check_proposal_status_count_view(
            filter_type='owner',
            expected={
                'Charley Doe': {
                    'approved': 0,
                    'received': 2,
                    'interviewing': 1,
                    'offer': 0,
                    'offer_accepted': 1,
                },
                'Alice Doe': {
                    'approved': 0,
                    'received': 2,
                    'interviewing': 0,
                    'offer': 1,
                    'offer_accepted': 1,
                },
                'Bob Doe': {
                    'received': 1,
                    'approved': 0,
                    'interviewing': 0,
                    'offer': 1,
                    'offer_accepted': 0,
                },
            },
        )

    def test_proposal_status_count_view_by_function(self):
        self.check_proposal_status_count_view(
            filter_type='function',
            expected={
                'Construction': {
                    'approved': 0,
                    'received': 2,
                    'interviewing': 1,
                    'offer': 0,
                    'offer_accepted': 1,
                },
                'Architecture': {
                    'approved': 0,
                    'received': 2,
                    'interviewing': 0,
                    'offer': 1,
                    'offer_accepted': 1,
                },
                'Building': {
                    'received': 1,
                    'approved': 0,
                    'interviewing': 0,
                    'offer': 1,
                    'offer_accepted': 0,
                },
            },
        )

    def assert_equal_to_conversion_results(self, ratios):
        expected = {
            "new": {
                "from_status": "new",
                'interviewing': 1.0,
                'offer': 0.8,
                'offer_accepted': 0.4,
            },
            "offer": {"from_status": "offer", 'offer_accepted': 0.5,},
        }
        float_fields = ('interviewing', 'offer', 'offer_accepted')
        for i in range(len(ratios)):
            row_id = ratios[i]['id']
            self.assertIn(row_id, expected.keys())
            for key in expected[row_id]:
                if key in float_fields:
                    self.assertAlmostEqual(ratios[i][key], expected[row_id][key])
                else:
                    self.assertEqual(ratios[i][key], expected[row_id][key])

    def test_get_conversion_ratios(self):
        conversion_ratios_params = (
            ('new', ('interviewing', 'offer', 'offer_accepted')),
            ('offer', ('offer_accepted',)),
        )

        ratios = get_conversion_ratios(Proposal.objects.all(), conversion_ratios_params)

        for result, param in zip(ratios, conversion_ratios_params):
            self.assertEqual(result['id'], param[0])
            self.assertEqual(result['from_status'], param[0])

        self.assert_equal_to_conversion_results(ratios)

    def test_analytics_for_archived_candidates(self):
        """Calculating must consider archived candidates"""
        qs = Candidate.objects.all()
        qs.update(archived=True)

        self.test_job_open_average_view_by_function()
        self.test_job_open_average_view_by_team()
        self.test_job_open_average_view_by_owner()

        self.test_get_conversion_ratios()
        self.test_get_job_open_average()
        self.test_proposal_status_count_view_by_function()
        self.test_proposal_status_count_view_by_team()
        self.test_proposal_status_count_view_by_owner()

        # test should not affect other tests
        qs.update(archived=False)

    def check_open_jobs(self, jobs, params, expected):
        user = f.create_user()
        client = f.create_client(primary_contact=user)
        client.assign_administrator(user)

        self.client.force_login(user)
        for closed_at, open_for_days in jobs:
            self.create_job(client, open_for_days, closed_at)

        response = self.client.get(reverse('stats-open-jobs'), params)

        self.assertEqual(expected, response.json())

        self.default_login()

    def test_check_open_jobs_monthly(self):
        self.check_open_jobs(
            jobs=[
                (datetime(2019, 6, 15, 1, tzinfo=utc), 6),
                (datetime(2019, 6, 15, tzinfo=utc), 5),
                (datetime(2019, 6, 6, tzinfo=utc), 1),
                (datetime(2019, 5, 9, tzinfo=utc), 1),
            ],
            params={
                'granularity': 'month',
                'date_end': '2019-06-16',
                'date_start': '2019-04-01',
                'filter_type': 'team',
            },
            expected=[
                {'date': date, 'value': value}
                for date, value in [
                    ('2019-04-01', 0),
                    ('2019-05-01', 1),
                    ('2019-06-01', 3),
                ]
            ],
        )

    def test_check_open_jobs_monthly_on_edge(self):
        self.check_open_jobs(
            jobs=[
                (datetime(2019, 6, 15, 1, tzinfo=utc), 6),
                (datetime(2019, 6, 15, tzinfo=utc), 5),
                (datetime(2019, 6, 6, tzinfo=utc), 1),
                (datetime(2019, 5, 9, tzinfo=utc), 1),
            ],
            params={
                'granularity': 'month',
                'date_end': '2019-06-15',
                'date_start': '2019-04-01',
                'filter_type': 'team',
            },
            expected=[
                {'date': date, 'value': value}
                for date, value in [
                    ('2019-04-01', 0),
                    ('2019-05-01', 1),
                    ('2019-06-01', 3),
                ]
            ],
        )

    def test_check_open_jobs_weekly(self):
        self.check_open_jobs(
            jobs=[
                (datetime(2019, 6, 19, tzinfo=utc), 5),
                (datetime(2019, 6, 17, tzinfo=utc), 5),
                (datetime(2019, 6, 10, tzinfo=utc), 5),
                (datetime(2019, 6, 4, tzinfo=utc), 5),
            ],
            params={
                'granularity': 'week',
                'date_end': '2019-06-17',
                'date_start': '2019-05-29',
                'filter_type': 'team',
            },
            expected=[
                {'date': date, 'value': value}
                for date, value in [
                    ('2019-05-27', 1),
                    ('2019-06-03', 2),
                    ('2019-06-10', 3),
                    ('2019-06-17', 2),
                ]
            ],
        )

    def test_check_open_jobs_daily(self):
        self.check_open_jobs(
            jobs=[
                (datetime(2019, 6, 2, tzinfo=utc), 1),
                (datetime(2019, 6, 3, tzinfo=utc), 2),
                (datetime(2019, 6, 4, tzinfo=utc), 1),
                (datetime(2019, 6, 5, tzinfo=utc), 1),
            ],
            params={
                'granularity': 'day',
                'date_end': '2019-06-05',
                'date_start': '2019-06-02',
                'filter_type': 'team',
            },
            expected=[
                {'date': date, 'value': value}
                for date, value in [
                    ('2019-06-02', 2),
                    ('2019-06-03', 2),
                    ('2019-06-04', 2),
                    ('2019-06-05', 1),
                ]
            ],
        )


def mix_date_with_current_time(date):
    return timezone.now().replace(year=date.year, month=date.month, day=date.day,)


@skip("TODO(ZOO-829)")
class JobAnalyticsTests(APITestCase):
    def generate_determined_status_workflow(
        self, timeline_name, status_group=None, proposal_update=None
    ):
        timeline = self.timelines[timeline_name]
        for proposal, date in timeline.items():
            if proposal_update:
                for attr, value in proposal_update.items():
                    setattr(proposal, attr, value)
            if status_group:
                proposal.status = ProposalStatus.objects.get(group=status_group)
            proposal.save()
            history = ProposalStatusHistory.objects.create(
                proposal=proposal, status=proposal.status, changed_by=self.client_admin
            )
            history.changed_at = mix_date_with_current_time(date)
            # to make sure later statuses would be later in history
            history.save()

    def generate_random_status_workflow(self, timeline_name, status_group_choices):
        # TODO workflow
        timeline = self.timelines[timeline_name]
        random_status_timeline = dict()

        for proposal, date in timeline.items():
            status = ProposalStatus.objects.get(
                group=random.choice(status_group_choices)
            )

            random_status_timeline[proposal] = (date, status)

        for proposal, (date, status) in random_status_timeline.items():
            proposal.status = status
            proposal.save()
            history = ProposalStatusHistory.objects.create(
                proposal=proposal, status=proposal.status, changed_by=self.client_admin
            )
            history.changed_at = mix_date_with_current_time(date)
            # to make sure later statuses would be later in history
            history.save()

        return random_status_timeline

    def get_end_day(self):
        return timezone.now().replace(year=2019, month=10, day=28)

    def get_days_ago(self, days):
        return self.get_end_day() - timedelta(days=days)

    def generate_workflow(self, actor_org='client'):
        self.client_obj = f.create_client()
        self.client_admin = f.create_client_administrator(self.client_obj)

        self.agency = f.create_agency()
        self.agency_admin = f.create_agency_administrator(self.agency)

        self.job = f.create_job(self.client_obj)

        f.create_contract(self.agency, self.client_obj)
        self.job.assign_agency(self.agency)

        self.end_day = timezone.now().replace(
            year=2019, month=10, day=28, hour=0, minute=0, second=0, microsecond=0
        )
        self.first_week_day = self.end_day.replace(month=9, day=30)

        for i in range(28):
            org = self.client_obj
            user = self.client_admin

            # alternate proposal owner for agency workflow
            if actor_org != 'client' and is_even(i):
                org = self.agency
                user = self.agency_admin

            setattr(self, f'_{i}_days_ago', self.end_day - timedelta(days=i))
            setattr(self, f'candidate_{i}', f.create_candidate(org))

            setattr(
                self,
                f'proposal_{i}',
                f.create_proposal(
                    self.job, getattr(self, f'candidate_{i}'), user, stage='longlist'
                ),
            )

        # See core.tests.dummies.jd-analytics-dump.json
        # for getting representation of generated data below

        def get_proposal(index):
            return getattr(self, f'proposal_{index}')

        # Fill timelines
        every_n_proposal = {
            'shortlisted': 6,
            'interviewed': 4,
            'contacted': 2,
            'identified': 1,
        }

        self.timelines = {
            timeline_name: {
                get_proposal(i): self.get_days_ago(i) for i in range(0, 28, period)
            }
            for timeline_name, period in every_n_proposal.items()
        }

        # IDENTIFIED WORKFLOW
        self.generate_determined_status_workflow(
            timeline_name='identified',
            status_group=ProposalStatusGroup.ASSOCIATED_TO_JOB.key,
        )

        # CONTACTED WORKFLOW
        self.random_contacted_statuses = self.generate_random_status_workflow(
            timeline_name='contacted',
            status_group_choices=PROPOSAL_STATUS_GROUP_CATEGORIES['contacted'],
        )

        # INTERVIEWED WORKFLOW
        self.random_interviewed_statuses = self.generate_random_status_workflow(
            timeline_name='interviewed',
            status_group_choices=PROPOSAL_STATUS_GROUP_CATEGORIES['interviewed'],
        )

        # SHORTLISTED WORKFLOW
        self.generate_determined_status_workflow(
            timeline_name='shortlisted',
            status_group='new',
            proposal_update={
                'stage': 'shortlist',
                'shortlisted_by': self.client_admin,
            },
        )

        self.default_chart_request_params = {
            'date_start': self._27_days_ago.strftime('%Y-%m-%d'),
            'date_end': self.end_day.strftime('%Y-%m-%d'),
            'job': self.job.id,
        }

        status_groups_to_serialize = (
            'new',
            'not_contacted',
            'interested',
            'not_interested',
            'not_interested_after_interview',
            'pending_interview',
            'pending_feedback',
            'not_suitable',
        )

        self.serialized_statuses = {
            group: s.ProposalStatusSerializer(
                ProposalStatus.objects.get(group=group)
            ).data
            for group in status_groups_to_serialize
        }

        self.snapshot_rest_data = {
            "candidate": {
                "name": "Test Candidate",
                "current_company": "",
                "current_position": "",
            }
        }

    def setUp(self):
        self.chart_url = '/api/stats/candidates_statuses/'
        self.proposal_snapshot_diff_url = '/api/proposals_snapshot_diff/'
        self.proposal_snapshot_state_url = '/api/proposals_snapshot_state/'
        self.maxDiff = None

    def _test_candidate_statuses_daily(self, org_actor):
        self.generate_workflow(org_actor)
        if org_actor == 'client':
            self.client.force_login(self.client_admin)
        else:
            self.client.force_login(self.agency_admin)

        response = self.client.get(
            self.chart_url, {'granularity': 'day', **self.default_chart_request_params}
        )

        expected_line_data = list()
        expected_diffs = list()

        # See core.tests.dummies.jd-analytics-dump.json
        # for getting representation of generated data

        first_data_point = {
            "date": self._27_days_ago.strftime('%Y-%m-%d'),  # 2019-10-01
            "identified": 1,
            "contacted": 0,
            "interviewed": 0,
            "shortlisted": 0,
        }
        expected_line_data.append(first_data_point)
        expected_diffs.append(first_data_point)

        for i in range(26, -1, -1):
            proposal = getattr(self, f'proposal_{i}')

            date = getattr(self, f'_{i}_days_ago').strftime('%Y-%m-%d')

            prev_point = expected_line_data[26 - i]

            steps_backwards = ('shortlisted', 'interviewed', 'contacted', 'identified')

            # agency shouldn't see client proposals
            if org_actor != 'client' and not is_even(i):
                diff_point = {key: 0 for key in steps_backwards}
            else:
                diff_point = dict()
                diff = 0
                for step in steps_backwards:
                    if proposal in self.timelines[step]:
                        diff = 1
                    diff_point[step] = diff

            diff_point['date'] = date

            line_point = {
                step: prev_point[step] + diff_point[step] for step in steps_backwards
            }
            line_point['date'] = date

            expected_line_data.append(line_point)
            expected_diffs.append(diff_point)

        expected = {"line_data": expected_line_data, "diffs": expected_diffs}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(underscoreize(response.json()), expected)

    def test_candidate_statuses_daily_client(self):
        self._test_candidate_statuses_daily('client')

    def test_candidate_statuses_daily_agency(self):
        """Agency should see only their own proposals"""
        self._test_candidate_statuses_daily('agency')

    def test_candidate_statuses_weekly(self):
        self.generate_workflow()
        self.client.force_login(self.client_admin)

        response = self.client.get(
            self.chart_url, {'granularity': 'week', **self.default_chart_request_params}
        )

        # See core.tests.dummies.jd-analytics-dump.json
        # for getting representation of generated data

        expected_diffs = [
            # from 2019-09-30 to 2019-10-07
            {
                "date": self.first_week_day.strftime('%Y-%m-%d'),
                "identified": 6,
                "contacted": 3,
                "interviewed": 1,
                "shortlisted": 1,
            },
            # from 2019-10-07 to 2019-10-14
            {
                "date": self._21_days_ago.strftime('%Y-%m-%d'),
                "identified": 7,
                "contacted": 3,
                "interviewed": 3,
                "shortlisted": 1,
            },
            # from 2019-10-14 to 2019-10-21
            {
                "date": self._14_days_ago.strftime('%Y-%m-%d'),
                "identified": 7,
                "contacted": 4,
                "interviewed": 2,
                "shortlisted": 1,
            },
            # from 2019-10-21 to 2019-10-28
            {
                "date": self._7_days_ago.strftime('%Y-%m-%d'),
                "identified": 7,
                "contacted": 3,
                "interviewed": 2,
                "shortlisted": 1,
            },
            # from 2019-10-28
            {
                "date": self._0_days_ago.strftime('%Y-%m-%d'),
                "identified": 1,
                "contacted": 1,
                "interviewed": 1,
                "shortlisted": 1,
            },
        ]

        expected_line_data = list()
        expected_line_data.append(expected_diffs[0])

        for i in range(1, len(expected_diffs)):
            expected_line_data.append(
                {
                    "date": expected_diffs[i]["date"],
                    "identified": expected_line_data[i - 1]["identified"]
                    + expected_diffs[i]["identified"],
                    "contacted": expected_line_data[i - 1]["contacted"]
                    + expected_diffs[i]["contacted"],
                    "interviewed": expected_line_data[i - 1]["interviewed"]
                    + expected_diffs[i]["interviewed"],
                    "shortlisted": expected_line_data[i - 1]["shortlisted"]
                    + expected_diffs[i]["shortlisted"],
                }
            )

        expected = {"line_data": expected_line_data, "diffs": expected_diffs}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(underscoreize(response.json()), expected)

    def test_candidate_statuses_monthly(self):
        self.generate_workflow()
        self.client.force_login(self.client_admin)

        response = self.client.get(
            self.chart_url,
            {'granularity': 'month', **self.default_chart_request_params},
        )

        # See core.tests.dummies.jd-analytics-dump.json
        # for getting representation of generated data

        expected_diffs = [
            {
                "date": self._27_days_ago.strftime('%Y-%m-%d'),  # 1st month day
                "identified": 28,
                "contacted": 14,
                "interviewed": 9,
                "shortlisted": 5,
            }
        ]

        expected = {
            "line_data": expected_diffs,
            "diffs": expected_diffs,
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(underscoreize(response.json()), expected)

    def test_candidate_statuses_non_proper_params(self):
        self.generate_workflow()
        self.client.force_login(self.client_admin)

        response = self.client.get(self.chart_url, {"date_start": 11})

        self.assertEqual(response.status_code, 400)

    def test_proposals_snapshot(self):
        self.generate_workflow()
        self.client.force_login(self.client_admin)

        response = self.client.get(
            self.proposal_snapshot_diff_url,
            {
                "date": self.end_day.strftime('%Y-%m-%d'),
                "job": self.job.id,
                "granularity": "day",
                "date_start": self._27_days_ago.strftime('%Y-%m-%d'),
                "date_end": self.end_day.strftime('%Y-%m-%d'),
            },
        )

        self.assertEqual(response.status_code, 200)

    def test_proposals_snapshot_diff_daily(self):
        self.generate_workflow()
        self.client.force_login(self.client_admin)

        response = self.client.get(
            self.proposal_snapshot_diff_url,
            {
                "date": self._21_days_ago.strftime('%Y-%m-%d'),
                "job": self.job.id,
                "granularity": "day",
                "date_start": self._27_days_ago.strftime('%Y-%m-%d'),
                "date_end": self.end_day.strftime('%Y-%m-%d'),
            },
        )

        expected = [
            {
                "changed_at": self._21_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses['not_contacted'],
                "proposal": self.proposal_21.id,
                **self.snapshot_rest_data,
            }
        ]

        self.assertEqual(underscoreize(response.json())['results'], expected)

    def test_proposals_snapshot_state_daily(self):
        self.generate_workflow()
        self.client.force_login(self.client_admin)

        response = self.client.get(
            self.proposal_snapshot_state_url,
            {
                "date": self._21_days_ago.strftime('%Y-%m-%d'),
                "job": self.job.id,
                "granularity": "day",
                "date_start": self._27_days_ago.strftime('%Y-%m-%d'),
                "date_end": self._21_days_ago.strftime('%Y-%m-%d'),
                "ordering": "-changedAt",
            },
        )

        expected = [
            {
                **self.snapshot_rest_data,
                "changed_at": self._21_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses['not_contacted'],
                "proposal": self.proposal_21.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._22_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses[
                    self.random_contacted_statuses[self.proposal_22][1].group
                ],
                "proposal": self.proposal_22.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._23_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses['not_contacted'],
                "proposal": self.proposal_23.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._24_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses['new'],
                "proposal": self.proposal_24.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._25_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses['not_contacted'],
                "proposal": self.proposal_25.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._26_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses[
                    self.random_contacted_statuses[self.proposal_26][1].group
                ],
                "proposal": self.proposal_26.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._27_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses['not_contacted'],
                "proposal": self.proposal_27.id,
            },
        ]

        self.assertCountEqual(underscoreize(response.json())['results'], expected)

    def test_proposals_snapshot_diff_weekly(self):
        self.generate_workflow()
        self.client.force_login(self.client_admin)

        response = self.client.get(
            self.proposal_snapshot_diff_url,
            {
                "date": self.first_week_day.strftime('%Y-%m-%d'),
                "job": self.job.id,
                "granularity": "week",
                "date_start": self._27_days_ago.strftime('%Y-%m-%d'),
                "date_end": self.end_day.strftime('%Y-%m-%d'),
                "ordering": '-changedAt',
            },
        )
        expected = [
            {
                **self.snapshot_rest_data,
                "changed_at": self._22_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses[
                    self.random_contacted_statuses[self.proposal_22][1].group
                ],
                "proposal": self.proposal_22.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._23_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses['not_contacted'],
                "proposal": self.proposal_23.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._24_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses['new'],
                "proposal": self.proposal_24.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._25_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses['not_contacted'],
                "proposal": self.proposal_25.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._26_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses[
                    self.random_contacted_statuses[self.proposal_26][1].group
                ],
                "proposal": self.proposal_26.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._27_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses['not_contacted'],
                "proposal": self.proposal_27.id,
            },
        ]

        self.assertEqual(underscoreize(response.json())['results'], expected)

    def test_proposals_snapshot_state_weekly(self):
        self.generate_workflow()
        self.client.force_login(self.client_admin)

        response = self.client.get(
            self.proposal_snapshot_state_url,
            {
                "date": self.first_week_day.strftime('%Y-%m-%d'),
                "job": self.job.id,
                "granularity": "week",
                "date_start": self._27_days_ago.strftime('%Y-%m-%d'),
                "date_end": self.end_day.strftime('%Y-%m-%d'),
                "ordering": '-changedAt',
            },
        )
        expected = [
            {
                **self.snapshot_rest_data,
                "changed_at": self._22_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses[
                    self.random_contacted_statuses[self.proposal_22][1].group
                ],
                "proposal": self.proposal_22.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._23_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses['not_contacted'],
                "proposal": self.proposal_23.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._24_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses['new'],
                "proposal": self.proposal_24.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._25_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses['not_contacted'],
                "proposal": self.proposal_25.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._26_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses[
                    self.random_contacted_statuses[self.proposal_26][1].group
                ],
                "proposal": self.proposal_26.id,
            },
            {
                **self.snapshot_rest_data,
                "changed_at": self._27_days_ago.strftime('%Y-%m-%d'),
                "status": self.serialized_statuses['not_contacted'],
                "proposal": self.proposal_27.id,
            },
        ]

        self.assertEqual(underscoreize(response.json())['results'], expected)

    def test_proposals_snapshot_non_proper_params(self):
        self.generate_workflow()
        self.client.force_login(self.client_admin)

        response = self.client.get(
            self.proposal_snapshot_diff_url, {}  # required params is missing
        )

        self.assertEqual(response.status_code, 400)
