# Generated by Django 2.1.7 on 2019-04-06 12:48

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


GROUPS = ['Recruiters', 'Agency Administrators', 'Agency Managers']


def add_proposal_change_permission(apps, schema_editor):
    """Add Proposal Change Permissions."""
    db_alias = schema_editor.connection.alias

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    p = Permission.objects.using(db_alias).filter(
        codename='change_proposal'
    ).first()

    groups = Group.objects.using(db_alias).filter(name__in=GROUPS).all()
    for group in groups:
        group.permissions.add(p)


def remove_proposal_change_permission(apps, schema_editor):
    """Remove Proposal Change Permissions."""
    db_alias = schema_editor.connection.alias

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    p = Permission.objects.using(db_alias).filter(
        codename='change_proposal'
    ).first()

    groups = Group.objects.using(db_alias).filter(
        name__in=GROUPS,
        permissions=p
    ).all()

    for group in groups:
        group.permissions.remove(p)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0064_linkedin'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposal',
            name='moved_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='moved_proposals', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='proposal',
            name='moved_from_job',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='moved_proposals', to='core.Job'),
        ),
        migrations.AddField(
            model_name='user',
            name='email_proposal_moved',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='verb',
            field=models.CharField(choices=[('agency_proposed_candidate_for_job', 'Agency submits a candidate for a job'), ('client_assigned_agency_for_job', 'Client assigns your agency to a job'), ('client_assigned_recruiter_for_job', 'Client assigns you to a job'), ('client_changed_proposal_status', 'Client changes status of a submitted candidate'), ('client_created_contract', 'Client creates a contract with your agency'), ('client_updated_job', 'Client updates a job'), ('proposal_moved', 'Candidate is reallocated to a different job'), ('talent_assigned_manager_for_job', 'Talent Associate assigns you to a job')], max_length=255),
        ),
        migrations.RunPython(
            add_proposal_change_permission, remove_proposal_change_permission
        ),
    ]
