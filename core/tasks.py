from datetime import timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from cloudconvert.exceptions import APIError
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from core import models as m
from core.converter import (
    PDFConverter,
    InputFileError,
    ExtensionError,
    FileAlreadyHasRequiredFormat,
)
from core.notifications import notify_fee_pending

logger = get_task_logger(__name__)


@shared_task
def send_email(*args, **kwargs):
    html_body = kwargs.pop('html_body', None)

    msg = EmailMultiAlternatives(**kwargs)

    if html_body:
        msg.attach_alternative(html_body, 'text/html')

    msg.send()


@shared_task
def remove_unactivated_accounts():
    td = timedelta(hours=settings.REMOVE_UNACTIVATED_ACCOUNTS_AFTER_HOURS)

    users_to_remove = m.User.objects.filter(
        is_activated=False, date_joined__lt=timezone.now() - td
    ).all()

    removed = []

    for user in users_to_remove:
        r = user.delete()
        removed.append((user.email, r))

    logger.info('Removed unactivated users: {}'.format(removed))


class FileInstanceAdapter:
    def __init__(
        self, model, pk, file_attribute='file', thumbnail_attribute='thumbnail'
    ):
        self.pk = pk
        self.instance = model.objects.get(pk=pk)
        self.file_attribute = file_attribute
        self.thumbnail_attribute = thumbnail_attribute

    @property
    def file(self):
        return getattr(self.instance, self.file_attribute)

    @property
    def thumbnail(self):
        return getattr(self.instance, self.thumbnail_attribute)

    def refresh_from_db(self):
        self.instance.refresh_from_db()

    def save(self):
        self.instance.save()


def convert_instance_file(instance, create_thumbnail_task):
    try:
        original_file = instance.file
        if not original_file:
            return

        content, filename, ext = PDFConverter.convert(original_file)

        if field_have_changed(instance, 'file'):
            return

        instance.file.delete()
        instance.thumbnail.delete()

        instance.file.save(filename, content)
        instance.save()

        create_thumbnail_task.delay(
            instance.pk, ext, instance.file_attribute, instance.thumbnail_attribute
        )

    except FileAlreadyHasRequiredFormat:
        if instance.file.name.endswith('.pdf'):
            create_thumbnail_task.delay(
                instance.pk,
                'pdf',
                instance.file_attribute,
                instance.thumbnail_attribute,
            )

    except (InputFileError, ExtensionError) as error:
        logger.error(error)


@shared_task(
    autoretry_for=(APIError,), retry_kwargs={"max_retries": 5}, retry_backoff=60
)
def convert_resume(candidate_pk):
    convert_instance_file(
        FileInstanceAdapter(m.Candidate, candidate_pk, 'resume', 'resume_thumbnail'),
        create_resume_thumbnail,
    )
    convert_instance_file(
        FileInstanceAdapter(
            m.Candidate, candidate_pk, 'resume_ja', 'resume_ja_thumbnail'
        ),
        create_resume_thumbnail,
    )
    convert_instance_file(
        FileInstanceAdapter(m.Candidate, candidate_pk, 'cv_ja', 'cv_ja_thumbnail'),
        create_resume_thumbnail,
    )


@shared_task(
    autoretry_for=(APIError,), retry_kwargs={"max_retries": 5}, retry_backoff=60
)
def convert_job_file(job_file_pk):
    convert_instance_file(
        FileInstanceAdapter(m.JobFile, job_file_pk), create_job_file_thumbnail,
    )


def field_have_changed(instance, attr):
    original_field = getattr(instance, attr)
    instance.refresh_from_db()
    current_field = getattr(instance, attr)

    return current_field != original_field


def convert_file(
    instance, in_attr='file', out_attr='file', convert=PDFConverter.convert
):
    original_file = getattr(instance, in_attr)
    if not original_file:
        return
    try:
        try:
            file_data = convert(original_file)

            if field_have_changed(instance, in_attr):
                return

            to_overwrite = getattr(instance, out_attr)
            to_overwrite.delete()
            to_overwrite.save(file_data[1], file_data[0])
            instance.save()

        except FileAlreadyHasRequiredFormat:
            if out_attr == in_attr or field_have_changed(instance, in_attr):
                return

            to_overwrite = getattr(instance, out_attr)
            to_overwrite.delete()

            setattr(instance, out_attr, original_file)
            instance.save()

    except (InputFileError, ExtensionError) as error:
        logger.info(error)


@shared_task(
    autoretry_for=(APIError,), retry_kwargs={"max_retries": 5}, retry_backoff=60
)
def create_candidate_file_preview_and_thumbnail(pk):
    instance = m.CandidateFile.objects.get(pk=pk)
    old_preview = instance.preview

    convert_file(instance, 'file', 'preview', PDFConverter.convert)

    if instance.preview and instance.preview != old_preview:
        convert_file(instance, 'preview', 'thumbnail', PDFConverter.create_thumbnail)


