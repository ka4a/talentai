# Generated by Django 2.2.17 on 2021-02-19 10:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0227_rename_appointment_tables'),
    ]

    operations = [
        migrations.RenameField(
            model_name='interviewtemplate',
            old_name='appointment_type',
            new_name='interview_type',
        ),
        migrations.RenameField(
            model_name='jobinterviewtemplate',
            old_name='appointment_type',
            new_name='interview_type',
        ),
        migrations.RenameField(
            model_name='proposalinterview',
            old_name='appointment_type',
            new_name='interview_type',
        ),
        migrations.RenameField(
            model_name='proposalinterview',
            old_name='is_current_appointment',
            new_name='is_current_interview',
        ),
        migrations.RenameField(
            model_name='proposalinterviewinvite',
            old_name='appointment',
            new_name='interview',
        ),
        migrations.RenameField(
            model_name='proposalinterviewtimeslot',
            old_name='appointment',
            new_name='interview',
        ),
        migrations.AlterField(
            model_name='jobinterviewtemplate',
            name='interviewer',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='interview_templates',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='jobinterviewtemplate',
            name='job',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='interview_templates',
                to='core.Job',
            ),
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
                    ('fee_approved', 'Fee is approved'),
                    ('fee_draft', 'Fee is set as draft'),
                    ('fee_needs_revision', 'Fee is sent to revision'),
                    ('fee_pending', 'Fee is submitted for approval'),
                    ('fee_pending_reminder', 'Fee is waiting approval'),
                    ('job_is_filled', 'Job is filled up'),
                    ('placement_fee_approved', 'Candidate placement is approved'),
                    ('placement_fee_draft', 'Candidate placement is set as draft'),
                    (
                        'placement_fee_needs_revision',
                        'Candidate placement is sent to revision',
                    ),
                    (
                        'placement_fee_pending',
                        'Candidate placement is submitted for approval',
                    ),
                    (
                        'placement_fee_pending_reminder',
                        'Candidate placement is sent to revision',
                    ),
                    ('proposal_interview_confirmed', 'Proposal interview confirmed'),
                    (
                        'proposal_interview_confirmed_proposer',
                        'Proposal interview confirmed',
                    ),
                    ('proposal_interview_rejected', 'Proposal interview rejected'),
                    ('proposal_moved', 'Candidate is reallocated to a different job'),
                    (
                        'proposal_public_application_confirmed',
                        'Proposal new public application',
                    ),
                    (
                        'talent_assigned_manager_for_job',
                        'Talent Associate assigns you to a job',
                    ),
                    ('user_mentioned_in_comment', 'User is mentioned'),
                    (
                        'user_mentioned_in_comment_deleted',
                        'Comment mentioning user is deleted',
                    ),
                ],
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name='proposalinterview',
            name='interviewer',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='proposal_interviews',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='proposalinterview',
            name='proposal',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='interviews',
                to='core.Proposal',
            ),
        ),
    ]
