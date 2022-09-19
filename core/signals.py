from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from core.utils import send_email, poly_relation_filter
from core.tasks import (
    create_candidate_file_preview_and_thumbnail,
    convert_job_file,
)

from core.notifications import (
    notify_contract_initiated,
    notify_contract_invitation,
    notify_removed_job_access,
    notify_contract_signed_by_one_party,
)
from core.models import (
    Agency,
    Client,
    JOB_STATUSES_CLOSED,
    Job,
    NotificationSetting,
    NotificationTypeEnum,
    ProposalStatus,
    OrganizationProposalStatus,
    Contract,
    ContractStatus,
    ProposalInterview,
    ProposalComment,
    get_proposal_comment,
    ProposalCommentTypes,
    CandidateFile,
    JobFile,
    User,
    LegalAgreement,
    LONGLIST_PROPOSAL_STATUS_GROUPS,
    CareerSiteJobPosting,
)


@receiver(pre_save, sender=Client)
def client_changed(sender, instance, **kwargs):
    if is_career_site_being_disabled(instance):
        CareerSiteJobPosting.public_objects.filter(
            poly_relation_filter('job__org_id', 'job__org_content_type', instance),
        ).update(is_enabled=False)


def is_career_site_being_disabled(new_client):
    if new_client.is_career_site_enabled:
        return False

    client = Client.objects.filter(pk=new_client.pk).first()

    if client is None or not client.is_career_site_enabled:
        return False

    return True


@receiver(post_save, sender=CandidateFile)
def candidate_file_saved(sender, instance, created, **kwargs):
    if created:
        create_candidate_file_preview_and_thumbnail.delay(instance.pk)


@receiver(post_save, sender=JobFile)
def job_file_saved(sender, instance, created, **kwargs):
    if created:
        convert_job_file.delay(instance.pk)


@receiver(post_save, sender=ProposalInterview)
def invite_candidate_to_interview(sender, instance, created, **kwargs):
    # TODO(ZOO-): Interviews
    return
    if created:
        proposal = instance.proposal
        candidate = proposal.candidate
        user = instance.created_by

        send_email(
            candidate.email,
            'candidate_interview_invitation',
            context={
                'job': proposal.job.title,
                'candidate': candidate.name,
                'user': user.full_name,
                'organisation': user.profile.org.name,
                'uuid': instance.public_uuid,
                'base_url': settings.BASE_URL,
            },
            extension='html',
        )
        ProposalComment.objects.create(
            author=user,
            proposal=proposal,
            public=True,
            **get_proposal_comment(ProposalCommentTypes.INTERVIEW_CREATED),
        )


def create_default_proposal_statuses(instance, created):
    if not created:
        return

    statuses = ProposalStatus.objects.filter(default=True).exclude(
        group__in=LONGLIST_PROPOSAL_STATUS_GROUPS
    )

    for status in statuses:
        org_status = OrganizationProposalStatus(
            status=status, order=status.default_order
        )
        org_status.organization = instance
        org_status.save()


@receiver(post_save, sender=Client)
def create_default_client_proposal_statuses(sender, instance, created, **kwargs):
    create_default_proposal_statuses(instance, created)


@receiver(post_save, sender=Agency)
def create_default_agency_proposal_statuses(sender, instance, created, **kwargs):
    create_default_proposal_statuses(instance, created)


@receiver(pre_save, sender=Contract)
def contract_changed(sender, instance, **kwargs):
    """Send notification if contract has been initiated"""
    # Previous state of the contract
    contract = Contract.objects.filter(pk=instance.pk).first()

    if not contract:
        return

    have_been_signed_once = (
        not contract.is_client_signed
        and contract.is_client_signed == contract.is_agency_signed
        and instance.is_client_signed != instance.is_agency_signed
    )

    if have_been_signed_once:
        notify_contract_signed_by_one_party(
            None, contract, to_agency=instance.is_client_signed
        )

    if contract.status != instance.status:
        if instance.status in [ContractStatus.PENDING.key, ContractStatus.REJECTED.key]:
            notify_contract_invitation(None, instance)

        elif instance.status == ContractStatus.EXPIRED.key:
            notify_removed_job_access(None, contract)

        elif instance.status == ContractStatus.INITIATED.key:
            notify_contract_initiated(None, instance)


@receiver(post_save, sender=User)
def create_default_notification_settings(sender, instance, created, **kwargs):
    if created:
        for n, _ in NotificationTypeEnum.get_group_choices():
            NotificationSetting.objects.get_or_create(
                user=instance, notification_type_group=n,
            )


@receiver(post_delete, sender=LegalAgreement)
@receiver(post_save, sender=LegalAgreement)
def update_user_legal_agreement_status(sender, instance, **kwargs):
    """Update users' agreement status if there's a new or no legal agreements"""
    hash = LegalAgreement.latest_objects.get_hash()
    if hash:
        User.objects.exclude(legal_agreement_hash=hash).update(
            is_legal_agreed=False, legal_agreement_hash=hash
        )
    else:
        User.objects.update(is_legal_agreed=True, legal_agreement_hash=hash)


@receiver(post_save, sender=Job)
def close_job_postings(sender, instance, **kwargs):
    if instance.status in JOB_STATUSES_CLOSED:
        if hasattr(instance, 'private_posting'):
            instance.private_posting.public_uuid = None
            instance.private_posting.save()
        if hasattr(instance, 'career_site_posting'):
            instance.career_site_posting.is_enabled = False
            instance.career_site_posting.save()
