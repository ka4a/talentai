from core.constants import NotificationLinkText
from itertools import chain

from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from core import models as m
from core.utils import send_email


def get_interview_notification_email_context(interview):

    return {
        'job': interview.proposal.job.title,
        'user': interview.created_by.full_name,
        'candidate': interview.proposal.candidate.name,
        'organisation': interview.created_by.profile.org.name,
        'interview_order': interview.order,
        'interviewer': interview.interviewer.name,
        'info': interview.notes,
    }


def notify_fee_pending(sender, fee, is_reminder=False):
    # TODO(ZOO-): Notification
    return
    try:
        org = fee.created_by.org
    except AttributeError:
        org = None

    recipients = set()

    if isinstance(org, m.Agency):
        recipients = set(
            m.User.objects.filter(
                Q(agencyadministrator__agency=org) | Q(agencymanager__agency=org)
            )
        )

    placement_verb = m.NotificationTypeEnum.PLACEMENT_FEE_PENDING
    fee_verb = m.NotificationTypeEnum.FEE_PENDING

    if is_reminder:
        placement_verb = m.NotificationTypeEnum.PLACEMENT_FEE_PENDING_REMINDER
        fee_verb = m.NotificationTypeEnum.FEE_PENDING_REMINDER

    if fee.submitted_by:
        recipients.add(fee.submitted_by)

    for recipient in recipients:
        m.Notification.send(
            recipient,
            placement_verb if fee.placement else fee_verb,
            sender=sender,
            send_via_email=recipient != sender and recipient.email_fee_pending,
            actor=fee.submitted_by or fee.created_by,
            action_object=fee,
            link=reverse('fee_page', kwargs={'fee_id': fee.id}),
        )


def notify_fee_submitter(sender, fee, verb, send_via_email):
    # TODO(ZOO-): Notification
    return
    recipient = fee.submitted_by

    if not recipient:
        return

    m.Notification.send(
        recipient,
        verb,
        sender=sender,
        send_via_email=recipient != sender and send_via_email,
        actor=fee.submitted_by,
        action_object=fee,
        link=reverse('fee_page', kwargs={'fee_id': fee.id}),
    )


def notify_fee_approved(sender, fee):
    # TODO(ZOO-): Notification
    return
    recipients = set()
    if fee.submitted_by:
        recipients.add(fee.submitted_by)

    profile_models = [m.AgencyAdministrator, m.AgencyManager, m.Recruiter]
    for model in profile_models:
        queryset = model.objects.filter(
            agency=fee.agency, teams__notify_if_fee_approved=True,
        )
        for profile in queryset:
            recipients.add(profile.user)

    for recipient in recipients:
        m.Notification.send(
            recipient,
            m.NotificationTypeEnum.PLACEMENT_FEE_APPROVED
            if fee.placement
            else m.NotificationTypeEnum.FEE_APPROVED,
            sender=sender,
            send_via_email=recipient != sender and recipient.email_fee_approved,
            actor=fee.submitted_by or fee.created_by,
            action_object=fee,
            link=reverse('fee_page', kwargs={'fee_id': fee.id}),
        )


def notify_fee_status_change(instance, user, status=None):
    # TODO(ZOO-): Notification
    return

    status = status or instance.status
    if status == m.FeeStatus.PENDING.key:
        notify_fee_pending(user, instance)

    if status == m.FeeStatus.APPROVED.key:
        notify_fee_approved(user, instance)

    if status == m.FeeStatus.NEEDS_REVISION.key:
        notify_fee_submitter(
            user,
            instance,
            m.NotificationTypeEnum.PLACEMENT_FEE_NEEDS_REVISION
            if instance.placement
            else m.NotificationTypeEnum.FEE_NEEDS_REVISION,
            user.email_fee_needs_revision,
        )

    if status == m.FeeStatus.DRAFT.key:
        notify_fee_submitter(
            user,
            instance,
            m.NotificationTypeEnum.PLACEMENT_FEE_DRAFT
            if instance.placement
            else m.NotificationTypeEnum.FEE_DRAFT,
            user.email_fee_needs_revision,
        )


