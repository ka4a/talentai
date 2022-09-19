from django.db import models, migrations, transaction

from core.models import ProposalDealStages, PROPOSAL_STATUS_GROUP_CHOICES

INTERVIEWING_GROUP = 'interviewing'
OLD_SECOND_INTERVIEW_NAME = 'Interviewing'
NEW_SECOND_INTERVIEW_NAME = 'Second interview'
THIRD_INTERVIEW_NAME = 'Third interview'
INTERVIEW_DEAL_STAGE = ProposalDealStages.INTERMEDIATE_ROUND.key


def apply_new_proposal_statuses(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    ContentType = apps.get_model('contenttypes', 'ContentType')
    ProposalStatus = apps.get_model('core', 'ProposalStatus')
    OrganizationProposalStatus = apps.get_model('core', 'OrganizationProposalStatus')
    Client = apps.get_model('core', 'Client')
    Agency = apps.get_model('core', 'Agency')

    # Rename Interviewing status
    SECOND_INTERVIEW_STATUS = (
        ProposalStatus.objects.using(db_alias)
        .filter(group=INTERVIEWING_GROUP, status_en=OLD_SECOND_INTERVIEW_NAME)
        .order_by('default_order')
        .first()
    )
    SECOND_INTERVIEW_STATUS.status_en = NEW_SECOND_INTERVIEW_NAME
    SECOND_INTERVIEW_STATUS.save()

    # Update Proposal status orders
    ProposalStatus.objects.using(db_alias).filter(
        default=True, default_order__gt=SECOND_INTERVIEW_STATUS.default_order
    ).update(default_order=models.F('default_order') + 1)

    # Create Third Interview status
    THIRD_INTERVIEW_STATUS = ProposalStatus.objects.using(db_alias).create(
        default=True,
        group=INTERVIEWING_GROUP,
        deal_stage=INTERVIEW_DEAL_STAGE,
        status_en=THIRD_INTERVIEW_NAME,
        default_order=SECOND_INTERVIEW_STATUS.default_order + 1,
    )

    # Add Third interview to all Organizations
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
                status=SECOND_INTERVIEW_STATUS
            ).first()

            # Update status order for every specific Organization
            org_statuses.filter(order__gt=status_to_shift_from.order).update(
                order=models.F('order') + 1
            )
            OrganizationProposalStatus.objects.using(db_alias).create(
                org_content_type=org_type,
                org_id=org_id,
                status=THIRD_INTERVIEW_STATUS,
                order=status_to_shift_from.order + 1,
            )

    # apply tenth orders to Proposal Statuses
    status_groups = [
        status['group']
        for status in list(
            ProposalStatus.objects.using(db_alias)
            .filter(default=True)
            .values('group')
            .annotate(min_order=models.Min('default_order'))
            .order_by('min_order')
        )
    ]
    base_order = 10
    for group in status_groups:
        # get all statuses that are belongs to the specific group
        grouped_statuses = (
            ProposalStatus.objects.using(db_alias)
            .filter(group=group)
            .order_by('default_order')
        )

        # update statuses by group
        for i in range(len(grouped_statuses)):
            status = grouped_statuses[i]
            status_order = base_order + i

            status.default_order = status_order
            status.save()

        base_order += 10

    # apply tenth orders to Organization Proposal Statuses
    status_groups = [
        status['status__group']
        for status in list(
            OrganizationProposalStatus.objects.using(db_alias)
            .values('status__group')
            .annotate(min_order=models.Min('order'))
            .order_by('min_order')
        )
    ]

    for org_type, org_id in organizations:
        with transaction.atomic():
            base_order = 10
            for group in status_groups:

                # get all statuses that are belongs to the specific group
                grouped_statuses = (
                    OrganizationProposalStatus.objects.using(db_alias)
                    .filter(
                        status__group=group, org_id=org_id, org_content_type=org_type
                    )
                    .order_by('order')
                )

                # update statuses by group
                for i in range(len(grouped_statuses)):
                    status = grouped_statuses[i]
                    status_order = base_order + i

                    status.order = status_order
                    status.save()

                base_order += 10


def revert_new_proposal_statuses(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    ContentType = apps.get_model('contenttypes', 'ContentType')
    ProposalStatus = apps.get_model('core', 'ProposalStatus')
    OrganizationProposalStatus = apps.get_model('core', 'OrganizationProposalStatus')
    Client = apps.get_model('core', 'Client')
    Agency = apps.get_model('core', 'Agency')

    # Rename Interviewing status back
    SECOND_INTERVIEW_STATUS = (
        ProposalStatus.objects.using(db_alias)
        .filter(group=INTERVIEWING_GROUP, status_en=NEW_SECOND_INTERVIEW_NAME)
        .order_by('default_order')
        .first()
    )
    SECOND_INTERVIEW_STATUS.status_en = OLD_SECOND_INTERVIEW_NAME
    SECOND_INTERVIEW_STATUS.save()

    THIRD_INTERVIEW_STATUS = (
        ProposalStatus.objects.using(db_alias)
        .filter(default=True, status_en=THIRD_INTERVIEW_NAME, group=INTERVIEWING_GROUP,)
        .order_by('default_order')
        .first()
    )

    # Revert Proposal status orders
    ProposalStatus.objects.using(db_alias).filter(
        default=True, default_order__gte=THIRD_INTERVIEW_STATUS.default_order
    ).update(default_order=models.F('default_order') - 1)

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
                status=THIRD_INTERVIEW_STATUS
            ).first()

            # Revert status order for every specific Organization
            org_statuses.filter(order__gt=status_unshift_to.order).update(
                order=models.F('order') - 1
            )

            status_unshift_to.delete()

    # Delete third interview status
    THIRD_INTERVIEW_STATUS.delete()

    # revert tenth orders
    proposal_statuses = ProposalStatus.objects.using(db_alias).order_by('default_order')
    for i in range(len(proposal_statuses)):
        status = proposal_statuses[i]
        status.default_order = i + 1
        status.save()

    for org_type, org_id in organizations:
        with transaction.atomic():
            org_proposal_statuses = (
                OrganizationProposalStatus.objects.using(db_alias)
                .filter(org_id=org_id, org_content_type=org_type)
                .order_by('order')
            )
            for i in range(len(org_proposal_statuses)):
                status = org_proposal_statuses[i]
                status.order = i + 1
                status.save()


class Migration(migrations.Migration):
    dependencies = [('core', '0155_apply_deal_proposal_stages')]

    operations = [
        migrations.RunPython(apply_new_proposal_statuses, revert_new_proposal_statuses)
    ]
