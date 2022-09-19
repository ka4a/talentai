import tempfile
from datetime import timedelta, datetime
from unittest.mock import patch
from unittest import skip
from os import path

from django.conf import settings
from django.core.files import File
from django.test import TestCase, override_settings
from django.utils import timezone

from core import models as m, fixtures as f
from core.converter import PDFConverter
from core.tasks import (
    remove_unactivated_accounts,
    convert_resume,
    convert_job_file,
    create_candidate_file_preview_and_thumbnail,
    set_pending_feedback_status,
    notify_of_pending_fees,
)

remove_after_hours_td = timedelta(
    hours=settings.REMOVE_UNACTIVATED_ACCOUNTS_AFTER_HOURS
)

dummy_pdf_name = 'pdffile'
dummy_pdf_path = path.join(
    settings.BASE_DIR, f'core/tests/dummies/{dummy_pdf_name}.pdf'
)


@skip("TODO(Z00-715)")
class SetPendingFeedbackStatusTask(TestCase):
    def test_switch(self):
        contract = f.create_contract(f.create_agency(), f.create_client())
        job = f.create_contract_job(contract)
        user = contract.agency.primary_contact
        future = timezone.now() + timedelta(hours=1)
        past = datetime(2010, 1, 1, tzinfo=timezone.utc)

        def create_proposal(
            interview_end_at=None,
            status_group='pending_interview',
            stage='longlist',
            interview_status=m.ProposalInterviewSchedule.Status.SCHEDULED,
        ):
            _proposal = f.create_proposal_with_candidate(job, user, stage=stage)
            _proposal.set_status_by_group(status_group, user, to_history=True)
            _proposal.save()
            if interview_end_at:
                start_at = interview_end_at - timedelta(hours=1)
                f.create_proposal_interview(
                    _proposal,
                    user,
                    start_at=start_at,
                    end_at=interview_end_at,
                    status=interview_status,
                )

            return _proposal

        proposals = {
            'future_interview': create_proposal(future),
            'past_interview': create_proposal(past),
            'not_confirmed': create_proposal(),
            'not_interested': create_proposal(past, 'not_interested'),
            'shortlist': create_proposal(past, stage='shortlist'),
            'no_interview': create_proposal(),
        }

        proposal_id_to_label = {proposals[key].id: key for key in proposals}

        set_pending_feedback_status()

        queryset = m.Proposal.objects.filter(
            status__group='pending_feedback',
            status_history__status__group='pending_feedback',
        )
        expected_labels = {'past_interview'}
        labels = {
            proposal_id_to_label[proposal.id]
            for proposal in queryset
            if proposal.id in proposal_id_to_label
        }
        self.assertSetEqual(expected_labels, labels)
        self.assertEqual(queryset.count(), len(expected_labels))


class RemoveUnactivatedAccountsTaskTestCase(TestCase):
    def create_and_test_removed(self, is_activated, date_joined):
        u = f.create_user('test@test.com')
        u.is_activated = is_activated
        u.date_joined = date_joined
        u.save()

        remove_unactivated_accounts()

        try:
            u.refresh_from_db()
        except m.User.DoesNotExist:
            return True

        return False

    def test_remove(self):
        """Should remove unactivated account after X hours."""
        self.assertTrue(
            self.create_and_test_removed(
                is_activated=False,
                date_joined=(
                    timezone.now() - remove_after_hours_td - timedelta(minutes=1)
                ),
            )
        )

    def test_not_remove(self):
        """Should not remove unactivated account before X hours."""
        self.assertFalse(
            self.create_and_test_removed(
                is_activated=False,
                date_joined=(
                    timezone.now() - remove_after_hours_td + timedelta(minutes=1)
                ),
            )
        )

    def test_activated(self):
        """Should not remove activated account."""
        self.assertFalse(
            self.create_and_test_removed(
                is_activated=True,
                date_joined=(
                    timezone.now() - remove_after_hours_td - timedelta(minutes=1)
                ),
            )
        )

    @patch('core.tasks.PDFConverter.convert')
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_convert_resume(self, convert):
        """The task should call PDFConverter.convert()"""

        file = File(open(dummy_pdf_path, 'rb'))

        convert.return_value = [file, dummy_pdf_name, 'pdf']

        c = f.create_candidate(f.create_agency())

        c.resume.save(dummy_pdf_name, file)
        convert_resume(c.pk)

        convert.assert_called_once_with(c.resume)

    @staticmethod
    def get_dummy_file(filename):
        return File(open(dummy_pdf_path, 'rb'))

    def get_convert_return_values(self, filename):
        name, ext = filename.split('.')
        return (
            self.get_dummy_file(filename),
            name,
            ext,
        )

    def get_create_thumbnail_return_values(self, filename):
        name, ext = filename.split('.')
        return self.get_dummy_file(filename), name

    def get_name_and_file(self, filename):
        return filename, self.get_dummy_file(filename)

    @patch('core.tasks.PDFConverter.convert')
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_convert_job_file(self, convert):
        """The task should call PDFConverter.convert()"""

        convert.return_value = self.get_convert_return_values('pdffile.pdf')

        job = f.create_job(f.create_client())
        job_file = m.JobFile.objects.create(job=job)
        job_file.file.save(*self.get_name_and_file('docxfile.docx'))

        convert_job_file(job_file.id)

        PDFConverter.convert.assert_called_once_with(job_file.file)

    # muting signal to prevent it from calling task
    @patch('core.signals.create_candidate_file_preview_and_thumbnail.delay')
    @patch('core.tasks.PDFConverter.create_thumbnail')
    @patch('core.tasks.PDFConverter.convert')
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_create_candidate_file_preview_and_thumbnail(
        self, convert, create_thumbnail, delay
    ):
        """The task should call PDFConverter.convert()"""

        convert.return_value = self.get_convert_return_values('pdffile.pdf')
        create_thumbnail.return_value = self.get_create_thumbnail_return_values(
            'thumbnail.jpg'
        )

        client = f.create_client()
        file_record = m.CandidateFile()
        file_record.organization = client
        file_record.candidate = f.create_candidate(client)
        file_record.file.save(*self.get_name_and_file('docxfile.docx'))
        file_record.save()

        create_candidate_file_preview_and_thumbnail(file_record.pk)

        create_thumbnail.assert_called_once()
        convert.assert_called_once_with(file_record.file)

    @patch('core.tasks.notify_fee_pending')
    def test_notify_of_pending_candidate_placements(self, notify):
        agency = f.create_agency()
        client = f.create_client()
        f.create_contract(agency, client)
        user = agency.primary_contact
        job = f.create_job(client, client=client)
        job.assign_agency(agency)

        def create_placement(status=m.FeeStatus.PENDING.key):
            return f.create_fee(
                proposal=f.create_proposal_with_candidate(job, user),
                created_by=user,
                agency=agency,
                status=status,
                submitted_by=user,
            )

        placements = [create_placement() for i in range(3)]

        for status in m.FeeStatus:
            if status.key != m.FeeStatus.PENDING.key:
                create_placement(status.key)

        notify_of_pending_fees()

        self.assertEqual(notify.call_count, len(placements))

        for placement in placements:
            notify.assert_any_call(None, placement, is_reminder=True)
