from unittest.mock import patch
from rest_framework.reverse import reverse

from rest_framework.test import APITestCase
from core.factories import (
    CareerSiteJobPostingFactory,
    ClientAdministratorFactory,
    ClientCandidateFactory,
    ClientFactory,
    ClientInternalRecruiterFactory,
    ClientJobFactory,
    ClientProposalFactory,
    ClientStandardUserFactory,
    PrivateJobPostingFactory,
    ProposalInterviewAssessmentFactory,
)


class ClientRolesTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_obj = ClientFactory()
        cls.admin = ClientAdministratorFactory().user
        cls.internal_recruiter = ClientInternalRecruiterFactory().user
        cls.hiring_manager = ClientStandardUserFactory().user
        cls.job_interviewer = ClientStandardUserFactory().user
        cls.proposal_interviewer = ClientStandardUserFactory().user
        cls.standard_user = ClientStandardUserFactory().user
        # hm setup
        cls.job = ClientJobFactory(owner=cls.admin)
        cls.job.recruiters.add(cls.internal_recruiter)
        cls.job.assign_manager(cls.hiring_manager)
        # interviewer setup
        interview = cls.job.interview_templates.first()
        interview.interviewer = cls.job_interviewer
        interview.save()
        cls.candidate = ClientCandidateFactory()
        cls.proposal = ClientProposalFactory(job=cls.job, candidate=cls.candidate)
        proposal_interview = cls.proposal.interviews.last()
        proposal_interview.interviewer = cls.proposal_interviewer
        proposal_interview.save()
        CareerSiteJobPostingFactory(job=cls.job)
        PrivateJobPostingFactory(job=cls.job)

    def setUp(self):
        super().setUp()
        # not assigned
        self.other_job = ClientJobFactory()
        self.other_candidate = ClientCandidateFactory()
        self.other_proposal = ClientProposalFactory(
            job=self.other_job, candidate=self.other_candidate
        )
        CareerSiteJobPostingFactory(job=self.other_job)
        PrivateJobPostingFactory(job=self.other_job)

    def setup_editing_test_data(self):
        self.job2 = ClientJobFactory(owner=self.admin)
        self.job2.recruiters.add(self.internal_recruiter)
        self.job2.assign_manager(self.hiring_manager)
        interview = self.job2.interview_templates.first()
        interview.interviewer = self.job_interviewer
        interview.save()
        self.candidate2 = ClientCandidateFactory()
        self.proposal2 = ClientProposalFactory(job=self.job2, candidate=self.candidate2)
        proposal_interview = self.proposal2.interviews.last()
        proposal_interview.interviewer = self.proposal_interviewer
        proposal_interview.save()
        CareerSiteJobPostingFactory(job=self.job2)
        PrivateJobPostingFactory(job=self.job2)

    # Managers
    def test_get_managers_list(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(reverse('manager-list'))
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    # Candidates
    def test_get_candidates_list(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(reverse('candidate-list'))
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 200),
            (self.job_interviewer, 200),
            (self.proposal_interviewer, 200),
            (self.standard_user, 200),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_get_candidates_detail_own_assigned(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(
                    reverse('candidate-detail', kwargs={'pk': self.candidate.pk})
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 200),
            (self.job_interviewer, 200),
            (self.proposal_interviewer, 200),
            (self.standard_user, 404),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_get_candidates_detail_own_not_assigned(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(
                    reverse('candidate-detail', kwargs={'pk': self.other_candidate.pk})
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 404),
            (self.job_interviewer, 404),
            (self.proposal_interviewer, 404),
            (self.standard_user, 404),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_post_candidates_create(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.post(
                    reverse('candidate-list'), {'bla': 'bla'}, format='json'
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 400),
            (self.internal_recruiter, 400),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    # Jobs
    def test_get_jobs_list(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(reverse('job-list'))
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 200),
            (self.job_interviewer, 200),
            (self.proposal_interviewer, 200),
            (self.standard_user, 200),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_get_jobs_detail_own_assigned(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(
                    reverse('job-detail', kwargs={'pk': self.job.pk})
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 200),
            (self.job_interviewer, 200),
            (self.proposal_interviewer, 200),
            (self.standard_user, 404),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_get_jobs_detail_own_not_assigned(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(
                    reverse('job-detail', kwargs={'pk': self.other_job.pk})
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 404),
            (self.job_interviewer, 404),
            (self.proposal_interviewer, 404),
            (self.standard_user, 404),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_post_jobs_create(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.post(
                    reverse('job-list'), {'bla': 'bla'}, format='json'
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 400),
            (self.internal_recruiter, 400),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_put_jobs_update_assigned(self):
        self.setup_editing_test_data()

        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.put(
                    reverse('job-detail', kwargs={'pk': self.job2.pk}),
                    {'bla': 'bla'},
                    format='json',
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 400),
            (self.internal_recruiter, 400),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_put_jobs_update_not_assigned(self):
        self.setup_editing_test_data()

        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.put(
                    reverse('job-detail', kwargs={'pk': self.other_job.pk}),
                    {'bla': 'bla'},
                    format='json',
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 400),
            (self.internal_recruiter, 403),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    # Jobs -- Public
    def test_create_private_job_posting(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.post(
                    reverse('private-job-posting-list'),
                    {'pk': self.job.pk},
                    format='json',
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 400),
            (self.internal_recruiter, 400),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_create_career_site_job_posting(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.post(
                    reverse('career-site-job-posting-list'),
                    {'job_id': self.job.pk},
                    format='json',
                )
                self.assertEqual(response.status_code, expected_code, response.json())

        to_test = [
            (self.admin, 400),
            (self.internal_recruiter, 400),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_get_private_job_posting(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(
                    reverse(
                        'private-job-posting-detail', kwargs={'job_id': self.job.pk}
                    )
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 200),
            (self.job_interviewer, 200),
            (self.proposal_interviewer, 200),
            (self.standard_user, 200),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_get_career_site_job_posting(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(
                    reverse(
                        'career-site-job-posting-detail', kwargs={'job_id': self.job.pk}
                    )
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 200),
            (self.job_interviewer, 200),
            (self.proposal_interviewer, 200),
            (self.standard_user, 200),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_update_private_job_posting(self):
        self.setup_editing_test_data()

        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.patch(
                    reverse(
                        'private-job-posting-detail', kwargs={'job_id': self.job2.pk},
                    ),
                    {'bla': 'bla'},
                    format='json',
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_update_careeer_site_job_posting(self):
        self.setup_editing_test_data()

        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.patch(
                    reverse(
                        'career-site-job-posting-detail',
                        kwargs={'job_id': self.job2.pk},
                    ),
                    {'bla': 'bla'},
                    format='json',
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    # Jobs -- Files
    def test_get_job_files_retrieve(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(
                    reverse(
                        'job-file-detail',
                        kwargs={'pk': self.job.jobfile_set.first().pk},
                    )
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 200),
            (self.job_interviewer, 200),
            (self.proposal_interviewer, 200),
            (self.standard_user, 404),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_patch_job_files_update(self):
        self.setup_editing_test_data()

        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.patch(
                    reverse(
                        'job-file-detail',
                        kwargs={'pk': self.job2.jobfile_set.first().pk},
                    ),
                    {'title': 'new name'},
                    format='multipart',
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 200),
            (self.job_interviewer, 200),
            (self.proposal_interviewer, 200),
            (self.standard_user, 404),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    # Proposals
    def test_get_proposals_list(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(reverse('proposal-list'))
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 200),
            (self.job_interviewer, 200),
            (self.proposal_interviewer, 200),
            (self.standard_user, 200),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_get_proposals_detail_own_assigned(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(
                    reverse('proposal-detail', kwargs={'pk': self.proposal.pk})
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 200),
            (self.job_interviewer, 200),
            (self.proposal_interviewer, 200),
            (self.standard_user, 404),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_get_proposals_detail_own_not_assigned(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(
                    reverse('proposal-detail', kwargs={'pk': self.other_proposal.pk})
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 404),
            (self.job_interviewer, 404),
            (self.proposal_interviewer, 404),
            (self.standard_user, 404),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_post_proposals_create(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.post(
                    reverse('proposal-list'), {'bla': 'bla'}, format='json'
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 400),
            (self.internal_recruiter, 400),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_get_proposal_questions_list(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(reverse('proposalquestion-list'))
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 200),
            (self.job_interviewer, 200),
            (self.proposal_interviewer, 200),
            (self.standard_user, 200),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_post_proposal_questions_create(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.post(
                    reverse('proposalquestion-list'), {'bla': 'bla'}
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 403),
            (self.internal_recruiter, 403),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_patch_proposal_questions_update(self):
        self.setup_editing_test_data()
        proposal_question = self.proposal2.questions.first()

        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.put(
                    reverse(
                        'proposalquestion-detail', kwargs={'pk': proposal_question.pk}
                    ),
                    {'bla': 'bla'},
                    format='json',
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 400),
            (self.internal_recruiter, 400),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_post_proposal_quick_actions(self):
        self.setup_editing_test_data()

        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.post(
                    reverse('proposal-quick-actions', kwargs={'pk': self.proposal2.pk}),
                    {'bla': 'bla'},
                    format='json',
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 400),
            (self.internal_recruiter, 400),
            (self.hiring_manager, 400),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 404),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_get_proposal_interviews_list(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(reverse('proposal_interviews-list'))
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 200),
            (self.job_interviewer, 200),
            (self.proposal_interviewer, 200),
            (self.standard_user, 200),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_post_proposal_interviews_create(self):
        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.post(
                    reverse('proposal_interviews-list'), {'bla': 'bla'}, format='json'
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 400),
            (self.internal_recruiter, 400),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_patch_proposal_interviews_update(self):
        self.setup_editing_test_data()
        proposal_interview = self.proposal2.interviews.first()

        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.put(
                    reverse(
                        'proposal_interviews-detail',
                        kwargs={'pk': proposal_interview.pk},
                    ),
                    {'bla': 'bla'},
                    format='json',
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_delete_proposal_interviews(self):
        def check(user, expected_code, **kwargs):
            self.setup_editing_test_data()
            proposal_interview = self.proposal2.interviews.last()
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.delete(
                    reverse(
                        'proposal_interviews-detail',
                        kwargs={'pk': proposal_interview.pk},
                    )
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 204),
            (self.internal_recruiter, 204),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_delete_proposal_interviews_current_interview(self):
        self.setup_editing_test_data()
        proposal_interview = self.proposal2.interviews.first()

        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.delete(
                    reverse(
                        'proposal_interviews-detail',
                        kwargs={'pk': proposal_interview.pk},
                    )
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 403),
            (self.internal_recruiter, 403),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 403),
            (self.standard_user, 403),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_post_proposal_interview_assessment_create(self):
        self.setup_editing_test_data()
        proposal_interview = self.proposal2.interviews.last()

        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.post(
                    reverse(
                        'proposal_interviews-assessment',
                        kwargs={'pk': proposal_interview.pk},
                    ),
                    {'bla': 'bla'},
                    format='json',
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 400),
            (self.internal_recruiter, 400),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 400),
            (self.standard_user, 404),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)

    def test_get_proposal_interview_assessment_read(self):
        self.setup_editing_test_data()
        proposal_interview = self.proposal2.interviews.last()
        assessment = ProposalInterviewAssessmentFactory(interview=proposal_interview)

        def check(user, expected_code, **kwargs):
            with self.subTest(role=user.profile, **kwargs):
                self.client.force_login(user)
                response = self.client.get(
                    reverse(
                        'proposal_interviews-assessment',
                        kwargs={'pk': proposal_interview.pk},
                    ),
                )
                self.assertEqual(response.status_code, expected_code)

        to_test = [
            (self.admin, 200),
            (self.internal_recruiter, 200),
            (self.hiring_manager, 403),
            (self.job_interviewer, 403),
            (self.proposal_interviewer, 200),
            (self.standard_user, 404),
        ]
        for i, item in enumerate(to_test):
            check(*item, index=i)
