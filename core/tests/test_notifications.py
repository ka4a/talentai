from unittest.mock import patch, call, MagicMock
from unittest import skip

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import datetime, utc

from core import fixtures as f
from core import models as m
from core.constants import NotificationLinkText
from core.factories import ClientFactory, UserFactory
from core.notifications import (
    notify_candidate_proposed_for_job,
    notify_client_assigned_agency,
    notify_client_changed_proposal_status,
    notify_client_created_contract,
    notify_contract_initiated,
    notify_client_updated_job,
    notify_proposal_moved,
    notify_client_admin_assigned_manager,
    notify_contract_signed_by_one_party,
    notify_removed_job_access,
    notify_contract_invitation,
    notify_proposal_interview_confirmed,
    notify_proposal_interview_rejected,
    notify_proposal_interview_canceled,
    notify_fee_status_change,
    notify_fee_pending,
    get_interview_notification_email_context,
    notify_agency_assigned_job_member,
)
from core.utils import compare_model_dicts, poly_relation_filter


def create_contract(check_disabled=False, status=m.ContractStatus.PENDING.key):
    client = f.create_client()

    # agency_admin = f.create_user(email_client_created_contract=not check_disabled)
    agency_admin = f.create_user()
    agency = f.create_agency(primary_contact=agency_admin)
    agency.assign_agency_administrator(agency_admin)

    return f.create_contract(agency, client, status)


def unwrap_contract(contract):
    return (
        contract.client,
        contract.agency,
        contract.client.primary_contact,
        contract.agency.primary_contact,
    )


def setup_interview_test():
    client = ClientFactory.create()

    admin = client.primary_contact
    client.assign_administrator(admin)

    recruiter = UserFactory.create()
    client.assign_internal_recruiter(recruiter)

    interview = MagicMock(
        start_at=datetime(2100, 1, 1, 13, 0, tzinfo=utc),
        end_at=datetime(2100, 1, 1, 13, 30, tzinfo=utc),
        creator_timezone='America/New_York',
        created_by=client.primary_contact,
        proposal=f.create_proposal_with_candidate(
            job=f.create_job(client), created_by=recruiter
        ),
        scheduling_type=m.ProposalInterviewSchedule.SchedulingType.INTERVIEW_PROPOSAL,
        ics_attachment=('filename', 'content', 'type'),
        ics_canceled_attachment=('cancel_attachment',),
        **{'format.return_value': 'fake timeframe'},
    )

    interview.format.return_value = 'date placeholder'

    return interview


class MockCallsMixin:
    def assert_has_only_calls(self, mock, calls):
        self.assertEqual(len(calls), mock.call_count)
        mock.assert_has_calls(calls, any_order=True)


