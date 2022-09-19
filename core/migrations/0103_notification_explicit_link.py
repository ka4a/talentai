# Generated by Django 2.2.2 on 2019-09-05 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0102_client_job_related_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='explicit_link',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='verb',
            field=models.CharField(
                choices=[
                    ('candidate_proposed_for_job', 'Candidate submitted for a job'),
                    ('client_assigned_agency_for_job', 'Client assigns your agency to a job'),
                    ('client_assigned_recruiter_for_job', 'Client assigns you to a job'),
                    ('client_changed_proposal_status', 'Client changes status of a submitted candidate'),
                    ('client_created_contract', 'Client creates a contract with your agency'),
                    ('client_updated_job', 'Client updates a job'),
                    ('contract_initiated_agency', 'Your contract with the client has been initiated.'),
                    ('contract_initiated_client', 'Your contract with the agency has been initiated.'),
                    ('contract_invitation_accepted', 'Agency accepted invitation'),
                    ('contract_invitation_declined', 'Agency declined invitation'),
                    ('contract_job_access_revoked_invite_ignored', 'Job access has been removed'),
                    ('contract_job_access_revoked_no_agreement', 'Job access has been removed'),
                    ('contract_signed_by_one_party', 'Contract is signed by one of the parties'),
                    ('proposal_moved', 'Candidate is reallocated to a different job'),
                    ('talent_assigned_manager_for_job', 'Talent Associate assigns you to a job')
                ],
                max_length=255
            ),
        ),
    ]