def notify_proposal_interview_status_changed(
    sender, interview, verb, recipient=None, action_object=None,
):
    # TODO(ZOO-): Notification
    return
    interviewer = interview.created_by
    proposal = interview.proposal
    job = proposal.job

    m.Notification.send(
        recipient or interviewer,
        verb,
        sender=sender,
        send_via_email=False,
        actor=proposal.candidate,
        action_object=action_object,
        target=job,
        link=reverse(
            'proposal_page', kwargs={'job_id': job.id, 'proposal_id': proposal.id,},
        ),
    )


def format_interview_timeframe(interview):
    return interview.format('%a %b %d, %Y {start_at} - {end_at} (%Z)', '%H:%M')


def is_interview_proposal(interview):
    return (
        interview.scheduling_type
        == m.ProposalInterviewSchedule.SchedulingType.INTERVIEW_PROPOSAL
    )


def notify_proposal_interview_canceled(sender, interview):
    """
    Notify recruiter, interviewer
    Email interviewer
    Email candidate (if candidate email exists)
    """
    proposal = interview.proposal
    candidate = proposal.candidate
    context_data = {
        'link_text': m.NotificationLinkText.PROPOSAL_DETAIL.name,
        'timeframe': format_interview_timeframe(interview),
    }
    attachments = [interview.ics_canceled_attachment]

    def send_to_staff(recipient, send_via_email=False, email_attachments=None):
        m.Notification.send(
            recipient,
            m.NotificationTypeEnum.INTERVIEW_PROPOSAL_CANCELED,
            sender=sender,
            actor=sender,
            action_object=interview,
            target=proposal,
            context_data=context_data,
            send_via_email=send_via_email,
            email_attachments=email_attachments,
        )

    # to recruiters
    for recipient in proposal.job.recruiters.all():
        send_to_staff(recipient)

    # to interviewer
    if interview.interviewer:
        send_to_staff(
            interview.interviewer, send_via_email=True, email_attachments=attachments,
        )

    # to candidate
    if is_interview_proposal(interview) and candidate.email:
        email_args = {
            'context': {
                **get_interview_notification_email_context(interview),
                'timeframe': format_interview_timeframe(interview),
            },
            'extension': 'html',
            'attachments': attachments,
        }
        send_email(
            candidate.email, f'candidate_interview_canceled/to_candidate', **email_args,
        )


def notify_proposal_interview_confirmed(sender, interview):
    """
    Notify hiring manager, recruiters,
    Email interviewer with calendar attachment,
    Email candidate (if candidate email exists)
    """
    proposal = interview.proposal
    candidate = proposal.candidate
    timeframe = format_interview_timeframe(interview)

    def send_to_staff(_recipient, notification_type, attachments=None):
        if _recipient:
            m.Notification.send(
                _recipient,
                notification_type,
                sender=sender,
                actor=candidate,
                action_object=interview,
                target=proposal,
                context_data={
                    'link_text': m.NotificationLinkText.PROPOSAL_DETAIL.name,
                    'timeframe': timeframe,
                },
                email_attachments=attachments,
            )

    # to recruiters
    for recipient in proposal.job.recruiters.all():
        send_to_staff(
            recipient,
            notification_type=m.NotificationTypeEnum.INTERVIEW_PROPOSAL_CONFIRMED_PROPOSER,
        )

    send_to_staff(
        interview.interviewer,
        notification_type=m.NotificationTypeEnum.INTERVIEW_PROPOSAL_CONFIRMED_INTERVIEWER,
        attachments=[interview.ics_attachment],
    )

    # to candidate
    if is_interview_proposal(interview) and candidate.email:
        email_args = {
            'context': {
                **get_interview_notification_email_context(interview),
                'timeframe': timeframe,
            },
            'extension': 'html',
            'attachments': [interview.ics_attachment],
        }
        send_email(
            candidate.email,
            f'candidate_interview_confirmed/to_candidate',
            **email_args,
        )