class NotificationsTestCase(TestCase, MockCallsMixin):
    def setUp(self):
        self.contract = create_contract()
        self.contract_no_check = create_contract(check_disabled=True)
        self.contract_rejected = create_contract(status=m.ContractStatus.REJECTED.key)
        self.contract_invitation = create_contract(
            status=m.ContractStatus.AGENCY_INVITED.key
        )

    @skip('TODO(ZOO-963)')
    @patch('core.models.Notification.send')
    def check_notify_client_created_contract(self, send_mock, *args, contract):
        client, agency, client_admin, agency_admin = unwrap_contract(contract)

        notify_client_created_contract(sender=client_admin, contract=contract)

        send_mock.assert_called_once_with(
            agency_admin,
            m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
            sender=client_admin,
            actor=client,
            # send_via_email=agency_admin.email_client_created_contract,
            action_object=agency,
            reply_to=client_admin.email,
            link=reverse('invitations_page'),
        )

    @skip('TODO(ZOO-963)')
    @patch('core.models.Notification.send')
    def check_notify_contract_initiated(self, send_mock, *args, contract):
        client, agency, client_admin, agency_admin = unwrap_contract(contract)

        notify_contract_initiated(sender=None, contract=contract)

        send_mock.assert_has_calls(
            [
                call(
                    agency_admin,
                    m.NotificationTypeEnum.CONTRACT_INITIATED_AGENCY,
                    sender=None,
                    actor=client,
                    action_object=agency,
                    # send_via_email=agency_admin.email_client_created_contract,
                ),
                call(
                    client_admin,
                    m.NotificationTypeEnum.CONTRACT_INITIATED_CLIENT,
                    sender=None,
                    actor=agency,
                    action_object=client,
                    # send_via_email=client_admin.email_client_created_contract,
                ),
            ]
        )

    @skip('TODO(ZOO-963)')
    @patch('core.models.Notification.send')
    def check_notify_signed_contract(
        self, send_mock, *args, contract, actor, action_object, is_agency_signed
    ):

        notify_contract_signed_by_one_party(
            sender=None, contract=contract, to_agency=not is_agency_signed,
        )

        send_mock.assert_called_once_with(
            action_object.primary_contact,
            m.NotificationTypeEnum.CONTRACT_SIGNED_BY_ONE_PARTY,
            sender=None,
            actor=actor,
            # send_via_email=action_object.primary_contact.email_client_created_contract,
            action_object=action_object,
            link=reverse('invitations_page'),
        )

    @skip('TODO(ZOO-963)')
    @patch('core.models.Notification.send')
    def check_notify_invitation(self, send_mock, *args, contract, is_accepted):
        client, agency, client_admin, agency_admin = unwrap_contract(contract)

        notify_contract_invitation(
            sender=None, contract=contract,
        )

        send_mock.assert_called_once_with(
            client_admin,
            m.NotificationTypeEnum.CONTRACT_INVITATION_ACCEPTED
            if is_accepted
            else m.NotificationTypeEnum.CONTRACT_INVITATION_DECLINED,
            sender=None,
            actor=agency,
            # send_via_email=client_admin.email_client_created_contract,
            action_object=client,
        )

    @skip('TODO(ZOO-963)')
    @patch('core.models.Notification.send')
    def check_notify_remove_job_access(
        self, send_mock, *args, contract, no_agreement=False
    ):
        client, agency, client_admin, agency_admin = unwrap_contract(contract)

        notify_removed_job_access(
            sender=None, contract=contract,
        )

        send_mock.assert_called_once_with(
            client_admin,
            m.NotificationTypeEnum.CONTRACT_JOB_ACCESS_REVOKED_NO_AGREEMENT
            if no_agreement
            else m.NotificationTypeEnum.CONTRACT_JOB_ACCESS_REVOKED_INVITE_IGNORED,
            sender=None,
            actor=agency,
            # send_via_email=client_admin.email_client_created_contract,
            action_object=client,
        )

    def test_notify_agency_client_signed_contract(self):
        contract = self.contract
        self.check_notify_signed_contract(
            contract=contract,
            actor=contract.client,
            action_object=contract.agency,
            is_agency_signed=False,
        )

    def test_notify_client_agency_signed_contract(self):
        contract = self.contract
        self.check_notify_signed_contract(
            contract=contract,
            actor=contract.agency,
            action_object=contract.client,
            is_agency_signed=True,
        )

    def test_notify_invitation_accepted(self):
        self.check_notify_invitation(contract=self.contract, is_accepted=True)

    def test_notify_invitation_rejected(self):
        self.check_notify_invitation(contract=self.contract_rejected, is_accepted=False)

    def test_notify_client_created_contract(self):
        self.check_notify_client_created_contract(contract=self.contract)

    def test_notify_client_created_contract_disabled(self):
        """Should not send notification, if disabled by user."""
        self.check_notify_client_created_contract(contract=self.contract_no_check)

    def test_notify_contract_initiated(self):
        self.check_notify_contract_initiated(contract=self.contract)

    def test_notify_contract_initiated_disabled(self):
        """Should not send notification, if disabled by user."""
        self.check_notify_contract_initiated(contract=self.contract_no_check)

    def test_remove_job_access_no_agreement(self):
        self.check_notify_remove_job_access(contract=self.contract, no_agreement=True)

    def test_remove_job_access_ignored(self):
        self.check_notify_remove_job_access(contract=self.contract_invitation)

    @skip('TODO(ZOO-963)')
    @patch('core.models.Notification.send')
    def check_notify_client_updated_job(self, send_mock, check_disabled=False):
        client_admin = f.create_user()
        client = f.create_client(primary_contact=client_admin)
        client.assign_administrator(client_admin)

        agency = f.create_agency()
        f.create_contract(agency, client)

        recruiter = f.create_recruiter(agency)
        if check_disabled:
            recruiter.email_client_updated_job = False
            recruiter.save()

        job = f.create_job(client)
        job.assign_agency(agency)

        notify_client_updated_job(
            sender=client_admin,
            job=job,
            diff=compare_model_dicts(
                {'title': 'Old'}, {'title': 'New'}, compare=['title']
            ),
        )

        notified_users = [recruiter, agency.primary_contact]

        self.assertEqual(send_mock.call_count, len(notified_users))

        for user in notified_users:
            send_mock.assert_any_call(
                user,
                m.NotificationTypeEnum.CLIENT_UPDATED_JOB,
                sender=client_admin,
                actor=client,
                target=job,
                # send_via_email=user.email_client_updated_job,
            )

    def test_notify_client_updated_job(self):
        self.check_notify_client_updated_job()

    def test_notify_client_updated_job_disabled(self):
        """Should not send notification, if disabled by user."""
        self.check_notify_client_updated_job(check_disabled=True)

    @skip('TODO(ZOO-963)')
    @patch('core.models.Notification.send')
    def test_notify_client_updated_job_no_diff(self, send_mock):
        """Should not send notification, if no fields were updated."""
        client = f.create_client()
        agency = f.create_agency()
        f.create_contract(agency, client)

        client_admin = f.create_client_administrator(client)
        f.create_recruiter(agency)

        job = f.create_job(client)
        job.assign_agency(agency)

        notify_client_updated_job(sender=client_admin, job=job, diff={})

        send_mock.assert_not_called()

    @skip('TODO(ZOO-963)')
    @patch('core.models.Notification.send')
    def check_notify_client_assigned_agency(
        self, send_mock, job_published=True, check_disabled=False
    ):
        """Should send notification to Agency.
        Only Agency Administrator and Agency Manager should receive them"""

        client_admin = f.create_user()
        client = f.create_client(primary_contact=client_admin)
        client.assign_administrator(client_admin)

        agency = f.create_agency()
        f.create_contract(agency, client)

        recruiter = f.create_recruiter(agency)  # shouldn't receive
        if check_disabled:
            # recruiter.email_client_assigned_agency_for_job = False
            recruiter.save()

        job = f.create_job(client)
        job.published = job_published
        job.save()
        job.assign_agency(agency)

        notify_client_assigned_agency(
            sender=client_admin,
            job=job,
            diff=compare_model_dicts(
                {'agencies': []}, {'agencies': [agency.id]}, compare_as_set=['agencies']
            ),
        )

        if job_published:
            self.assert_has_only_calls(
                send_mock,
                [
                    call(
                        agency.primary_contact,
                        m.NotificationTypeEnum.CLIENT_ASSIGNED_AGENCY_FOR_JOB,
                        sender=client_admin,
                        actor=client,
                        target=job,
                        # send_via_email=agency.primary_contact.email_client_assigned_agency_for_job,
                    ),
                ],
            )
        else:
            send_mock.assert_not_called()

    @skip('TODO(ZOO-963)')
    @patch('core.models.Notification.send')
    def check_notify_agency_assigned_member(
        self, send_mock, job_published=True, check_disabled=False
    ):
        """Should send a Notification to Recruiter."""
        client = f.create_client()
        agency = f.create_agency()
        agency_admin = f.create_agency_administrator(agency)
        f.create_contract(agency, client)

        recruiter = f.create_recruiter(agency)
        if check_disabled:
            # recruiter.email_agency_assigned_member_for_job = False
            recruiter.save()

        job = f.create_job(client)
        job.published = job_published
        job.save()
        job.assign_member(recruiter)

        notify_agency_assigned_job_member(
            sender=agency_admin, job=job, assignee_id=recruiter.id
        )

        if job_published:
            send_mock.assert_called_once_with(
                recruiter,
                m.NotificationTypeEnum.AGENCY_ASSIGNED_MEMBER_FOR_JOB,
                sender=agency_admin,
                actor=agency_admin,
                target=job,
                # send_via_email=recruiter.email_agency_assigned_member_for_job,
            )
        else:
            send_mock.assert_not_called()

    def test_notify_client_assigned_agency(self):
        self.check_notify_client_assigned_agency()
        self.check_notify_agency_assigned_member()

    def test_notify_client_assigned_agency_job_not_published(self):
        """Should not notify about unpublished job."""
        self.check_notify_client_assigned_agency(job_published=False)
        self.check_notify_agency_assigned_member(job_published=False)

    def test_notify_client_assigned_agency_disabled(self):
        """Should not send notification, if disabled by user."""
        self.check_notify_client_assigned_agency(check_disabled=True)
        self.check_notify_agency_assigned_member(check_disabled=True)

    @skip('TODO(ZOO-963)')
    @patch('core.models.Notification.send')
    def test_notify_client_assigned_agency_became_published(self, send_mock):
        """Should notify all assigned agencies, if became published.
        Only Agency Administrator and Agency Manager should receive them
        """
        client = f.create_client()
        client_admin = f.create_client_administrator(client)

        agency1 = f.create_agency()
        agency_manager1 = f.create_agency_manager(agency1)
        f.create_contract(agency1, client)

        agency2 = f.create_agency()
        recruiter2 = f.create_recruiter(agency2)  # shouldn't receive
        f.create_contract(agency2, client)

        job = f.create_job(client, published=True)
        job.assign_agency(agency1)
        job.assign_agency(agency2)

        notify_client_assigned_agency(
            sender=client_admin,
            job=job,
            diff=compare_model_dicts(
                {'published': False, 'agencies': []},
                {'published': True, 'agencies': [agency1.id]},
                compare=['published'],
                compare_as_set=['agencies'],
            ),
        )

        notified_users = [
            agency_manager1,
            agency1.primary_contact,
            agency2.primary_contact,
        ]

        self.assertEqual(send_mock.call_count, len(notified_users))

        for r in notified_users:
            send_mock.assert_any_call(
                r,
                m.NotificationTypeEnum.CLIENT_ASSIGNED_AGENCY_FOR_JOB,
                sender=client_admin,
                actor=client,
                target=job,
                # send_via_email=r.email_client_assigned_agency_for_job,
            )

    @skip('TODO(ZOO-963)')
    @patch('core.models.Notification.send')
    def check_notify_client_assigned_agency_published(
        self, send_mock, job_published=True
    ):
        client = f.create_client()
        agency = f.create_agency()
        f.create_contract(agency, client)

        client_admin = f.create_client_administrator(client)
        recruiter = f.create_recruiter(agency)

        job = f.create_job(client)
        job.published = job_published
        job.save()
        job.assign_agency(agency)

        notify_client_assigned_agency(
            sender=client_admin,
            job=job,
            diff=compare_model_dicts(
                {'published': not job_published},
                {'published': job_published},
                compare=['published'],
            ),
        )

        if job_published:
            send_mock.assert_called_once_with(
                recruiter,
                m.NotificationTypeEnum.CLIENT_ASSIGNED_AGENCY_FOR_JOB,
                sender=client_admin,
                actor=client,
                target=job,
                # send_via_email=recruiter.email_client_assigned_agency_for_job,
            )
        else:
            send_mock.assert_not_called()

    def test_notify_client_assigned_agency_published(self):
        """Should notify all assigned agencies when published."""
        self.check_notify_client_assigned_agency()
        self.check_notify_agency_assigned_member()

    def test_notify_client_assigned_agency_unpublished(self):
        """Should not notify when unpublished."""
        self.check_notify_client_assigned_agency(job_published=False)
        self.check_notify_agency_assigned_member(job_published=False)

    @patch('core.models.Notification.send')
    def check_notify_client_changed_proposal_status(
        self, send_mock, check_disabled=False
    ):
        client = f.create_client()
        agency = f.create_agency()
        f.create_contract(agency, client)

        client_admin = f.create_client_administrator(client)
        recruiter = f.create_recruiter(agency)

        job = f.create_job(client)
        job.assign_agency(agency)

        candidate = f.create_candidate(agency)
        proposal = f.create_proposal(job, candidate, recruiter)
        proposal.save()

        creator = proposal.created_by
        if check_disabled:
            n = m.NotificationSetting.objects.filter(
                user=creator,
                notification_type_group=m.NotificationTypeEnum.CLIENT_CHANGED_PROPOSAL_STATUS.value.group,
            ).first()
            n.email = False
            n.save()

        next_status = f.get_random_proposal_status(m.ProposalStatusGroup.SUITABLE.key)

        notify_client_changed_proposal_status(
            sender=client_admin,
            proposal=proposal,
            diff=compare_model_dicts(
                {'status': proposal.status.id},
                {'status': next_status.id},
                compare=['status'],
            ),
        )

        send_mock.assert_called_once_with(
            creator,
            m.NotificationTypeEnum.CLIENT_CHANGED_PROPOSAL_STATUS,
            sender=client_admin,
            actor=client_admin,
            action_object=candidate,
            target=proposal,
            context_data={
                'old_status': proposal.status.status,
                'status': next_status.status,
                'link_text': NotificationLinkText.PROPOSAL_DETAIL.name,
            },
        )

    def test_notify_client_changed_proposal_status(self):
        """Should send notification about changed proposal status."""
        self.check_notify_client_changed_proposal_status()

    def test_notify_client_changed_proposal_status_disabled(self):
        """Should not send email notification, if disabled by user."""
        self.check_notify_client_changed_proposal_status(check_disabled=True)

    @skip('TODO(ZOO-963)')
    @patch('core.models.Notification.send')
    def check_notify_proposal_moved(
        self,
        send_mock,
        recruiter_has_access=True,
        check_disabled=False,
        check_by_recruiter=False,
    ):
        client = f.create_client()
        agency = f.create_agency()
        f.create_contract(agency, client)

        client_admin = f.create_client_administrator(client)
        hm = f.create_hiring_manager(client)
        recruiter = f.create_recruiter(agency)
        if check_disabled:
            # recruiter.email_proposal_moved = False
            recruiter.save()

        job = f.create_job(client)
        job.assign_manager(hm)
        if recruiter_has_access:
            job.assign_agency(agency)
            job.assign_member(recruiter)

        another_job = f.create_job(client)
        another_hm = f.create_hiring_manager(client)
        another_job.assign_manager(another_hm)
        another_job.assign_agency(agency)

        candidate = f.create_candidate(agency)
        proposal = f.create_proposal(job, candidate, recruiter)
        proposal.moved_from_job = another_job
        proposal.save()

        if check_by_recruiter:
            sender = recruiter
            recipients = [hm, another_hm]
        else:
            sender = client_admin
            recipients = [recruiter] if recruiter_has_access else []

        notify_proposal_moved(sender=sender, proposal=proposal)

        for recipient in recipients:
            send_mock.assert_any_call(
                recipient,
                m.NotificationTypeEnum.PROPOSAL_MOVED,
                sender=sender,
                actor=sender.profile.org,
                action_object=candidate,
                target=job,
                context_data={'from_job': proposal.moved_from_job.title},
                # send_via_email=recipient.email_proposal_moved,
            )

        if not recipients:
            send_mock.assert_not_called()

    def test_notify_proposal_moved_by_client_admin(self):
        """Should send notification about moved proposal to recruiter."""
        self.check_notify_proposal_moved()

    def test_notify_proposal_moved_recruiter_no_access(self):
        """Should send notification about moved proposal to HMs."""
        self.check_notify_proposal_moved(recruiter_has_access=False)

    def test_notify_proposal_moved_by_recruiter(self):
        """Should send notification about moved proposal to HMs."""
        self.check_notify_proposal_moved(check_by_recruiter=True)

    def test_notify_proposal_moved_disabled(self):
        """Should not send email notification, if disabled by user."""
        self.check_notify_proposal_moved(check_disabled=True)

    @skip('TODO(ZOO-963)')
    @patch('core.models.Notification.send')
    def check_notify_client_admin_assigned_manager(
        self, send_mock, check_disabled=False
    ):
        client = f.create_client()

        client_admin = f.create_client_administrator(client)
        manager = f.create_hiring_manager(client)
        if check_disabled:
            manager.email_client_admin_assigned_manager_for_job = False
            manager.save()

        job = f.create_job(client)
        job.assign_manager(manager)

        notify_client_admin_assigned_manager(
            sender=client_admin,
            job=job,
            diff=compare_model_dicts(
                {'managers': []},
                {'managers': [manager.pk]},
                compare_as_set=['managers'],
            ),
        )

        nt = m.NotificationTypeEnum.TALENT_ASSIGNED_MANAGER_FOR_JOB

        send_mock.assert_called_once_with(
            manager,
            nt,
            sender=client_admin,
            actor=client_admin,
            target=job,
            # send_via_email=manager.email_client_admin_assigned_manager_for_job,
        )

    def test_notify_client_admin_assigned_manager(self):
        self.check_notify_client_admin_assigned_manager()

    @skip('TODO(ZOO-963)')
    def test_notify_client_admin_assigned_manager_disabled(self):
        """Should not send notification, if disabled by user."""
        self.check_notify_client_admin_assigned_manager(check_disabled=True)

    @skip('TODO(ZOO-963)')
    @patch('core.models.Notification.send')
    def test_notify_client_admin_assigned_manager_no_diff(self, send_mock):
        client = f.create_client()

        client_admin = f.create_client_administrator(client)
        manager = f.create_hiring_manager(client)

        job = f.create_job(client)
        job.assign_manager(manager)

        notify_client_admin_assigned_manager(sender=client_admin, job=job, diff={})

        send_mock.assert_not_called()

    @patch('core.models.Notification.send')
    def check_notify_candidate_proposed_for_job(
        self, send_mock, proposed_by, stage, check_disabled=False
    ):
        client_admin = f.create_user()
        client = f.create_client(primary_contact=client_admin)
        client.assign_administrator(client_admin)

        agency = f.create_agency()
        f.create_contract(agency, client)

        manager = f.create_hiring_manager(client)
        manager_unassigned = f.create_hiring_manager(client)

        if check_disabled:
            for u in [client_admin, manager, manager_unassigned]:
                # u.email_candidate_shortlisted_for_job = stage == 'shortlist'
                # u.email_candidate_longlisted_for_job = stage == 'longlist'
                u.save()

        recruiter = f.create_recruiter(agency)

        job = f.create_job(client)
        job.assign_agency(agency)
        job.assign_manager(manager)

        submitter = manager if proposed_by == 'client' else recruiter
        if proposed_by == client:
            actor = client
            owner = client_admin
        else:
            actor = agency
            owner = recruiter

        candidate = f.create_candidate(actor, owner=owner)

        proposal = f.create_proposal(job, candidate, submitter, stage=stage)

        notify_candidate_proposed_for_job(sender=submitter, proposal=proposal)

        if stage == 'shortlist':
            notification_type = m.NotificationTypeEnum.CANDIDATE_SHORTLISTED_FOR_JOB
            send_via_email_field = "email_candidate_shortlisted_for_job"
        else:
            notification_type = m.NotificationTypeEnum.CANDIDATE_LONGLISTED_FOR_JOB
            send_via_email_field = "email_candidate_longlisted_for_job"

        if stage == 'longlist' and proposed_by == 'agency':
            users_should_receive_notification = []
        elif proposed_by == 'client':
            users_should_receive_notification = [client_admin]
        else:
            users_should_receive_notification = [client_admin, manager]

        for u in users_should_receive_notification:
            send_mock.assert_any_call(
                u,
                notification_type,
                sender=submitter,
                actor=actor,
                action_object=candidate,
                target=job,
                # send_via_email=getattr(u, send_via_email_field),
            )

        self.assertEqual(send_mock.call_count, len(users_should_receive_notification))

    @skip("TODO(ZOO-830")
    @patch('core.models.Notification.send')
    def test_notify_candidate_proposed_for_job_sender(self, send_mock):
        """Should not send a Notification to a User proposed a Candidate."""

        client_admin = f.create_user()
        client = f.create_client(primary_contact=client_admin)
        client.assign_administrator(client_admin)

        hm = f.create_hiring_manager(client)

        job = f.create_job(client)
        job.assign_manager(hm)

        candidate = f.create_candidate(client, owner=client_admin)
        proposal = f.create_proposal(job, candidate, client_admin)

        notify_candidate_proposed_for_job(sender=client_admin, proposal=proposal)

        nt = m.NotificationTypeEnum.CANDIDATE_SHORTLISTED_FOR_JOB

        send_mock.assert_called_once_with(
            hm,
            nt,
            sender=client_admin,
            actor=client,
            action_object=candidate,
            target=job,
            # send_via_email=hm.email_candidate_shortlisted_for_job,
        )

    @skip("TODO(ZOO-963)")
    def test_notify_shortlisted_candidate_proposed_for_job_by_client(self):
        self.check_notify_candidate_proposed_for_job(
            proposed_by='client', stage='shortlist'
        )

    @skip("TODO(ZOO-963)")
    def test_notify_longlisted_candidate_proposed_for_job_by_client(self):
        self.check_notify_candidate_proposed_for_job(
            proposed_by='client', stage='longlist'
        )

    @skip("TODO(ZOO-963)")
    def test_notify_candidate_proposed_for_job_disabled(self):
        """Should not send notification, if disabled by user."""
        self.check_notify_candidate_proposed_for_job(
            proposed_by='client', stage='shortlist', check_disabled=True
        )

    @skip("TODO(ZOO-963)")
    def test_notify_longlisted_candidate_proposed_for_job_by_agency(self):
        """Shouldn't notify if Agency proposes a longlisted candidate"""
        self.check_notify_candidate_proposed_for_job(
            proposed_by='agency', stage='longlist'
        )

    @skip("TODO(ZOO-963)")
    def test_notify_shortlisted_candidate_proposed_for_job_by_agency(self):
        """Should notify if Agency proposes a shortlisted candidate"""
        self.check_notify_candidate_proposed_for_job(
            proposed_by='agency', stage='shortlist'
        )

    def test_get_interview_notification_email_context(self):
        interview = setup_interview_test()

        context = get_interview_notification_email_context(interview)

        self.assertDictEqual(
            {
                'job': interview.proposal.job.title,
                'user': interview.created_by.full_name,
                'candidate': interview.proposal.candidate.name,
                'organisation': interview.created_by.profile.org.name,
                'interview_order': interview.order,
                'interviewer': interview.interviewer.name,
                'info': interview.notes,
            },
            context,
        )

    @staticmethod
    def get_interview_notification_kwargs(interview):
        proposal = interview.proposal
        job = proposal.job

        return {
            'sender': None,
            'send_via_email': False,
            'actor': proposal.candidate,
            'target': job,
            'link': reverse(
                'proposal_page', kwargs={'job_id': job.id, 'proposal_id': proposal.id,}
            ),
        }

    @skip('TODO(ZOO-963)')
    @patch('core.notifications.send_email')
    @patch('core.models.Notification.send')
    def test_notify_proposal_interview_rejected(self, send_mock, send_email_mock):
        interview = setup_interview_test()

        interviewer = interview.created_by
        notify_proposal_interview_rejected(None, interview)

        kwargs = self.get_interview_notification_kwargs(interview)

        self.assert_has_only_calls(
            mock=send_mock,
            calls=[
                call(
                    interviewer,
                    m.NotificationTypeEnum.PROPOSAL_INTERVIEW_REJECTED,
                    action_object=None,
                    **kwargs,
                ),
            ],
        )

        context = get_interview_notification_email_context(interview)

        self.assert_has_only_calls(
            mock=send_email_mock,
            calls=[call(interviewer.email, 'candidate_interview_rejected', context)],
        )


