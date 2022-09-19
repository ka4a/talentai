import copy
from decimal import Decimal
from math import floor
from unittest import skip

from rest_framework.test import APITestCase, APIRequestFactory
from djangorestframework_camel_case.util import camelize, underscoreize
from djangorestframework_camel_case.util import camelize
from djmoney.money import Money
from djmoney.contrib.exchange.models import Rate as CurrencyRate, ExchangeBackend

from core import models as m
from core import fixtures as f
from core import serializers as s
from core.tests.generic_response_assertions import GenericResponseAssertionSet
from core.annotations import annotate_proposal_deal_pipeline_metrics

factory = APIRequestFactory()


HIRING_FEE_C = 0.3
FIRST_ROUND_C = 0.1
INTERMEDIATE_ROUND_C = 0.3
FINAL_ROUND_C = 0.5
OFFER_C = 0.8

REALISM_COEFFICIENTS = {
    'first_round': FIRST_ROUND_C,
    'intermediate_round': INTERMEDIATE_ROUND_C,
    'final_round': FINAL_ROUND_C,
    'offer': OFFER_C,
}

DEFAULT_SALARY = 1000000  # / 1 000 000
DEFAULT_CURRENCY = 'JPY'
DEFAULT_CANDIDATE = {
    'current_salary': Money(DEFAULT_SALARY, DEFAULT_CURRENCY),
}

DEFAULT_METRICS = {
    'total': {'first_round': 0, 'intermediate_round': 0, 'final_round': 0, 'offer': 0,},
    'realistic': {
        'first_round': 0,
        'intermediate_round': 0,
        'final_round': 0,
        'offer': 0,
    },
}