def notify_proposal_interview_rejected(sender, interview):
    proposal = interview.proposal
    candidate = proposal.candidate

    # to recruiters
    for recruiter in proposal.job.recruiters.all():
        m.Notification.send(
            recruiter,
            m.NotificationTypeEnum.INTERVIEW_PROPOSAL_REJECTED_RECRUITER,
            sender=sender,
            actor=candidate,
            action_object=interview,
            target=proposal,
            context_data={'link_text': m.NotificationLinkText.PROPOSAL_DETAIL.name,},
        )

    # to interviewer
    if interview.interviewer:
        m.Notification.send(
            interview.interviewer,
            m.NotificationTypeEnum.INTERVIEW_PROPOSAL_REJECTED_INTERVIEWER,
            sender=sender,
            actor=candidate,
            action_object=interview,
            target=proposal,
            context_data={'link_text': m.NotificationLinkText.PROPOSAL_DETAIL.name,},
            email_attachments=[interview.ics_attachment],
        )


def notify_interview_assessment_added(sender, interview):
    proposal = interview.proposal

    # to recruiters
    for recruiter in proposal.job.recruiters.all():
        m.Notification.send(
            recruiter,
            m.NotificationTypeEnum.INTERVIEW_ASSESSMENT_ADDED_RECRUITER,
            sender=sender,
            actor=sender,
            action_object=interview,
            target=proposal,
            context_data={
                'link_text': m.NotificationLinkText.PROPOSAL_DETAIL.name,
                'timeframe': format_interview_timeframe(interview),
            },
        )

    # to interviewer
    if interview.interviewer:
        m.Notification.send(
            interview.interviewer,
            m.NotificationTypeEnum.INTERVIEW_ASSESSMENT_ADDED_INTERVIEWER,
            sender=sender,
            actor=sender,
            action_object=interview,
            target=proposal,
            context_data={
                'link_text': m.NotificationLinkText.PROPOSAL_DETAIL.name,
                'timeframe': format_interview_timeframe(interview),
            },
        )


def notify_contract_initiated(sender, contract):
    # TODO(ZOO-): Notification
    return
    agency_recipient = contract.agency.primary_contact

    client_recipient = contract.client.primary_contact

    if agency_recipient:
        m.Notification.send(
            agency_recipient,
            m.NotificationTypeEnum.CONTRACT_INITIATED_AGENCY,
            sender=sender,
            actor=contract.client,
            action_object=contract.agency,
        )

    if client_recipient:
        m.Notification.send(
            client_recipient,
            m.NotificationTypeEnum.CONTRACT_INITIATED_CLIENT,
            sender=sender,
            actor=contract.agency,
            action_object=contract.client,
        )


def notify_client_created_contract(sender, contract):
    # TODO(ZOO-): Notification
    return
    recipient = contract.agency.primary_contact

    if not recipient:
        return

    m.Notification.send(
        recipient,
        m.NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
        sender=sender,
        actor=contract.client,
        action_object=contract.agency,
        reply_to=getattr(contract.client.primary_contact, 'email', None),
        link=reverse('invitations_page'),
    )


def notify_contract_signed_by_one_party(sender, contract, to_agency):
    # TODO(ZOO-): Notification
    return
    if to_agency:
        recipient = contract.agency.primary_contact
        actor = contract.client
        action_object = contract.agency
    else:
        recipient = contract.client.primary_contact
        actor = contract.agency
        action_object = contract.client

    if not recipient:
        return

    m.Notification.send(
        recipient,
        m.NotificationTypeEnum.CONTRACT_SIGNED_BY_ONE_PARTY,
        sender=sender,
        actor=actor,
        action_object=action_object,
        link=reverse('invitations_page'),
    )


