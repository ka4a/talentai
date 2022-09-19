# Generated by Django 2.2.9 on 2020-02-10 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0137_unique_candidate_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='email_client_assigned_recruiter_for_job',
            new_name='email_agency_assigned_member_for_job',
        ),
        migrations.AlterField(
            model_name='notification',
            name='verb',
            field=models.CharField(
                choices=[
                    (
                        'agency_assigned_member_for_job',
                        'Your agency assigns you to a job',
                    ),
                    ('candidate_longlisted_for_job', 'Candidate longlisted for a job'),
                    (
                        'candidate_shortlisted_for_job',
                        'Candidate shortlisted for a job',
                    ),
                    (
                        'client_assigned_agency_for_job',
                        'Client assigns your agency to a job',
                    ),
                    (
                        'client_changed_proposal_status',
                        'Client changes status of a submitted candidate',
                    ),
                    (
                        'client_created_contract',
                        'Client creates a contract with your agency',
                    ),
                    ('client_updated_job', 'Client updates a job'),
                    (
                        'contract_initiated_agency',
                        'Your contract with the client has been initiated.',
                    ),
                    (
                        'contract_initiated_client',
                        'Your contract with the agency has been initiated.',
                    ),
                    ('contract_invitation_accepted', 'Agency accepted invitation'),
                    ('contract_invitation_declined', 'Agency declined invitation'),
                    (
                        'contract_job_access_revoked_invite_ignored',
                        'Job access has been removed',
                    ),
                    (
                        'contract_job_access_revoked_no_agreement',
                        'Job access has been removed',
                    ),
                    (
                        'contract_signed_by_one_party',
                        'Contract is signed by one of the parties',
                    ),
                    ('job_is_filled', 'Job is filled up'),
                    (
                        'proposal_appointment_confirmed',
                        'Proposal appointment confirmed',
                    ),
                    (
                        'proposal_appointment_confirmed_proposer',
                        'Proposal appointment confirmed',
                    ),
                    ('proposal_appointment_rejected', 'Proposal appointment rejected'),
                    ('proposal_moved', 'Candidate is reallocated to a different job'),
                    (
                        'talent_assigned_manager_for_job',
                        'Talent Associate assigns you to a job',
                    ),
                ],
                max_length=255,
            ),
        ),
    ]