def create_thumbnail(instance, ext):
    if ext != 'pdf':
        return

    try:
        original_file = instance.file
        if not original_file:
            return

        content, filename = PDFConverter.create_thumbnail(original_file)

        instance.refresh_from_db()
        # Exit if file was replace or removed before convert was ended
        if instance.file != original_file:
            return

        instance.thumbnail.save(filename, content)
        instance.save()

    except InputFileError as error:
        logger.info(error)
    except ExtensionError as error:
        logger.info(error)


@shared_task(
    autoretry_for=(APIError,), retry_kwargs={"max_retries": 5}, retry_backoff=60
)
def create_resume_thumbnail(candidate_pk, ext, field_name, thumbnail_field_name):
    create_thumbnail(
        FileInstanceAdapter(
            m.Candidate, candidate_pk, field_name, thumbnail_field_name
        ),
        ext,
    )


@shared_task(
    autoretry_for=(APIError,), retry_kwargs={"max_retries": 5}, retry_backoff=60
)
def create_job_file_thumbnail(job_file_pk, ext, *args, **kwargs):
    create_thumbnail(
        FileInstanceAdapter(m.JobFile, job_file_pk), ext,
    )


@shared_task
def mark_expired_contracts():
    """Set's status as expired for all expired invitations"""
    marked = []

    for contract in m.Contract.objects.filter(
        status__in=m.CONTRACT_STATUSES_CAN_EXPIRE,
    ):
        if contract.days_until_invitation_expire <= 0:
            contract.status = m.ContractStatus.EXPIRED.key
            contract.save()
            marked.append(str(contract))

    logger.info('Set status as expired for contracts: {}'.format(marked))


@shared_task
def update_currency_rates(backend=settings.EXCHANGE_BACKEND, **kwargs):
    backend = import_string(backend)()
    backend.update_rates()


@shared_task
def notify_of_pending_fees(**kwargs):
    queryset = m.Fee.objects.filter(status=m.FeeStatus.PENDING.key)
    for placement in queryset:
        notify_fee_pending(None, placement, is_reminder=True)


@shared_task
def set_pending_feedback_status(**kwargs):
    # TODO(ZOO-715)
    # status becomes COMPLETED_INTERVIEW_WAITING_FOR_FEEDBACK
    # query group
    # pending_feedback_status = m.ProposalStatus.objects.filter(
    #     group='pending_feedback'
    # ).first()

    # if not pending_feedback_status:
    #     raise m.ProposalStatus.DoesNotExist(
    #         message='Status with group pending_feedback is not found'
    #     )

    # current_time = timezone.now()

    # queryset = m.Proposal.objects.filter(
    #     status__group='interview',
    #     interviews__end_at__lt=current_time,
    #     interviews__status=m.ProposalInterviewStatus.SCHEDULED.key,
    #     stage='longlist',
    # )

    # for proposal in queryset:
    #     proposal.update_status_history(pending_feedback_status, None)

    # queryset.update(status=pending_feedback_status)
    pass


@shared_task
def set_invoice_overdue(**kwargs):
    m.Fee.objects.filter(
        invoice_status=m.InvoiceStatus.SENT.key, invoice_due_date__lt=timezone.now(),
    ).update(invoice_status=m.InvoiceStatus.OVERDUE.key)


@shared_task
def email_public_candidate_application_confirmation(proposal_id):
    proposal = m.Proposal.objects.get(pk=proposal_id)
    job = proposal.job
    candidate = proposal.candidate
    attached_files = candidate.files.all()
    context = dict(
        client=job.client.name,
        job=job.title,
        candidate=candidate.name,
        email=candidate.email,
        phone=candidate.phone or _('(Empty)'),
        cv=candidate.resume_file_name or _('(Empty)'),
        attached_files=', '.join([file.file_name for file in attached_files])
        if attached_files
        else _('(Empty)'),
        job_url=settings.BASE_URL + reverse('job', kwargs={'job_id': job.id}),
        proposal_url=settings.BASE_URL
        + reverse(
            'proposal_page', kwargs={'job_id': job.id, 'proposal_id': proposal.id}
        ),
    )

    folder = 'candidate_public_application_confirmed'
    recipient_subfolder = [
        (candidate.email, 'to_candidate'),
    ]
    for recipient, subfolder in recipient_subfolder:
        send_email_kwargs = dict(
            to=[recipient],
            subject=render_to_string(f'{folder}/{subfolder}/subject.txt', context,),
            body=render_to_string(f'{folder}/{subfolder}/body.txt', context,),
        )
        send_email.delay(**send_email_kwargs)
