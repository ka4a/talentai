from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


def apply_candidate_additional_fields(apps, schema_editor):
    """
        Set default owners, creators and updaters.
        Client: Primary Contact
        Agency: Agency Administrator, then Agency Manager
    """

    Candidate = apps.get_model('core', 'Candidate')
    Client = apps.get_model('core', 'Client')
    Agency = apps.get_model('core', 'Agency')
    User = apps.get_model('core', 'User')

    candidates = Candidate.objects.all()

    for candidate in candidates:
        org = candidate.org_content_type.model

        if org == 'client':
            actor = Client.objects.get(pk=candidate.org_id).primary_contact
        else:
            agency = Agency.objects.get(pk=candidate.org_id)
            actor = (
                agency.primary_contact
                or User.objects.filter(agencyadministrator__agency=agency).first()
                or User.objects.filter(agencymanager__agency=agency).first()
            )

        candidate.owner = actor
        candidate.created_by = actor
        candidate.updated_by = actor
        candidate.save()


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0138_assign_member_notifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='owner',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='owned_candidates',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='candidate',
            name='created_by',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='created_candidates',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='candidate',
            name='updated_by',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='last_updated_candidates',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(
            apply_candidate_additional_fields, migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name='candidate',
            name='owner',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='owned_candidates',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='original',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='core.Candidate',
            ),
        ),
    ]