def notify_removed_job_access(sender, contract):
    # TODO(ZOO-): Notification
    return
    recipient = contract.client.primary_contact
    if not recipient:
        return
    notification = m.NotificationTypeEnum.CONTRACT_JOB_ACCESS_REVOKED_INVITE_IGNORED
    if contract.status == m.ContractStatus.PENDING.key:
        notification = m.NotificationTypeEnum.CONTRACT_JOB_ACCESS_REVOKED_NO_AGREEMENT
    m.Notification.send(
        recipient,
        notification,
        sender=sender,
        actor=contract.agency,
        action_object=contract.client,
    )


def notify_contract_invitation(sender, contract):
    # TODO(ZOO-): Notification
    return
    recipient = getattr(contract.client, 'primary_contact', None)
    if not recipient:
        return

    notification = m.NotificationTypeEnum.CONTRACT_INVITATION_ACCEPTED
    if contract.status == m.ContractStatus.REJECTED.key:
        notification = m.NotificationTypeEnum.CONTRACT_INVITATION_DECLINED

    m.Notification.send(
        recipient,
        notification,
        sender=sender,
        actor=contract.agency,
        action_object=contract.client,
    )


NOTIFY_JOB_FIELDS_COMPARE = [
    'title',
    'work_location',
    'responsibilities',
    'salary_currency',
    'salary_from',
    'salary_to',
    'salary_per',
    'telework_eligibility',
    'employment_type',
]

NOTIFY_JOB_FIELDS_COMPARE_BY_MATCHING_KEY = [
    ('questions', 'id', {'compare': ['text']}),
    ('required_languages', 'id', {'compare': ['id']}),
]


def notify_job_is_filled(sender, job):
    users_to_notify = set(job.managers) | set(job.recruiters.all())

    for user in users_to_notify:
        if user:
            hired_candidates_list = job.get_hired_candidates()
            m.Notification.send(
                user,
                m.NotificationTypeEnum.JOB_IS_FILLED,
                sender=sender,
                actor=sender,
                target=job,
                context_data={
                    'hired_candidates': '\n'.join(
                        [f'・ {c.name}' for c in hired_candidates_list]
                    ),
                    'link_text': NotificationLinkText.JOB_DETAIL.name,
                },
            )


def notify_client_updated_job(sender, job, diff):
    # TODO(ZOO-): Notification
    return
    # if not diff or not job.published:
    #     return
    #
    # for agency in job.agencies.all():
    #     for user in agency.members:  # TODO: check recruiter is assigned
    #         m.Notification.send(
    #             user,
    #             m.NotificationTypeEnum.CLIENT_UPDATED_JOB,
    #             sender=sender,
    #             actor=job.organization,
    #             target=job,
    #         )


def notify_client_assigned_agency(sender, job, diff):
    # TODO(ZOO-): Notification
    return
    # agency_ids = []
    #
    # if diff.get('published', {}).get('to') is True:
    #     # if job was published, notify all assigned agencies
    #     agency_ids = [a.agency_id for a in job.agency_contracts.filter(is_active=True)]
    #
    # elif job.published:
    #     if diff.get('agencies', {}).get('added'):
    #         # if job is published and new agencies were assigned, notify new
    #         agency_ids = diff['agencies']['added']
    #
    # if not agency_ids:
    #     return
    #
    # for agency_id in agency_ids:
    #     agency = m.Agency.objects.get(pk=agency_id)
    #
    #     recipients = m.User.objects.filter(
    #         Q(agencyadministrator__agency=agency) | Q(agencymanager__agency=agency)
    #     )
    #
    #     for recipient in recipients:
    #         m.Notification.send(
    #             recipient,
    #             m.NotificationTypeEnum.CLIENT_ASSIGNED_AGENCY_FOR_JOB,
    #             sender=sender,
    #             actor=job.organization,
    #             target=job,
    #         )


def notify_agency_assigned_job_member(sender, job, assignee_id):
    # TODO(ZOO-): Notification
    return
    # if not job.published:
    #     return
    #
    # assignee = m.User.objects.filter(pk=assignee_id).first()
    #
    # if not assignee or sender.id == assignee_id:
    #     return
    #
    # m.Notification.send(
    #     assignee,
    #     m.NotificationTypeEnum.AGENCY_ASSIGNED_MEMBER_FOR_JOB,
    #     sender=sender,
    #     actor=sender,
    #     target=job,
    # )