@skip("TODO(ZOO-829)")
class DealPipelineTests(APITestCase):
    def setUp(self):
        self.metrics_viewname = 'deal_pipeline-predicted-values'
        self.candidates_viewname = 'deal_pipeline-list'
        self.assert_response = GenericResponseAssertionSet(self)
        self.FIRST_ROUND_STATUS = m.ProposalStatus.objects.filter(
            deal_stage=m.ProposalDealStages.FIRST_ROUND.key
        ).first()
        self.INTERMEDIATE_ROUND_STATUS = m.ProposalStatus.objects.filter(
            deal_stage=m.ProposalDealStages.INTERMEDIATE_ROUND.key
        ).first()
        self.FINAL_ROUND_STATUS = m.ProposalStatus.objects.filter(
            deal_stage=m.ProposalDealStages.FINAL_ROUND.key
        ).first()
        self.OFFER_STATUS = m.ProposalStatus.objects.filter(
            deal_stage=m.ProposalDealStages.OFFER.key
        ).first()

    def generate_expected_data(self, **kwargs):
        expected_data = copy.deepcopy(DEFAULT_METRICS)
        for round, value in kwargs.items():
            expected_data['total'][round] = int(float(value.amount) * HIRING_FEE_C)
            expected_data['realistic'][round] = int(
                float(value.amount) * HIRING_FEE_C * REALISM_COEFFICIENTS[round]
            )

        total_total = sum(expected_data['total'].values())
        realistic_total = sum(expected_data['realistic'].values())

        expected_data['total']['total'] = total_total
        expected_data['realistic']['total'] = realistic_total

        return camelize(expected_data)

    def test_empty_pipeline(self):
        """Should return zeroes if there're no candidates in Deal Pipeline."""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        self.client.force_login(agency_admin)

        expected_data = self.generate_expected_data()

        self.assert_response.ok(
            'get', self.metrics_viewname, expected_data=expected_data
        )

    def test_one_job_one_opening_one_candidate_out_of_pipeline(self):
        """Should return zero values"""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        self.client.force_login(agency_admin)

        job = f.create_job(agency)
        candidate = f.create_candidate(agency, **DEFAULT_CANDIDATE)
        f.create_proposal(job, candidate, agency_admin, stage='longlist')

        expected_data = self.generate_expected_data()

        self.assert_response.ok(
            'get', self.metrics_viewname, expected_data=expected_data
        )

    def test_one_job_one_opening_one_candidate_first_stage(self):
        """Should calculate metrics for one candidate"""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        self.client.force_login(agency_admin)

        job = f.create_job(agency)
        candidate = f.create_candidate(agency, **DEFAULT_CANDIDATE)
        proposal = f.create_proposal(job, candidate, agency_admin)
        proposal.status = self.FIRST_ROUND_STATUS
        proposal.save()

        expected_data = self.generate_expected_data(
            first_round=candidate.current_salary
        )

        self.assert_response.ok(
            'get', self.metrics_viewname, expected_data=expected_data
        )

    def test_one_job_multiple_candidates_different_stages(self):
        """Should calculate metrics for candidate with highest deal stage"""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        self.client.force_login(agency_admin)

        job = f.create_job(agency)
        candidate_1 = f.create_candidate(agency, **DEFAULT_CANDIDATE)
        candidate_2 = f.create_candidate(agency, **DEFAULT_CANDIDATE)

        proposal_1 = f.create_proposal(job, candidate_1, agency_admin)
        proposal_2 = f.create_proposal(job, candidate_2, agency_admin)

        proposal_1.status = self.INTERMEDIATE_ROUND_STATUS
        proposal_1.save()
        proposal_2.status = self.FINAL_ROUND_STATUS  # highest deal stage
        proposal_2.save()

        expected_data = self.generate_expected_data(
            final_round=candidate_2.current_salary
        )

        self.assert_response.ok(
            'get', self.metrics_viewname, expected_data=expected_data
        )

    def test_one_job_multiple_candidates_same_stage_different_salary(self):
        """Should calculate metrics for candidate with highest salary"""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        self.client.force_login(agency_admin)

        job = f.create_job(agency)
        candidate_1 = f.create_candidate(agency, **DEFAULT_CANDIDATE)
        candidate_2 = f.create_candidate(agency, current_salary=DEFAULT_SALARY * 2)

        proposal_1 = f.create_proposal(job, candidate_1, agency_admin)
        proposal_2 = f.create_proposal(job, candidate_2, agency_admin)

        proposal_1.status = self.INTERMEDIATE_ROUND_STATUS
        proposal_1.save()
        proposal_2.status = self.INTERMEDIATE_ROUND_STATUS  # has a highest salary
        proposal_2.save()

        expected_data = self.generate_expected_data(
            intermediate_round=candidate_2.current_salary
        )

        self.assert_response.ok(
            'get', self.metrics_viewname, expected_data=expected_data
        )

    def test_one_job_n_openings_n_candidates(self):
        """Should calculate metrics for 2 candidates"""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        self.client.force_login(agency_admin)

        job = f.create_job(agency, openings_count=2)
        candidate_1 = f.create_candidate(agency, **DEFAULT_CANDIDATE)
        candidate_2 = f.create_candidate(agency, **DEFAULT_CANDIDATE)

        proposal_1 = f.create_proposal(job, candidate_1, agency_admin)
        proposal_2 = f.create_proposal(job, candidate_2, agency_admin)

        proposal_1.status = self.INTERMEDIATE_ROUND_STATUS
        proposal_1.save()
        proposal_2.status = self.FINAL_ROUND_STATUS
        proposal_2.save()

        expected_data = self.generate_expected_data(
            intermediate_round=candidate_1.current_salary,
            final_round=candidate_2.current_salary,
        )

        self.assert_response.ok(
            'get', self.metrics_viewname, expected_data=expected_data
        )

    def test_multiple_jobs_multiple_candidates(self):
        """Should calculate metrics for all jobs"""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        self.client.force_login(agency_admin)

        job_1 = f.create_job(agency)
        job_2 = f.create_job(agency)
        candidate_1 = f.create_candidate(agency, **DEFAULT_CANDIDATE)
        candidate_2 = f.create_candidate(agency, **DEFAULT_CANDIDATE)

        proposal_1 = f.create_proposal(job_1, candidate_1, agency_admin)
        proposal_2 = f.create_proposal(job_2, candidate_2, agency_admin)

        proposal_1.status = self.INTERMEDIATE_ROUND_STATUS
        proposal_1.save()
        proposal_2.status = self.FINAL_ROUND_STATUS
        proposal_2.save()

        expected_data = self.generate_expected_data(
            intermediate_round=candidate_1.current_salary,
            final_round=candidate_1.current_salary,
        )

        self.assert_response.ok(
            'get', self.metrics_viewname, expected_data=expected_data
        )

    def test_one_job_n_openings_all_stages(self):
        """Should calculate metrics for one candidate per stage"""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        self.client.force_login(agency_admin)

        job = f.create_job(agency, openings_count=10)
        candidate_1 = f.create_candidate(agency, **DEFAULT_CANDIDATE)
        candidate_2 = f.create_candidate(agency, **DEFAULT_CANDIDATE)
        candidate_3 = f.create_candidate(agency, **DEFAULT_CANDIDATE)
        candidate_4 = f.create_candidate(agency, **DEFAULT_CANDIDATE)
        candidate_5 = f.create_candidate(agency, **DEFAULT_CANDIDATE)

        proposal_1 = f.create_proposal(job, candidate_1, agency_admin)
        proposal_2 = f.create_proposal(job, candidate_2, agency_admin)
        proposal_3 = f.create_proposal(job, candidate_3, agency_admin)
        proposal_4 = f.create_proposal(job, candidate_4, agency_admin)
        proposal_5 = f.create_proposal(
            job, candidate_5, agency_admin, stage='longlist'
        )  # out of deal pipeline

        proposal_1.status = self.FIRST_ROUND_STATUS
        proposal_1.save()
        proposal_2.status = self.INTERMEDIATE_ROUND_STATUS
        proposal_2.save()
        proposal_3.status = self.FINAL_ROUND_STATUS
        proposal_3.save()
        proposal_4.status = self.OFFER_STATUS
        proposal_4.save()

        expected_data = self.generate_expected_data(
            first_round=candidate_1.current_salary,
            intermediate_round=candidate_2.current_salary,
            final_round=candidate_3.current_salary,
            offer=candidate_4.current_salary,
        )
        self.assert_response.ok(
            'get', self.metrics_viewname, expected_data=expected_data
        )

    def test_multilple_jobs_n_openings_multiple_candidates_all_stages(self):
        """Should calculate metrics for all jobs"""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        self.client.force_login(agency_admin)

        job_1 = f.create_job(agency)
        job_2 = f.create_job(agency)
        job_3 = f.create_job(agency, openings_count=2)
        job_4 = f.create_job(agency, openings_count=2)
        job_5 = f.create_job(agency, openings_count=2)

        candidate_1 = f.create_candidate(agency, current_salary=DEFAULT_SALARY * 1)
        candidate_2 = f.create_candidate(agency, current_salary=DEFAULT_SALARY * 2)
        candidate_3 = f.create_candidate(agency, current_salary=DEFAULT_SALARY * 3)
        candidate_4 = f.create_candidate(agency, current_salary=DEFAULT_SALARY * 4)
        candidate_5 = f.create_candidate(agency, current_salary=DEFAULT_SALARY * 5)
        candidate_5 = f.create_candidate(agency, current_salary=DEFAULT_SALARY * 6)
        candidate_6 = f.create_candidate(agency, current_salary=DEFAULT_SALARY * 7)
        candidate_7 = f.create_candidate(agency, current_salary=DEFAULT_SALARY * 8)
        candidate_8 = f.create_candidate(agency, current_salary=DEFAULT_SALARY * 9)
        candidate_9 = f.create_candidate(agency, current_salary=DEFAULT_SALARY * 10)
        candidate_10 = f.create_candidate(agency, current_salary=DEFAULT_SALARY * 11)

        proposal_1 = f.create_proposal(job_1, candidate_1, agency_admin)
        proposal_2 = f.create_proposal(job_1, candidate_2, agency_admin)

        proposal_3 = f.create_proposal(job_2, candidate_3, agency_admin)
        proposal_4 = f.create_proposal(job_2, candidate_4, agency_admin)

        proposal_5 = f.create_proposal(job_3, candidate_5, agency_admin)
        proposal_6 = f.create_proposal(job_3, candidate_6, agency_admin)

        proposal_7 = f.create_proposal(job_4, candidate_7, agency_admin)
        proposal_8 = f.create_proposal(job_4, candidate_8, agency_admin)

        proposal_9 = f.create_proposal(job_5, candidate_9, agency_admin)
        proposal_10 = f.create_proposal(job_5, candidate_10, agency_admin)

        # job-1: same stage, 1 opening
        proposal_1.status = self.FIRST_ROUND_STATUS
        proposal_1.save()
        proposal_2.status = self.FIRST_ROUND_STATUS  # highest salary
        proposal_2.save()

        # job-2, same stage, 1 opening
        proposal_3.status = self.INTERMEDIATE_ROUND_STATUS
        proposal_3.save()
        proposal_4.status = self.INTERMEDIATE_ROUND_STATUS  # highest salary
        proposal_4.save()

        # job-3
        proposal_5.status = self.FINAL_ROUND_STATUS
        proposal_5.save()
        proposal_6.status = self.INTERMEDIATE_ROUND_STATUS
        proposal_6.save()

        # job-4
        proposal_7.status = self.FIRST_ROUND_STATUS
        proposal_7.save()
        proposal_8.status = self.INTERMEDIATE_ROUND_STATUS
        proposal_8.save()

        # job-5
        proposal_9.status = self.OFFER_STATUS
        proposal_9.save()
        proposal_10.status = self.FINAL_ROUND_STATUS
        proposal_10.save()

        expected_data = self.generate_expected_data(
            first_round=sum([candidate_2.current_salary, candidate_7.current_salary]),
            intermediate_round=sum(
                [
                    candidate_4.current_salary,
                    candidate_6.current_salary,
                    candidate_8.current_salary,
                ]
            ),
            final_round=sum([candidate_5.current_salary, candidate_10.current_salary]),
            offer=candidate_9.current_salary,
        )

        self.assert_response.ok(
            'get', self.metrics_viewname, expected_data=expected_data
        )

    def test_one_job_n_openings_different_currencies(self):
        """Should calculate metrics with properly converted salaries"""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        self.client.force_login(agency_admin)

        job = f.create_job(agency, openings_count=3)

        candidate_1 = f.create_candidate(agency, current_salary=Money(10000000, 'USD'),)
        candidate_2 = f.create_candidate(agency, current_salary=Money(10000000, 'JPY'),)
        candidate_3 = f.create_candidate(agency, current_salary=Money(10000000, 'EUR'),)

        proposal_1 = f.create_proposal(job, candidate_1, agency_admin)
        proposal_2 = f.create_proposal(job, candidate_2, agency_admin)
        proposal_3 = f.create_proposal(job, candidate_3, agency_admin)

        proposal_1.status = self.INTERMEDIATE_ROUND_STATUS
        proposal_1.save()
        proposal_2.status = self.FINAL_ROUND_STATUS
        proposal_2.save()
        proposal_3.status = self.OFFER_STATUS
        proposal_3.save()

        # create test currency exchange rates
        e_backend = ExchangeBackend.objects.create(name='test', base_currency='JPY')
        rates = [
            CurrencyRate(currency='USD', value=0.0085, backend=e_backend),
            CurrencyRate(currency='EUR', value=0.0075, backend=e_backend),
            CurrencyRate(currency='JPY', value=1.0, backend=e_backend),
        ]
        CurrencyRate.objects.bulk_create(rates)

        salary_1 = lambda: None
        salary_2 = lambda: None
        salary_3 = lambda: None
        setattr(
            salary_1,
            'amount',
            candidate_1.current_salary.amount
            / CurrencyRate.objects.get(
                currency=candidate_1.current_salary_currency
            ).value,
        )
        setattr(
            salary_2,
            'amount',
            candidate_2.current_salary.amount
            / CurrencyRate.objects.get(
                currency=candidate_2.current_salary_currency
            ).value,
        )
        setattr(
            salary_3,
            'amount',
            candidate_3.current_salary.amount
            / CurrencyRate.objects.get(
                currency=candidate_3.current_salary_currency
            ).value,
        )

        expected_data = self.generate_expected_data(
            intermediate_round=salary_1, final_round=salary_2, offer=salary_3
        )

        self.assert_response.ok(
            'get', self.metrics_viewname, expected_data=expected_data
        )

    def test_deal_pipeline_candidates(self):
        """Should return deal pipeline candidates data"""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        candidate_1 = f.create_candidate(agency)
        candidate_2 = f.create_candidate(agency)
        job = f.create_job(agency, openings_count=2)

        proposal_1 = f.create_proposal(job, candidate_1, agency_admin)
        proposal_2 = f.create_proposal(job, candidate_2, agency_admin)
        proposal_1.status = self.FIRST_ROUND_STATUS
        proposal_1.save()
        proposal_2.status = self.INTERMEDIATE_ROUND_STATUS
        proposal_2.save()

        request = factory.get('/')
        request.user = agency_admin
        context = {'request': request}
        self.client.force_login(agency_admin)
        expected_data = s.DealPipelineProposalSerializer(
            annotate_proposal_deal_pipeline_metrics(
                m.Proposal.objects.filter(pk__in=[proposal_1.pk, proposal_2.pk]), agency
            ),
            many=True,
            context=context,
        ).data

        response = self.assert_response.ok('get', self.candidates_viewname)
        self.assertEqual(underscoreize(response.json()['results']), expected_data)

    def test_one_candidate_multiple_jobs(self):
        """One candidate should be included only once into the deal pipeline"""
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        self.client.force_login(agency_admin)

        candidate_1 = f.create_candidate(agency)
        candidate_2 = f.create_candidate(agency)

        # 1st candidate, different stages
        job_1 = f.create_job(agency)
        job_2 = f.create_job(agency)

        # 2nd candidate, same stage,
        job_3 = f.create_job(agency)
        job_4 = f.create_job(agency)

        proposal_1 = f.create_proposal(job_1, candidate_1, agency_admin)
        proposal_2 = f.create_proposal(job_2, candidate_1, agency_admin)

        proposal_3 = f.create_proposal(job_3, candidate_2, agency_admin)
        proposal_4 = f.create_proposal(job_4, candidate_2, agency_admin)

        # job_1
        proposal_1.status = self.FIRST_ROUND_STATUS
        proposal_1.save()
        proposal_2.status = self.INTERMEDIATE_ROUND_STATUS  # highest stage
        proposal_2.save()

        # job_2
        proposal_3.status = self.FINAL_ROUND_STATUS  # created earlier
        proposal_3.save()
        proposal_4.status = self.FINAL_ROUND_STATUS
        proposal_4.save()

        request = factory.get('/')
        request.user = agency_admin
        context = {'request': request}
        self.client.force_login(agency_admin)

        expected_data = s.DealPipelineProposalSerializer(
            annotate_proposal_deal_pipeline_metrics(
                m.Proposal.objects.filter(pk__in=[proposal_2.pk, proposal_3.pk]), agency
            ),
            many=True,
            context=context,
        ).data

        response = self.assert_response.ok('get', self.candidates_viewname)
        self.assertEqual(underscoreize(response.json()['results']), expected_data)

    def _test_filtration(self, openings_count=2, contribution=0.4):
        self.maxDiff = None
        agency = f.create_agency()
        basic_income = 1000

        users = [f.create_recruiter(agency) for _ in range(2)]
        salary_multiplier = {
            users[0].id: 0.6,
            users[1].id: 0.4,
        }

        statuses = [
            self.FIRST_ROUND_STATUS,
            self.INTERMEDIATE_ROUND_STATUS,
            self.FINAL_ROUND_STATUS,
            self.OFFER_STATUS,
        ]

        for status in statuses:
            job = f.create_job(agency, openings_count=openings_count)
            for user in users:
                f.create_proposal(
                    job,
                    f.create_candidate(
                        agency,
                        current_salary=Money(
                            floor(basic_income * salary_multiplier[user.id]), 'JPY'
                        ),
                    ),
                    user,
                    status=status,
                )

        self.client.force_login(f.create_agency_administrator(agency))
        params = {'status_last_updated_by': users[1].id}

        data = self.assert_response.ok(
            'get', 'deal_pipeline-predicted-values', params=params
        ).json()

        expected = {'total': {'total': 0}, 'realistic': {'total': 0}}
        rounds = ['first_round', 'intermediate_round', 'final_round', 'offer']

        basic_income = 1000
        proposal_worth = (
            basic_income * contribution * agency.deal_hiring_fee_coefficient
        )

        for key in rounds:
            expected['total'][key] = proposal_worth
            expected['total']['total'] += expected['total'][key]
            expected['realistic'][key] = proposal_worth * REALISM_COEFFICIENTS[key]
            expected['realistic']['total'] += expected['realistic'][key]

        expected = camelize(expected)

        self.assertDictEqual(expected, data)

    def test_filtration(self):
        self._test_filtration(2, 0.4)

    def test_filtration_one_opening(self):
        self._test_filtration(1, 0)
