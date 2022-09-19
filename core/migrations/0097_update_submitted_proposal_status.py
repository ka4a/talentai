from django.db import migrations


OLD_STATUS = 'Submitted'

NEW_STATUS = 'Pending review'


def update_default_submitted_status(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    ProposalStatus = apps.get_model('core', 'ProposalStatus')

    s = ProposalStatus.objects.using(db_alias).filter(
        status_en=OLD_STATUS
    ).first()
    s.status_en = NEW_STATUS
    s.save()


def revert_default_submitted_status(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    ProposalStatus = apps.get_model('core', 'ProposalStatus')

    s = ProposalStatus.objects.using(db_alias).filter(
        status_en=NEW_STATUS
    ).first()
    s.status_en = OLD_STATUS
    s.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0096_add_default_decline_reasons')
    ]

    operations = [
        migrations.RunPython(
            update_default_submitted_status,
            revert_default_submitted_status
        )
    ]