def action_object_filter(object):
    return poly_relation_filter(
        'action_object_object_id', 'action_object_content_type', object
    )


class CandidatePlacementNotificationTestCase(TestCase):
    DRAFT = m.FeeStatus.DRAFT.key
    DRAFT_VERB = m.NotificationTypeEnum.PLACEMENT_FEE_DRAFT.name.lower()
    NEEDS_REVISION = m.FeeStatus.NEEDS_REVISION.key
    NEEDS_REVISION_VERB = (
        m.NotificationTypeEnum.PLACEMENT_FEE_NEEDS_REVISION.name.lower()
    )
    APPROVED = m.FeeStatus.APPROVED.key
    APPROVED_VERB = m.NotificationTypeEnum.PLACEMENT_FEE_APPROVED.name.lower()
    PENDING = m.FeeStatus.PENDING.key
    PENDING_VERB = m.NotificationTypeEnum.PLACEMENT_FEE_PENDING.name.lower()
    PENDING_REMINDER_VERB = (
        m.NotificationTypeEnum.PLACEMENT_FEE_PENDING_REMINDER.name.lower()
    )

    def create_placement(self, user, submitter, status=DRAFT):
        agency = f.create_agency()
        agency.assign_recruiter(user)
        if user != submitter:
            agency.assign_recruiter(submitter)

        client = f.create_client()
        f.create_contract(agency, client)
        job = f.create_job(client, client=client)
        job.assign_agency(agency)

        return f.create_fee(
            proposal=f.create_proposal(
                job=job,
                candidate=f.create_candidate(agency, created_by=user, owner=user),
                created_by=user,
            ),
            status=status,
            agency=agency,
            created_by=user,
            submitted_by=submitter,
        )

    @skip('TODO(ZOO-963)')
    def test_candidate_placement_needs_revision(self):
        user = f.create_user()
        submitter = f.create_user()

        placement = self.create_placement(user, submitter, self.NEEDS_REVISION)

        notify_fee_status_change(placement, user)

        self.assertEqual(
            m.Notification.objects.filter(verb=self.NEEDS_REVISION_VERB).count(), 1,
        )

        self.assertEqual(
            m.Notification.objects.filter(
                action_object_filter(placement),
                verb=self.NEEDS_REVISION_VERB,
                recipient=submitter,
            ).count(),
            1,
        )

    @skip('TODO(ZOO-963)')
    def test_candidate_placement_draft(self):
        user = f.create_user()
        submitter = f.create_user()

        placement = self.create_placement(user, submitter, self.DRAFT)

        notify_fee_status_change(placement, user)

        self.assertEqual(
            m.Notification.objects.filter(verb=self.DRAFT_VERB).count(), 1,
        )

        self.assertEqual(
            m.Notification.objects.filter(
                action_object_filter(placement),
                verb=self.DRAFT_VERB,
                recipient=submitter,
            ).count(),
            1,
        )

    @skip('TODO(ZOO-963)')
    def make_assert_notified(self, queryset, send_email):
        def assert_notified(recipient=None, is_email_sent=True):
            found = list(queryset.filter(recipient=recipient))

            self.assertEqual(len(found), 1)

            notification = found[0]

            is_send_email_called = False
            for send_email_call in send_email.call_args_list:
                is_send_email_called = (
                    send_email_call[1]['body'] == notification.email_text
                    and send_email_call[1]['to'][0] == recipient.email
                )
                if is_send_email_called:
                    break

            self.assertEqual(is_email_sent, is_send_email_called)

        return assert_notified

    @skip('TODO(ZOO-963)')
    @patch('core.models.send_email.delay')
    def test_candidate_placement_approved(self, send_email):
        user = f.create_user()
        submitter = f.create_user()

        placement = self.create_placement(user, submitter, self.APPROVED)

        agency = placement.agency

        team = f.create_team(agency, notify_if_fee_approved=True)

        admin = f.create_agency_administrator(agency)
        manager = f.create_agency_manager(agency)
        recruiter = f.create_recruiter(agency)

        team_members = [
            user,
            admin,
            manager,
            recruiter,
        ]

        f.create_agency_administrator(agency)
        f.create_agency_manager(agency)
        f.create_recruiter(agency)

        for member in team_members:
            member.profile.teams.add(team)

        queryset = m.Notification.objects.filter(
            action_object_filter(placement), verb=self.APPROVED_VERB,
        )

        assert_notified = self.make_assert_notified(queryset, send_email)

        notify_fee_status_change(placement, user)

        self.assertEqual(queryset.count(), 5)

        assert_notified(submitter)
        assert_notified(user, is_email_sent=False)
        assert_notified(admin)
        assert_notified(manager)
        assert_notified(recruiter)

    @skip('TODO(ZOO-963)')
    @patch('core.models.send_email.delay')
    def test_candidate_placement_pending(self, send_email):
        submitter = f.create_user()
        placement = self.create_placement(submitter, submitter, self.PENDING)

        agency = placement.agency

        admin = f.create_agency_administrator(agency)
        manager = f.create_agency_manager(agency)
        recruiter = f.create_recruiter(agency)

        notify_fee_status_change(placement, submitter)

        queryset = m.Notification.objects.filter(
            action_object_filter(placement), verb=self.PENDING_VERB,
        )

        assert_notified = self.make_assert_notified(queryset, send_email)

        self.assertEqual(queryset.count(), 4)

        assert_notified(submitter, is_email_sent=False)
        assert_notified(agency.primary_contact)
        assert_notified(manager)
        assert_notified(admin)

    @skip('TODO(ZOO-963)')
    @patch('core.models.send_email.delay')
    def test_candidate_placement_pending_reminder(self, send_email):
        submitter = f.create_user()
        placement = self.create_placement(submitter, submitter, self.PENDING)

        agency = placement.agency

        admin = f.create_agency_administrator(agency)
        manager = f.create_agency_manager(agency)
        recruiter = f.create_recruiter(agency)

        notify_fee_pending(submitter, placement, True)

        queryset = m.Notification.objects.filter(
            action_object_filter(placement), verb=self.PENDING_REMINDER_VERB,
        )

        assert_notified = self.make_assert_notified(queryset, send_email)

        self.assertEqual(queryset.count(), 4)

        assert_notified(submitter, is_email_sent=False)
        assert_notified(agency.primary_contact)
        assert_notified(manager)
        assert_notified(admin)