def notify_client_changed_proposal_status(sender, proposal, diff):
    if 'status' not in diff or not proposal.created_by:
        return

    old_status = m.ProposalStatus.objects.get(id=diff['status']['from'])
    new_status = m.ProposalStatus.objects.get(id=diff['status']['to'])

    user = proposal.created_by
    if user:
        m.Notification.send(
            user,
            m.NotificationTypeEnum.CLIENT_CHANGED_PROPOSAL_STATUS,
            sender=sender,
            actor=sender,
            action_object=proposal.candidate,
            target=proposal,
            context_data={
                'old_status': old_status.status,
                'status': new_status.status,
                'link_text': NotificationLinkText.PROPOSAL_DETAIL.name,
            },
        )

    if new_status.group == m.ProposalStatusGroup.PENDING_HIRING_DECISION.key:
        for manager in proposal.job.managers:
            m.Notification.send(
                manager,
                m.NotificationTypeEnum.PROPOSAL_PENDING_HIRING_DECISION,
                sender=sender,
                actor=sender,
                action_object=proposal.candidate,
                target=proposal,
                context_data={'link_text': NotificationLinkText.PROPOSAL_DETAIL.name},
            )

    elif new_status.group == m.ProposalStatusGroup.PENDING_START.key:
        recipients = set(proposal.job.managers) | set(proposal.get_interviewers())
        for recipient in recipients:
            if recipient:
                m.Notification.send(
                    recipient,
                    m.NotificationTypeEnum.PROPOSAL_PENDING_START,
                    sender=sender,
                    actor=sender,
                    action_object=proposal.candidate,
                    target=proposal,
                    context_data={
                        'link_text': NotificationLinkText.PROPOSAL_DETAIL.name
                    },
                )


def notify_proposal_moved(sender, proposal, *args, **kwargs):
    # TODO(ZOO-): Notification
    return
    if type(sender.profile.org) is m.Agency:
        recipients = chain(proposal.moved_from_job.managers, proposal.job.managers)
    else:
        has_access = proposal.created_by.profile.apply_jobs_filter(
            m.Job.objects.filter(id=proposal.job.id)
        ).exists()
        if not has_access:
            return

        recipients = [proposal.created_by]

    for user in recipients:
        m.Notification.send(
            user,
            m.NotificationTypeEnum.PROPOSAL_MOVED,
            sender=sender,
            actor=sender.profile.org,
            action_object=proposal.candidate,
            target=proposal.job,
            context_data={'from_job': proposal.moved_from_job.title},
        )


def notify_client_admin_assigned_manager(sender, job, diff):
    # TODO(ZOO-963)
    return
    if not diff.get('managers', {}).get('added'):
        return

    managers = m.User.objects.filter(id__in=diff['managers']['added'])

    for manager in managers:
        m.Notification.send(
            manager,
            m.NotificationTypeEnum.TALENT_ASSIGNED_MANAGER_FOR_JOB,
            sender=sender,
            actor=sender,
            target=job,
        )


def notify_proposal_submitted_to_hiring_manager(sender, proposal):
    for manager in proposal.job.managers:
        m.Notification.send(
            manager,
            m.NotificationTypeEnum.PROPOSAL_SUBMITTED_TO_HIRING_MANAGER,
            sender=sender,
            actor=sender,
            action_object=proposal.candidate,
            target=proposal,
            context_data={'link_text': NotificationLinkText.PROPOSAL_DETAIL.name},
        )


def notify_proposal_approved_rejected_by_hiring_manager(sender, proposal, approved):
    if sender in proposal.job.managers:
        m.Notification.send(
            sender,
            m.NotificationTypeEnum.PROPOSAL_APPROVED_REJECTED_BY_HIRING_MANAGER,
            sender=sender,
            actor=sender,
            action_object=proposal.candidate,
            target=proposal,
            context_data={'decision': (_('Approved') if approved else _('Rejected'))},
            send_via_email=False,
        )


