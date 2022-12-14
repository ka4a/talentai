# Generated by Django 2.2.8 on 2020-01-13 06:35

from django.conf import settings
from django.db import migrations, models
import django.db.migrations.operations.special
import django.db.models.deletion


def set_default_job_owner(apps, schema_editor):
    """Add Job File Permissions."""

    Job = apps.get_model('core', 'Job')

    for job in Job.objects.filter(owner__isnull=True):
        client = job.client

        if client.primary_contact:
            job.owner = client.primary_contact
        else:
            # if not primary contact defined,
            # we would assign member of related organisation
            # prioritising Talent Associates
            members = list(
                client.members.order_by('-talent_associate', 'date_joined')[:1]
            )
            if len(members) > 0:
                job.owner = members[0]

        if job.owner:
            job.save()
        else:
            raise Exception(
                f'Client {client} don\'t have any users to assign to a {job}'
            )


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0127_on_job_filled_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='owner',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='owned_jobs',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(
            code=set_default_job_owner,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='job',
            name='owner',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='owned_jobs',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
