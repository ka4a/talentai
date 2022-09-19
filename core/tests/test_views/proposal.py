from datetime import datetime

from django.utils.dateparse import parse_datetime
from django.utils.timezone import utc

from djangorestframework_camel_case.util import camelize
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from core import fixtures as f, serializers as s, models as m, factories as fa
from core.factories import (
    ClientFactory,
    UserFactory,
    ClientCandidateFactory,
    ClientJobFactory,
    ClientProposalFactory,
)
from core.tests.generic_response_assertions import GenericResponseAssertionSet
from core.utils import org_filter

DRAFT = m.FeeStatus.DRAFT.key
APPROVED = m.FeeStatus.APPROVED.key
NEEDS_REVISION = m.FeeStatus.NEEDS_REVISION.key
PENDING = m.FeeStatus.PENDING.key


def is_file_id_not_found(data, files, case):
    for file_info in data['candidate']['files']:
        if file_info['id'] == files[case].id:
            return False
    return True


class ProposalTests(APITestCase):
    """Tests related to the Proposal viewset."""

    def setUp(self):
        """Create the required objects during initialization."""
        super().setUp()
        self.client_obj = f.create_client()
        self.job = f.create_job(self.client_obj)

        self.agency = f.create_agency()
        self.agency_admin = f.create_agency_administrator(self.agency)
        self.recruiter = f.create_recruiter(self.agency)
        self.candidate_1 = f.create_candidate(self.agency)
        self.candidate_2 = f.create_candidate(self.agency)
        self.client_candidate = f.create_candidate(self.client_obj)

        f.create_contract(self.agency, self.client_obj)
        self.job.assign_agency(self.agency)

        self.client_admin = fa.ClientAdministratorFactory(client=self.client_obj).user
        self.default_login()
        self.maxDiff = None
        self.assert_response = GenericResponseAssertionSet(self)

    def default_login(self):
        self.client.force_login(self.client_admin)

    def test_get_proposals(self):
        """Should return a list of all Proposals."""
        proposal_1 = f.create_proposal(self.job, self.candidate_1, self.recruiter)
        proposal_2 = f.create_proposal(self.job, self.candidate_2, self.recruiter)
        # queryset annotation emulation
        proposal_1.last_activity_at = None
        proposal_2.last_activity_at = None

        url = reverse('proposal-list')
        response = self.client.get(url)

        proposals_data = s.ProposalSerializer(
            [proposal_1, proposal_2],
            context={'request': response.wsgi_request},
            many=True,
        ).data
        for p in proposals_data:
            p['candidate']['note'] = ''

        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.json()['results'], camelize(proposals_data))

    def test_get_proposals_without_proposals(self):
        """Should return an empty list if no Proposals created."""
        url = reverse('proposal-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'], [])

    def test_get_proposal(self):
        """Should return Proposal details."""
        proposal = f.create_proposal(self.job, self.candidate_1, self.recruiter)
        proposal.last_activity_at = None  # queryset annotation emulation

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        proposal_data = s.RetrieveProposalSerializer(
            proposal, context={'request': response.wsgi_request}
        ).data
        proposal_data['candidate']['note'] = ''
        response_data = response.json()
        response_data.pop('quickActions')
        self.assertDictEqual(response_data, camelize(proposal_data))

    def get_proposal_status_by_group(self, org, group):
        return (
            m.OrganizationProposalStatus.objects.filter(
                org_filter(org), status__group=group
            )
            .first()
            .status
        )

    def create_status_history(self, changed_by, proposal, status, changed_at):
        instance = m.ProposalStatusHistory.objects.create(
            proposal=proposal, status=status, changed_by=changed_by,
        )
        instance.changed_at = changed_at
        instance.save()
        return instance

    def setup_hired_at_test(self):
        candidate = f.create_candidate(self.agency)
        hired_status = self.get_proposal_status_by_group(
            self.agency, m.ProposalStatusGroup.PENDING_START.key
        )
        interviewing_status = self.get_proposal_status_by_group(
            self.agency, m.ProposalStatusGroup.INTERVIEWING.key
        )

        proposal = f.create_proposal(
            self.job, candidate, self.recruiter, status=hired_status
        )
        candidate.save()

        hired_at = datetime(2019, 2, 19, 14, 35, tzinfo=utc)

        self.create_status_history(self.recruiter, proposal, hired_status, hired_at)
        self.create_status_history(
            self.recruiter,
            proposal,
            interviewing_status,
            datetime(2019, 3, 19, 12, 31, tzinfo=utc),
        )
        self.create_status_history(
            self.recruiter,
            proposal,
            hired_status,
            datetime(2019, 1, 1, 12, 13, tzinfo=utc),
        )

        return hired_at, proposal

    def test_get_proposal_hired_at(self):
        hired_at, proposal = self.setup_hired_at_test()

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response_data = self.client.get(f'{url}?extra_fields=hired_at').json()

        self.assertIn('hiredAt', response_data)
        self.assertEqual(hired_at, parse_datetime(response_data['hiredAt']))

    def test_get_proposal_not_hired(self):
        hired_at, proposal = self.setup_hired_at_test()

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response_data = self.client.get(url).json()

        self.assertNotIn('hiredAt', response_data)

    def check_can_see_placement(
        self,
        user,
        created_by,
        can_see_placement,
        can_edit_placement,
        status=DRAFT,
        submitted_by=None,
    ):
        client = f.create_client()
        agency = created_by.org
        f.create_contract(agency, client)

        self.client.force_login(user)

        job = f.create_job(client, client)
        job.assign_agency(agency)
        job.assign_member(user)
        candidate = f.create_candidate(agency, created_by=created_by)

        proposal = f.create_proposal(job, candidate, created_by)

        f.create_fee(proposal, created_by, submitted_by=submitted_by, status=status)

        f.create_fee(f.create_proposal_with_candidate(job, created_by), user)  # noise

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response_data = self.client.get(
            f'{url}?extra_fields=can_see_placement,can_edit_placement'
        ).json()

        self.assertEqual(can_see_placement, response_data.get('canSeePlacement', False))
        self.assertEqual(
            can_edit_placement, response_data.get('canEditPlacement', False)
        )

    def test_get_proposal_can_see_placement_agency_admin(self):
        agency = f.create_agency()
        user = f.create_agency_administrator(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, other_user, True, True)

    def test_get_proposal_can_see_placement_agency_manager(self):
        agency = f.create_agency()
        user = f.create_agency_manager(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, other_user, True, True)

    def test_get_proposal_can_see_placement_recruiter(self):
        agency = f.create_agency()
        user = f.create_recruiter(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, other_user, False, False)

    def test_get_proposal_can_see_placement_agency_admin_pending_submitter(self):
        agency = f.create_agency()
        user = f.create_agency_administrator(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, other_user, True, True, PENDING, user)

    def test_get_proposal_can_see_placement_agency_manager_pending_submitter(self):
        agency = f.create_agency()
        user = f.create_agency_manager(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, other_user, True, True, PENDING, user)

    def test_get_proposal_can_see_placement_recruiter_pending_submitter(self):
        agency = f.create_agency()
        user = f.create_recruiter(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, other_user, True, False, PENDING, user)

    def test_get_proposal_can_see_placement_agency_admin_pending_creator(self):
        agency = f.create_agency()
        user = f.create_agency_administrator(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, user, True, True, PENDING, other_user)

    def test_get_proposal_can_see_placement_agency_manager_pending_creator(self):
        agency = f.create_agency()
        user = f.create_agency_manager(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, user, True, True, PENDING, other_user)

    def test_get_proposal_can_see_placement_recruiter_pending_creator(self):
        agency = f.create_agency()
        user = f.create_recruiter(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, user, True, False, PENDING, other_user)

    def test_get_proposal_can_see_placement_agency_admin_approved_submitter(self):
        agency = f.create_agency()
        user = f.create_agency_administrator(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, other_user, True, False, APPROVED, user)

    def test_get_proposal_can_see_placement_agency_manager_approved_submitter(self):
        agency = f.create_agency()
        user = f.create_agency_manager(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, other_user, True, False, APPROVED, user)

    def test_get_proposal_can_see_placement_recruiter_approved_submitter(self):
        agency = f.create_agency()
        user = f.create_recruiter(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, other_user, True, False, APPROVED, user)

    def test_get_proposal_can_see_placement_agency_admin_approved_creator(self):
        agency = f.create_agency()
        user = f.create_agency_administrator(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, user, True, False, APPROVED, other_user)

    def test_get_proposal_can_see_placement_agency_manager_approved_creator(self):
        agency = f.create_agency()
        user = f.create_agency_manager(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, user, True, False, APPROVED, other_user)

    def test_get_proposal_can_see_placement_recruiter_approved_creator(self):
        agency = f.create_agency()
        user = f.create_recruiter(agency)
        other_user = f.create_recruiter(agency)

        self.check_can_see_placement(user, user, True, False, APPROVED, other_user)

    def test_get_proposal_can_see_placement_agency_admin_creator(self):
        agency = f.create_agency()
        user = f.create_agency_administrator(agency)

        self.check_can_see_placement(user, user, True, True)

    def test_get_proposal_can_see_placement_agency_manager_creator(self):
        agency = f.create_agency()
        user = f.create_agency_manager(agency)

        self.check_can_see_placement(user, user, True, True)

    def test_get_proposal_can_see_placement_recruiter_creator(self):
        agency = f.create_agency()
        user = f.create_recruiter(agency)

        self.check_can_see_placement(user, user, True, True)

    def check_can_create_placement(self, user, expected):
        client = f.create_client()
        agency = user.org
        f.create_contract(agency, client)
        other_user = f.create_agency_administrator(agency)

        job = f.create_job(client, client=client)
        job.assign_member(user)
        job.assign_agency(agency)

        def create_proposal(
            job,
            created_by,
            status_stage=m.ProposalStatusStage.HIRED.key,
            group=m.ProposalStatusGroup.PENDING_START.key,
            **kwargs,
        ):
            proposal = f.create_proposal_with_candidate(job, created_by, **kwargs)

            proposal.set_status_by_group(status_stage, created_by, group=group)
            proposal.save()

            return proposal

        proposals = {
            'if_created_by': create_proposal(job, user),
            'if_not_created_by': create_proposal(job, other_user),
            'if_not_hired': create_proposal(
                job,
                user,
                m.ProposalStatusStage.SUBMISSIONS.key,
                group=m.ProposalStatusGroup.SUBMITTED_TO_HIRING_MANAGER.key,
            ),
        }
        proposal_keys = {proposal.id: key for key, proposal in proposals.items()}

        url = reverse('proposal-list')

        self.client.force_login(user)
        response_data = self.client.get(
            f'{url}?extra_fields=can_create_placement'
        ).json()

        result = dict()

        for proposal_data in response_data['results']:
            proposal_id = proposal_data['id']
            self.assertIn(proposal_id, proposal_keys)

            result[proposal_keys[proposal_id]] = proposal_data['canCreatePlacement']

        self.assertCountEqual(expected.items(), result.items())

    def test_get_proposals_can_create_placement_agency_admin(self):
        agency = f.create_agency()
        user = f.create_agency_administrator(agency)

        self.check_can_create_placement(
            user,
            {'if_created_by': True, 'if_not_created_by': True, 'if_not_hired': False,},
        )

    def test_get_proposals_can_create_placement_agency_manager(self):
        agency = f.create_agency()
        user = f.create_agency_manager(agency)

        self.check_can_create_placement(
            user,
            {'if_created_by': True, 'if_not_created_by': True, 'if_not_hired': False,},
        )

    def test_get_proposals_can_create_placement_recruiter(self):
        agency = f.create_agency()
        user = f.create_recruiter(agency)

        self.check_can_create_placement(
            user,
            {'if_created_by': True, 'if_not_created_by': False, 'if_not_hired': False,},
        )

    def test_get_proposal_job_created_by_name(self):
        job_owner = self.job.owner
        job_owner.first_name = 'Hank'
        job_owner.last_name = 'Hill'
        job_owner.save()

        proposal = f.create_proposal(self.job, self.candidate_1, self.recruiter)

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response_data = self.client.get(
            f'{url}?extra_fields=job_created_by_name'
        ).json()

        self.assertIn('jobCreatedByName', response_data)
        self.assertEqual('Hank Hill', response_data['jobCreatedByName'])

    def test_get_proposal_candidate_files(self):
        files_visible_to_client = {
            'client': ('client_shared_file',),
            'agency': ('agency_shared_file',),
        }

        files_visible_to_agency = {
            'agency': ('agency_shared_file',),
        }

        checks = {
            'client': {
                'client_administrator': files_visible_to_client,
                'client_internal_recruiter': files_visible_to_client,
            },
            'agency': {
                'agency_administrator': files_visible_to_agency,
                'agency_manager': files_visible_to_agency,
            },
        }

        users, org = f.get_org_users_map({'client': 'client', 'agency': 'agency'})

        f.create_contract(org['agency'], org['client'])

        job = f.create_job(org['client'])
        job.assign_manager(users['client']['client_administrator'])
        job.assign_agency(org['agency'])

        candidates = {
            'client': f.create_candidate(organization=org['client'],),
            'agency': f.create_candidate(organization=org['agency'],),
        }

        proposal_created_by = {
            'client': 'client_administrator',
            'agency': 'agency_administrator',
        }

        proposals = {
            org_name: f.create_proposal(
                job=job,
                candidate=candidates[org_name],
                created_by=users[org_name][user_type],
            )
            for org_name, user_type in proposal_created_by.items()
        }

        create_files = {
            'client_private_file': {'org': 'client', 'is_shared': False,},
            'client_shared_file': {'org': 'client', 'is_shared': True,},
            'agency_private_file': {'org': 'agency', 'is_shared': False,},
            'agency_shared_file': {'org': 'agency', 'is_shared': True,},
        }

        files = {
            key: f.create_candidate_file(
                prefix=key,
                candidate=candidates[value['org']],
                org=org[value['org']],
                is_shared=value['is_shared'],
            )
            for key, value in create_files.items()
        }
        try:
            for org_type in checks:
                for user_type in checks[org_type]:
                    for proposal_type in checks[org_type][user_type]:
                        self.client.force_login(users[org_type][user_type])

                        msg = f'Organization: {org_type}, User: {user_type}, Proposal: {proposal_type}'

                        response = self.client.get(
                            reverse(
                                'proposal-detail',
                                kwargs={'pk': proposals[proposal_type].pk},
                            )
                        )

                        self.assertEqual(response.status_code, 200, msg)

                        data = response.json()
                        self.assertTrue('candidate' in data, msg)
                        self.assertTrue('files' in data['candidate'], msg)

                        files_not_found = set()
                        for case in checks[org_type][user_type][proposal_type]:
                            if is_file_id_not_found(data, files, case):
                                files_not_found.add(case)

                        # compare sets, so it would be easy to see what files are missing
                        self.assertSetEqual(files_not_found, set(), msg)

                        self.client.logout()
        finally:
            self.default_login()
            for file in files.values():
                file.file.delete()

    def test_get_proposal_without_proposal(self):
        """Should return 404 status code if not existing pk requested."""
        self.assert_response.not_found('get', 'proposal-detail', f.NOT_EXISTING_PK)

    def test_create_proposal_for_open_job(self):
        """Should create proposal, if job is open."""
        self.client.force_login(self.agency_admin)

        candidate = f.create_candidate(self.agency)

        self.assert_response.created(
            'post',
            'proposal-list',
            data={'job': self.job.id, 'candidate': candidate.id},
        )

    def test_create_proposal_for_agency_open_job(self):
        """Should create proposal, if job is open."""
        self.client.force_login(self.agency_admin)
        job = f.create_job(self.agency_admin.profile.org, owner=self.agency_admin)

        candidate = f.create_candidate(self.agency)

        response = self.assert_response.created(
            'post', 'proposal-list', data={'job': job.id, 'candidate': candidate.id}
        )

        self.assertTrue(m.Proposal.objects.filter(id=response.json()['id']).exists())

    def test_create_proposal_for_non_open_job(self):
        """Should not create proposal, if job is not open."""
        self.job.status = m.JobStatus.ON_HOLD.key
        self.job.save()

        self.client.force_login(self.agency_admin)

        candidate = f.create_candidate(self.agency)

        self.assert_response.bad_request(
            'post',
            'proposal-list',
            data={'job': self.job.id, 'candidate': candidate.id},
        )

    def test_move_to_job(self):
        """Should move proposal to other job."""
        proposal = f.create_proposal(self.job, self.candidate_1, self.recruiter)

        another_job = f.create_job(self.client_obj)

        data = {'job': another_job.id}
        url = reverse('proposal-move-to-job', kwargs={'pk': proposal.id})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 200)

        proposal.refresh_from_db()
        self.assertEqual(proposal.job, another_job)
        self.assertEqual(proposal.moved_from_job, self.job)
        self.assertEqual(proposal.moved_by, self.client_admin)

    def test_move_to_job_already_proposed(self):
        """Should not move proposal to other job if already proposed."""
        proposal = f.create_proposal(self.job, self.candidate_1, self.recruiter)
        another_job = f.create_job(self.client_obj)
        f.create_proposal(another_job, self.candidate_1, self.recruiter)

        data = {'job': another_job.id}
        url = reverse('proposal-move-to-job', kwargs={'pk': proposal.id})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 400)

    def test_move_to_job_same_job(self):
        """Should not move proposal to other job if same job."""
        proposal = f.create_proposal(self.job, self.candidate_1, self.recruiter)

        data = {'job': self.job.id}
        url = reverse('proposal-move-to-job', kwargs={'pk': proposal.id})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 400)

    def test_move_to_job_other_client(self):
        """Should not move proposal to other job if other client's job."""
        self.client.force_login(self.agency_admin)

        proposal = f.create_proposal(self.job, self.candidate_1, self.agency_admin)

        another_client = f.create_client()
        f.create_contract(self.agency, another_client)
        another_job = f.create_job(another_client)
        another_job.assign_agency(self.agency)

        data = {'job': another_job.id}
        url = reverse('proposal-move-to-job', kwargs={'pk': proposal.id})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, 400)

    def test_get_proposals_with_superuser(self):
        """Should return 403 once Admin request proposals"""
        admin = f.create_admin()
        self.client.force_login(admin)

        url = reverse('proposal-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {'detail': 'You do not have permission to perform this action.'},
        )

    def test_get_alien_proposal_by_client(self):
        """Client isn't available to see Longlisted candidate which was proposed
        by an Agency"""
        proposal = f.create_proposal(
            self.job, self.candidate_1, self.recruiter, stage='longlist'
        )

        self.client.force_login(self.client_admin)
        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not found."})

    def test_get_proposals_by_client(self):
        """Client see all their own proposed candidates (Longlisted and Shortlisted)
        and Shortlisted candidates which proposed by agency"""
        client_candidate_1 = f.create_candidate(self.client_obj)
        client_candidate_2 = f.create_candidate(self.client_obj)

        # Longlisted candidate proposed by Client
        proposal_c_l = f.create_proposal(
            self.job, client_candidate_1, self.client_admin, stage='longlist'
        )
        # Shortlisted candidate proposed by Client
        proposal_c_s = f.create_proposal(
            self.job, client_candidate_2, self.client_admin,
        )
        # Longlisted candidate proposed by Agency
        proposal_a_l = f.create_proposal(
            self.job, self.candidate_1, self.recruiter, stage='longlist'
        )
        # Shortlisted candidate proposed by Agency (hidden from client)
        proposal_a_s = f.create_proposal(self.job, self.candidate_2, self.recruiter)

        self.client.force_login(self.client_admin)

        url = reverse('proposal-list')
        response = self.client.get(url)

        legal_proposals = [proposal_c_l.pk, proposal_c_s.pk, proposal_a_s.pk].sort()
        coming_proposals = list(
            map(lambda x: x['id'], response.json()['results'])
        ).sort()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(legal_proposals, coming_proposals)

    def test_get_proposals_by_agency(self):
        """Agency see all their proposed candidates (Longlisted and Shortlisred)"""
        client_candidate_1 = f.create_candidate(self.client_obj)
        client_candidate_2 = f.create_candidate(self.client_obj)

        # Longlisted candidate proposed by Client
        proposal_c_l = f.create_proposal(
            self.job, client_candidate_1, self.client_admin, stage='longlist'
        )
        # Shortlisted candidate proposed by Client
        proposal_c_s = f.create_proposal(
            self.job, client_candidate_2, self.client_admin,
        )
        # Longlisted candidate proposed by Agency
        proposal_a_l = f.create_proposal(
            self.job, self.candidate_1, self.agency_admin, stage='longlist'
        )
        # Shortlisted candidate proposed by Agency (hidden from client)
        proposal_a_s = f.create_proposal(self.job, self.candidate_2, self.agency_admin)

        self.client.force_login(self.agency_admin)

        response = self.assert_response.ok('get', 'proposal-list')

        expected_proposal_ids = sorted((proposal_a_l.pk, proposal_a_s.pk))
        response_proposal_ids = sorted(
            proposal['id'] for proposal in response.json()['results']
        )

        self.assertEqual(expected_proposal_ids, response_proposal_ids)

    def test_update_suitability(self):
        proposal = f.create_proposal(
            self.job, self.client_candidate, self.client_admin, stage='longlist'
        )
        self.client.force_login(self.client_admin)

        url = reverse('proposal-detail', kwargs={'pk': proposal.pk})
        data = {'suitability': 4}
        response = self.client.patch(url, data, format='json')

        proposal.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(proposal.suitability, 4)

    def test_update_suitability_not_proper_value(self):
        """Should not allow to set value less than MIN and greater than MAX
        MIN: Proposal.MIN_SUITABILITY, MAX: Proposal.MAX_SUITABILITY"""
        proposal = f.create_proposal(
            self.job, self.client_candidate, self.client_admin, stage='longlist'
        )
        self.client.force_login(self.client_admin)

        url = reverse('proposal-detail', kwargs={"pk": proposal.pk})
        data = {"suitability": m.Proposal.MAX_SUITABILITY + 1}
        response = self.client.patch(url, data, format='json')

        proposal.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(proposal.suitability, None)

    def test_update_suitability_not_owned_proposal(self):
        """Should not set suitability for proposals of another organization"""
        proposal = f.create_proposal(
            self.job, self.candidate_1, self.recruiter, stage='longlist'
        )
        self.client.force_login(self.client_admin)

        url = reverse('proposal-detail', kwargs={"pk": proposal.pk})
        data = {"suitability": 4}
        response = self.client.patch(url, data, format='json')

        proposal.refresh_from_db()

        self.assertEqual(proposal.suitability, None)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not found."})

    def test_update_proposal_by_agency(self):
        """Agencies may update their longlist proposals"""
        proposal = f.create_proposal(
            self.job,
            self.candidate_1,
            self.agency_admin,
            status=m.ProposalStatus.longlist.filter(
                stage=m.ProposalStatusStage.ASSOCIATED.key
            ).first(),
        )
        self.client.force_login(self.agency_admin)
        url = reverse('proposal-detail', kwargs={"pk": proposal.pk})

        new_status = m.ProposalStatus.longlist.filter(
            group=m.ProposalStatusGroup.SUITABLE.key
        ).first()
        data = {'status': new_status.pk}

        response = self.client.patch(url, data, format='json')

        proposal.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(proposal.status, new_status)

    def test_update_not_own_candidate_by_agency(self):
        """Agency should not be able to update proposals if candidate belongs to other org"""
        proposal = f.create_proposal(
            self.job,
            f.create_candidate(self.client_obj),
            self.client_admin,
            status=m.ProposalStatus.longlist.filter(
                stage=m.ProposalStatusStage.ASSOCIATED.key
            ).first(),
        )
        self.client.force_login(self.recruiter)

        new_status = m.ProposalStatus.longlist.filter(
            group=m.ProposalStatusGroup.SUITABLE.key
        ).first()
        data = {'status': new_status.pk}
        self.assert_response.not_found('patch', 'proposal-detail', proposal.pk, data)

    def test_update_proposal_by_agency_not_appropriate_status(self):
        """Only longlist statuses supported."""
        proposal = f.create_proposal(
            self.job, self.candidate_1, self.agency_admin, stage='longlist',
        )
        self.client.force_login(self.agency_admin)
        url = reverse('proposal-detail', kwargs={"pk": proposal.pk})

        new_status = m.ProposalStatus.shortlist.filter(
            stage=m.ProposalStatusStage.SUBMISSIONS.key
        ).first()
        data = {'status': new_status.pk}

        response = self.client.patch(url, data, format='json')

        proposal.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {'status': [f'Invalid pk "{new_status.pk}" - object does not exist.']},
        )
        self.assertNotEqual(proposal.status, new_status)

    def check_delete_proposal(
        self, user, proposal, expected_response_status=204, still_exist=False
    ):
        self.client.force_login(user)
        url = reverse('proposal-detail', kwargs={"pk": proposal.pk})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, expected_response_status)
        self.assertEqual(m.Proposal.objects.exists(), still_exist)

    def test_delete_longlist(self):
        user = self.client_admin
        org = user.profile.org

        self.check_delete_proposal(
            user=user,
            proposal=f.create_proposal(
                created_by=user,
                job=f.create_job(org),
                candidate=f.create_candidate(org),
                stage='longlist',
            ),
            expected_response_status=403,
            still_exist=True,
        )

    def test_delete_shortlist(self):
        user = self.client_admin
        org = user.profile.org

        self.check_delete_proposal(
            user=user,
            proposal=f.create_proposal(
                created_by=user,
                job=f.create_job(org),
                candidate=f.create_candidate(org),
                stage='shortlist',
            ),
            expected_response_status=403,
            still_exist=True,
        )

    def test_candidate_hired_and_other_proposals_declined(self):
        """If a candidate became hired he should quit from other jobs"""
        job_1 = f.create_job(self.client_obj)
        job_2 = f.create_job(self.client_obj)
        job_3 = f.create_job(self.client_obj)

        proposal_1 = f.create_proposal(job_1, self.candidate_1, self.client_admin)
        proposal_2 = f.create_proposal(job_2, self.candidate_1, self.client_admin)
        proposal_3 = f.create_proposal(job_3, self.candidate_1, self.client_admin)

        proposal_1.status = m.ProposalStatus.objects.filter(
            deal_stage=m.ProposalDealStages.OFFER.key
        ).first()
        proposal_1.save()
        proposal_2.status = m.ProposalStatus.objects.filter(
            deal_stage=m.ProposalDealStages.INTERMEDIATE_ROUND.key
        ).first()
        proposal_2.save()

        offer_accepted_status = m.ProposalStatus.objects.filter(
            group=m.ProposalStatusGroup.PENDING_START.key
        ).first()

        self.client.force_login(self.client_admin)
        url = reverse('proposal-detail', kwargs={"pk": proposal_3.pk})
        self.client.patch(url, {'status': offer_accepted_status.pk}, format='json')

        proposal_1.refresh_from_db()
        proposal_2.refresh_from_db()

        self.assertFalse(proposal_1.is_rejected)
        self.assertFalse(proposal_2.is_rejected)
        self.assertFalse(proposal_3.is_rejected)


