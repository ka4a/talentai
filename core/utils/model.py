from django.utils import timezone

from core.models import FeeStatus, Fee
from core.notifications import notify_fee_status_change
from core.utils.common import create_invoice_number


def get_fee_status_update_and_notify(status, user=None, fee=None, update=None):
    new_values = {'status': status}
    if not fee or status != fee.status:
        if status == FeeStatus.APPROVED.key:
            new_values['approved_at'] = timezone.now()

            invoice_issuance_date = None
            submitted_by = user
            proposal = None

            if fee:
                invoice_issuance_date = fee.invoice_issuance_date
                submitted_by = fee.submitted_by or submitted_by
                if fee.placement:
                    proposal = fee.placement.proposal
                else:
                    proposal = fee.proposal

            if update:
                invoice_issuance_date = (
                    update.get('invoice_issuance_date') or invoice_issuance_date
                )
                proposal = update.get('proposal') or proposal

            if invoice_issuance_date:
                new_values['invoice_number'] = create_invoice_number(
                    last_order=Fee.objects.filter(
                        status=FeeStatus.APPROVED.key,
                    ).count(),
                    date=invoice_issuance_date,
                )

            if proposal and submitted_by:
                proposal.create_comment_placed(submitted_by)

        if status == FeeStatus.PENDING.key and user:
            new_values['submitted_by'] = user
            new_values['submitted_at'] = timezone.now()

        if fee and user:
            notify_fee_status_change(fee, user, status)

    return new_values