class TestNotifyProposalInterviewConfirmed(TestCase, MockCallsMixin):
    def setUp(self):
        self.interview = setup_interview_test()

        self.proposal = self.interview.proposal
        self.job = self.proposal.job
        self.client_org = self.job.organization

        self.manager = UserFactory.create()
        self.client_org.assign_standard_user(self.manager)
        self.job.assign_manager(self.manager)

        self.recruiter = UserFactory.create()
        self.client_org.assign_internal_recruiter(self.recruiter)
        self.job.recruiters.add(self.recruiter)

        self.expected_send_notification_kwargs = {
            'sender': None,
            'action_object': self.interview,
            'actor': self.proposal.candidate,
            'target': self.proposal,
            'context_data': {
                'link_text': m.NotificationLinkText.PROPOSAL_DETAIL.name,
                'timeframe': self.interview.format(),
            },
        }

    def assert_staff_notified(self, send_notification_mock):
        self.assert_has_only_calls(
            send_notification_mock,
            [
                call(
                    self.recruiter,
                    m.NotificationTypeEnum.INTERVIEW_PROPOSAL_CONFIRMED_PROPOSER,
                    **self.expected_send_notification_kwargs,
                    email_attachments=None,
                ),
                call(
                    self.interview.interviewer,
                    m.NotificationTypeEnum.INTERVIEW_PROPOSAL_CONFIRMED_INTERVIEWER,
                    **self.expected_send_notification_kwargs,
                    email_attachments=[self.interview.ics_attachment],
                ),
            ],
        )

    @patch('core.notifications.send_email')
    @patch('core.models.Notification.send')
    def test_proposed_interview(self, send_notification_mock, send_email_mock):
        notify_proposal_interview_confirmed(None, self.interview)

        self.assert_staff_notified(send_notification_mock)

        context = get_interview_notification_email_context(self.interview)
        context['timeframe'] = self.interview.format()
        attachments = [self.interview.ics_attachment]

        self.assert_has_only_calls(
            send_email_mock,
            [
                call(
                    self.proposal.candidate.email,
                    'candidate_interview_confirmed/to_candidate',
                    context=context,
                    extension='html',
                    attachments=attachments,
                ),
            ],
        )

    @patch('core.notifications.send_email')
    @patch('core.models.Notification.send')
    def test_simple_schedule(self, send_notification_mock, send_email_mock):
        self.interview.scheduling_type = (
            m.ProposalInterviewSchedule.SchedulingType.SIMPLE_SCHEDULING
        )

        notify_proposal_interview_confirmed(None, self.interview)

        self.assert_staff_notified(send_notification_mock)

        self.assertEqual(0, send_email_mock.call_count)


