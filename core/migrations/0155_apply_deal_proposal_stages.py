from django.db import migrations, models, transaction

from core.models import ProposalDealStages

FIRST_INTERVIEW_GROUP = 'interviewing'
FIRST_INTERVIEW_NAME = 'First interview'

MAP_DEFAULT_STATUSES_TO_PROPOSAL_DEAL_STAGES = {
    # Deal stage : [(group, status), ...]
    ProposalDealStages.FIRST_ROUND.key: [
        ('approved', 'CV Approved'),
        ('interviewing', FIRST_INTERVIEW_NAME),
    ],
    ProposalDealStages.INTERMEDIATE_ROUND.key: [('interviewing', 'Interviewing'),],
    ProposalDealStages.FINAL_ROUND.key: [('interviewing', 'Final Interview'),],
    ProposalDealStages.OFFER.key: [
        ('proceeding', 'Offer Prep'),
        ('offer', 'Offer Sent'),
        ('offer_accepted', 'Offer Accepted'),
    ],
}


def apply_deal_proposal_stages(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    ContentType = apps.get_model('contenttypes', 'ContentType')
    ProposalStatus = apps.get_model('core', 'ProposalStatus')
    OrganizationProposalStatus = apps.get_model('core', 'OrganizationProposalStatus')
    Client = apps.get_model('core', 'Client')
    Agency = apps.get_model('core', 'Agency')

    SHIFTED_DEFAULT_STATUS = (
        ProposalStatus.objects.using(db_alias)
        .filter(default=True, group=FIRST_INTERVIEW_GROUP)
        .order_by('default_order')
        .first()
    )

    # Update Proposal Status order
    ProposalStatus.objects.using(db_alias).filter(
        default_order__gte=SHIFTED_DEFAULT_STATUS.default_order
    ).update(default_order=models.F('default_order') + 1)

    # Create First Interview
    FIRST_INTERVIEW_STATUS = ProposalStatus.objects.using(db_alias).create(
        group=FIRST_INTERVIEW_GROUP,
        status_en=FIRST_INTERVIEW_NAME,
        default=True,
        default_order=SHIFTED_DEFAULT_STATUS.default_order,
    )

    # Add First Interview to all Organizations
    client_type = ContentType.objects.get_for_model(Client)
    agency_type = ContentType.objects.get_for_model(Agency)

    organizations = []

    organizations.extend([(client_type, client.pk) for client in Client.objects.all()])

    organizations.extend([(agency_type, agency.pk) for agency in Agency.objects.all()])

    for org_type, org_id in organizations:
        with transaction.atomic():
            org_statuses = OrganizationProposalStatus.objects.using(db_alias).filter(
                org_content_type=org_type, org_id=org_id
            )
            status_to_shift_from = org_statuses.filter(
                status=SHIFTED_DEFAULT_STATUS
            ).first()

            # Update status order for every specific Organization
            org_statuses.filter(order__gte=status_to_shift_from.order).update(
                order=models.F('order') + 1
            )
            OrganizationProposalStatus.objects.using(db_alias).create(
                org_content_type=org_type,
                org_id=org_id,
                status=FIRST_INTERVIEW_STATUS,
                order=status_to_shift_from.order,
            )

    for deal_stage, statuses in MAP_DEFAULT_STATUSES_TO_PROPOSAL_DEAL_STAGES.items():
        for group, status_en in statuses:
            ProposalStatus.objects.using(db_alias).filter(
                group=group, status_en=status_en
            ).update(deal_stage=deal_stage)


def revert_deal_proposal_stages(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    ContentType = apps.get_model('contenttypes', 'ContentType')
    ProposalStatus = apps.get_model('core', 'ProposalStatus')
    OrganizationProposalStatus = apps.get_model('core', 'OrganizationProposalStatus')
    Client = apps.get_model('core', 'Client')
    Agency = apps.get_model('core', 'Agency')

    FIRST_INTERVIEW_STATUS = (
        ProposalStatus.objects.using(db_alias)
        .filter(
            group=FIRST_INTERVIEW_GROUP, status_en=FIRST_INTERVIEW_NAME, default=True,
        )
        .first()
    )

    # Remove new Proposal Status from all organizations
    client_type = ContentType.objects.get_for_model(Client)
    agency_type = ContentType.objects.get_for_model(Agency)

    organizations = []

    organizations.extend([(client_type, client.pk) for client in Client.objects.all()])

    organizations.extend([(agency_type, agency.pk) for agency in Agency.objects.all()])

    for org_type, org_id in organizations:
        with transaction.atomic():
            org_statuses = OrganizationProposalStatus.objects.using(db_alias).filter(
                org_content_type=org_type, org_id=org_id
            )
            status_unshift_to = org_statuses.filter(
                status=FIRST_INTERVIEW_STATUS
            ).first()

            # Revert status order for every specific Organization
            org_statuses.filter(order__gt=status_unshift_to.order).update(
                order=models.F('order') - 1
            )

            status_unshift_to.delete()

    # Delete new Proposal Status
    FIRST_INTERVIEW_STATUS.delete()

    # Revert Proposal Status order
    ProposalStatus.objects.using(db_alias).filter(
        default_order__gt=FIRST_INTERVIEW_STATUS.default_order
    ).update(default_order=models.F('default_order') - 1)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0154_proposal_deal_stage'),
    ]
    operations = [
        migrations.RunPython(apply_deal_proposal_stages, revert_deal_proposal_stages),
    ]
