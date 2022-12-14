# Generated by Django 2.1.7 on 2019-04-28 17:59

from django.db import migrations


def add_client_declined_proposal_status(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    ProposalStatus = apps.get_model('core', 'ProposalStatus')
    ClientProposalStatus = apps.get_model('core', 'ClientProposalStatus')

    already_exists = ProposalStatus.objects.using(db_alias).filter(
        group='closed',
        status_en='Client declined',
        default=True,
    ).exists()

    if already_exists:
        return

    default_order = ProposalStatus.objects.using(db_alias).filter(
        default=True
    ).order_by(
        '-default_order'
    ).first().default_order + 1

    status_object = ProposalStatus.objects.using(db_alias).create(
        group='closed',
        status_en='Client declined',
        default=True,
        default_order=default_order
    )

    Client = apps.get_model('core', 'Client')

    for c in Client.objects.using(db_alias).all():
        order = ClientProposalStatus.objects.using(db_alias).filter(
            client=c
        ).order_by(
            '-order'
        ).first().order + 1

        ClientProposalStatus.objects.using(db_alias).create(
            client=c,
            status=status_object,
            order=order
        )


def remove_client_declined_proposal_status(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    ProposalStatus = apps.get_model('core', 'ProposalStatus')
    ClientProposalStatus = apps.get_model('core', 'ClientProposalStatus')

    s = ProposalStatus.objects.using(db_alias).filter(
        group='closed',
        status_en='Client declined',
        default=True,
    ).first()

    if not s:
        return

    ClientProposalStatus.objects.using(db_alias).filter(status=s).delete()
    s.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0065_moving_proposals'),
    ]

    operations = [
        migrations.RunPython(
            add_client_declined_proposal_status,
            remove_client_declined_proposal_status
        ),
    ]