class TestNotifyProposalInterviewCanceled(TestCase, MockCallsMixin):
    def setUp(self):
        self.interview = setup_interview_test()

        self.proposal = self.interview.proposal
        self.job = self.proposal.job
        self.client_org = self.job.organization

        self.manager = UserFactory.create()
        self.client_org.assign_standard_user(self.manager)
        self.job.assign_manager(self.manager)

        self.recruiter = UserFactory.create()
        self.client_org.assign_internal_recruiter(self.recruiter)
        self.job.recruiters.add(self.recruiter)

        sender = None
        self.expected_send_notification_kwargs = {
            'sender': sender,
            'actor': sender,
            'action_object': self.interview,
            'target': self.proposal,
            'context_data': {
                'link_text': m.NotificationLinkText.PROPOSAL_DETAIL.name,
                'timeframe': self.interview.format(),
            },
        }

    def assert_staff_notified(self, send_notification_mock):
        self.assert_has_only_calls(
            send_notification_mock,
            [
                call(
                    self.recruiter,
                    m.NotificationTypeEnum.INTERVIEW_PROPOSAL_CANCELED,
                    **self.expected_send_notification_kwargs,
                    send_via_email=False,
                    email_attachments=None,
                ),
                call(
                    self.interview.interviewer,
                    m.NotificationTypeEnum.INTERVIEW_PROPOSAL_CANCELED,
                    **self.expected_send_notification_kwargs,
                    send_via_email=True,
                    email_attachments=[self.interview.ics_canceled_attachment],
                ),
            ],
        )

    @patch('core.notifications.send_email')
    @patch('core.models.Notification.send')
    def test_proposed_interview(self, send_notification_mock, send_email_mock):
        notify_proposal_interview_canceled(None, self.interview)

        self.assert_staff_notified(send_notification_mock)

        context = get_interview_notification_email_context(self.interview)
        context['timeframe'] = self.interview.format()
        attachments = [self.interview.ics_canceled_attachment]

        self.assert_has_only_calls(
            send_email_mock,
            [
                call(
                    self.proposal.candidate.email,
                    'candidate_interview_canceled/to_candidate',
                    context=context,
                    extension='html',
                    attachments=attachments,
                ),
            ],
        )

    @patch('core.notifications.send_email')
    @patch('core.models.Notification.send')
    def test_simple_schedule(self, send_notification_mock, send_email_mock):
        self.interview.scheduling_type = (
            m.ProposalInterviewSchedule.SchedulingType.SIMPLE_SCHEDULING
        )

        notify_proposal_interview_canceled(None, self.interview)

        self.assert_staff_notified(send_notification_mock)

        self.assertEqual(0, send_email_mock.call_count)
