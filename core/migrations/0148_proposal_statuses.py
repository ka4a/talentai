from django.db.migrations import Migration as BaseMigration, RunPython


def create_default_proposal_statuses(apps, schema_editor):
    OrganizationProposalStatus = apps.get_model('core', 'OrganizationProposalStatus')
    ProposalStatus = apps.get_model('core', 'ProposalStatus')
    Agency = apps.get_model('core', 'Agency')
    ContentTypes = apps.get_model('contenttypes', 'ContentType')

    agency_ctype = ContentTypes.objects.filter(
        app_label='core', model='agency',
    ).first()

    agencies = list(Agency.objects.all())
    statuses = list(ProposalStatus.objects.filter(default=True))
    for agency in agencies:
        for status in statuses:
            OrganizationProposalStatus.objects.create(
                status=status,
                org_id=agency.id,
                org_content_type=agency_ctype,
                order=status.default_order,
            )


def revert_create_default_proposal_statuses(apps, schema_editor):
    OrganizationProposalStatus = apps.get_model('core', 'OrganizationProposalStatus')
    ContentTypes = apps.get_model('contenttypes', 'ContentType')

    OrganizationProposalStatus.objects.filter(
        org_content_type=ContentTypes.objects.filter(
            app_label='core', model='agency'
        ).first(),
        status__default=True,
    ).delete()


class Migration(BaseMigration):
    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('core', '0147_job_organization_field'),
    ]

    operations = [
        RunPython(
            create_default_proposal_statuses, revert_create_default_proposal_statuses
        ),
    ]