def notify_candidate_proposed_for_job(sender, proposal):
    sourced_by = proposal.candidate.owner
    if sourced_by:
        m.Notification.send(
            sourced_by,
            m.NotificationTypeEnum.NEW_PROPOSAL_CANDIDATE_SOURCED_BY,
            sender=sender,
            actor=sender,
            action_object=proposal.candidate,
            target=proposal,
            context_data={'link_text': NotificationLinkText.PROPOSAL_DETAIL.name},
            send_via_email=False if sourced_by == sender else None,
        )
    for recruiter in proposal.job.recruiters.all():
        m.Notification.send(
            recruiter,
            m.NotificationTypeEnum.NEW_PROPOSAL_CANDIDATE_RECRUITER,
            sender=sender,
            actor=sender,
            action_object=proposal.candidate,
            target=proposal,
            context_data={'link_text': NotificationLinkText.PROPOSAL_DETAIL.name},
        )


def notify_mentioned_users_in_comment(sender, candidate_comment, deleted=False):
    # TODO(ZOO-): Notification
    return
    notified_users = candidate_comment.get_mentioned_users()
    notification_type = (
        m.NotificationTypeEnum.USER_MENTIONED_IN_COMMENT_DELETED
        if deleted
        else m.NotificationTypeEnum.USER_MENTIONED_IN_COMMENT
    )

    for user in notified_users:
        if user == sender:
            continue

        m.Notification.send(
            user,
            notification_type,
            sender=sender,
            actor=sender,
            target=candidate_comment,
            link=reverse(
                'candidate_page',
                kwargs={'candidate_id': candidate_comment.candidate.id},
            )
            + '?st=4',
        )


def notify_client_candidate_public_application(proposal):
    for recruiter in proposal.job.recruiters.all():
        m.Notification.send(
            recruiter,
            m.NotificationTypeEnum.NEW_PROPOSAL_CANDIDATE_DIRECT_APPLICATION,
            actor=proposal.candidate,
            target=proposal,
            context_data={'link_text': NotificationLinkText.PROPOSAL_DETAIL.name},
        )


def notify_proposal_is_rejected(sender, proposal):
    for recruiter in proposal.job.recruiters.all():
        if recruiter == sender:
            m.Notification.send(
                recruiter,
                m.NotificationTypeEnum.PROPOSAL_IS_REJECTED,
                sender=sender,
                actor=sender,
                action_object=proposal.candidate,
                target=proposal,
                send_via_email=False,
            )
        else:
            m.Notification.send(
                recruiter,
                m.NotificationTypeEnum.PROPOSAL_IS_REJECTED,
                sender=sender,
                actor=sender,
                action_object=proposal.candidate,
                target=proposal,
                context_data={'link_text': NotificationLinkText.PROPOSAL_DETAIL.name},
            )


def notify_interview_schedule_sent(sender, interview, candidate_only=False):
    """
    Email candidate (if candidate email exists),
    Notify recruiters, interviewer.
    """
    proposal = interview.proposal
    candidate = proposal.candidate

    # to candidate
    if candidate.email:
        send_email(
            candidate.email,
            'candidate_interview_invitation',
            context={
                'job': proposal.job.title,
                'candidate': candidate.name,
                'sender': sender.full_name,
                'organisation': sender.profile.org.name,
                'uuid': interview.public_uuid,
                'base_url': settings.BASE_URL,
            },
            extension='html',
        )

    if candidate_only:
        return

    # to recruiters, interviewer
    recipients = set(proposal.job.recruiters.all()) | {interview.interviewer}
    for recipient in recipients:
        if recipient:
            m.Notification.send(
                recipient,
                m.NotificationTypeEnum.INTERVIEW_PROPOSAL_IS_SENT,
                sender=sender,
                actor=sender,
                action_object=interview,
                target=proposal,
                send_via_email=False,
                context_data={'link_text': NotificationLinkText.PROPOSAL_DETAIL.name},
            )
