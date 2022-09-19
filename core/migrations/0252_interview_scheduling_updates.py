# Generated by Django 2.2.19 on 2021-04-19 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0251_interview_update_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposalinterviewtimeslot',
            name='is_rejected',
            field=models.BooleanField(default=False),
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
                    ('client_changed_proposal_status', 'Application Status is Updated'),
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
                    (
                        'interview_proposal_confirmed_interviewer',
                        'Proposal interview confirmed',
                    ),
                    (
                        'interview_proposal_confirmed_proposer',
                        'Interview Proposal is Confirmed by Candidate',
                    ),
                    (
                        'interview_proposal_is_sent',
                        'Interview Proposal is Sent to Candidate',
                    ),
                    ('job_is_filled', 'Job is Filled up'),
                    (
                        'new_proposal_candidate_direct_application',
                        'Candidate is Added to Job - Direct Application',
                    ),
                    (
                        'new_proposal_candidate_recruiter',
                        'Candidate is Added to Job (excl. Direct Application)',
                    ),
                    ('new_proposal_candidate_sourced_by', 'Candidate is Added to Job'),
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
                    ('proposal_approved_rejected_by_hiring_manager', 'N/A'),
                    ('proposal_interview_rejected', 'Proposal interview rejected'),
                    ('proposal_is_rejected', 'Application is Rejected'),
                    ('proposal_moved', 'Candidate is reallocated to a different job'),
                    ('proposal_submitted_to_hiring_manager', 'N/A'),
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
            model_name='notificationsetting',
            name='notification_type_group',
            field=models.CharField(
                choices=[
                    ('candidate_is_added_to_job', 'Candidate is Added to Job'),
                    (
                        'candidate_is_added_to_job_direct_application',
                        'Candidate is Added to Job - Direct Application',
                    ),
                    (
                        'candidate_is_added_to_job_excl_direct_application',
                        'Candidate is Added to Job (excl. Direct Application)',
                    ),
                    ('client_changed_proposal_status', 'Application Status is Updated'),
                    (
                        'interview_proposal_is_confirmed',
                        'Interview Proposal is Confirmed by Candidate',
                    ),
                    (
                        'interview_proposal_is_sent',
                        'Interview Proposal is Sent to Candidate',
                    ),
                    ('job_is_filled', 'Job is Filled up'),
                    ('proposal_is_rejected', 'Application is Rejected'),
                ],
                max_length=255,
            ),
        ),
    ]