class ProposalFieldAccessTests(APITestCase):

    ADVANCED_FIELDS = {
        'email',
        'secondaryEmail',
        'phone',
        'secondaryPhone',
        'address',
        'taxEqualization',
        'salaryCurrency',
        'salary',
        'currentSalaryVariable',
        'currentSalaryCurrency',
        'currentSalary',
        'currentSalaryBreakdown',
        'totalAnnualSalary',
        'potentialLocations',
        'otherDesiredBenefits',
        'otherDesiredBenefitsOthersDetail',
        'expectationsDetails',
        'noticePeriod',
        'jobChangeUrgency',
        'source',
        'sourceDetails',
        'platform',
        'platformOtherDetails',
        'owner',
        'note',
    }

    def setUp(self):
        client = ClientFactory.create()
        user = UserFactory.create()
        candidate = ClientCandidateFactory.create(client=client)
        job = ClientJobFactory.create(client=client)

        self.proposal = ClientProposalFactory.create(job=job, candidate=candidate)
        self.user = user
        self.client_org = client
        self.job = job

        self.client.force_login(user)

    @staticmethod
    def get_url(pk=None):
        if not pk:
            return reverse('proposal-list')
        return reverse('proposal-detail', kwargs={'pk': pk})

    def send_get_request(self, pk=None):
        return self.client.get(self.get_url(pk), format='json').json()

    def assert_has_advanced_fields(self, data, has_fields=True):
        expected_set = set() if has_fields else self.ADVANCED_FIELDS
        self.assertSetEqual(
            self.ADVANCED_FIELDS - data['candidate'].keys(), expected_set
        )

    def test_retrieve_recruiter_advanced_fields(self):
        self.client_org.assign_internal_recruiter(self.user)

        data = self.send_get_request(self.proposal.pk)

        self.assert_has_advanced_fields(data)

    def test_list_recruiter_advanced_fields(self):
        self.client_org.assign_internal_recruiter(self.user)

        data = self.send_get_request()

        self.assert_has_advanced_fields(data['results'][0])

    def test_retrieve_client_admin_advanced_fields(self):
        self.client_org.assign_administrator(self.user)

        data = self.send_get_request(self.proposal.pk)

        self.assert_has_advanced_fields(data)

    def test_list_client_admin_advanced_fields(self):
        self.client_org.assign_administrator(self.user)

        data = self.send_get_request()

        self.assert_has_advanced_fields(data['results'][0])

    def setup_standard_user(self):
        self.client_org.assign_standard_user(self.user)
        self.job.assign_manager(self.user)

    def test_retrieve_standard_user_advanced_fields(self):
        self.setup_standard_user()

        data = self.send_get_request(self.proposal.pk)

        self.assert_has_advanced_fields(data, False)

    def test_list_standard_user_advanced_fields(self):
        self.setup_standard_user()

        data = self.send_get_request()

        self.assert_has_advanced_fields(data['results'][0], False)
