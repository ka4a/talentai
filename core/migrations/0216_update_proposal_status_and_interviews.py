# Generated by Django 2.2.17 on 2021-01-21 05:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0215_update_currencies'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposalappointment',
            name='is_current_appointment',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='proposalappointment',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('confirmed', 'Confirmed'),
                    ('rejected', 'Rejected'),
                    ('canceled', 'Canceled'),
                    ('completed', 'Completed'),
                ],
                default='pending',
                max_length=15,
            ),
        ),
        migrations.AlterField(
            model_name='proposalstatus',
            name='group',
            field=models.CharField(
                choices=[
                    ('associated_candidate_to_job', 'Associated Candidate to Job'),
                    ('interested_and_suitable', 'Interested and Suitable'),
                    ('contacted', 'Contacted'),
                    ('met_suitable', 'Met - Suitable'),
                    ('applied_by_candidate', 'Applied by Candidate'),
                    ('submitted_by_agent', 'Submitted by Agent'),
                    (
                        'submitted_by_internal_recruiter',
                        'Submitted by Internal Recruiter',
                    ),
                    ('submitted_by_referral', 'Submitted by Referral'),
                    ('submitted_to_client', 'Submitted to Client'),
                    ('submitted_to_hiring_manager', 'Submitted to Hiring Manager'),
                    ('on_hold', 'On Hold'),
                    ('on_hold_by_client', 'On Hold by Client'),
                    ('suitable', 'Suitable'),
                    ('approved_by_client', 'Approved by Client'),
                    ('scheduling_in_progress', 'Scheduling in Progress'),
                    ('confirmed_client_availability', 'Confirmed Client Availability'),
                    (
                        'confirmed_candidate_availability',
                        'Confirmed Candidate Availability',
                    ),
                    ('scheduled_interview', 'Scheduled Interview'),
                    (
                        'completed_interview_waiting_for_feedback',
                        'Completed Interview (waiting for feedback)',
                    ),
                    ('decided_to_offer', 'Decided to Offer'),
                    ('prepared_the_offer', 'Prepared the Offer'),
                    ('presented_the_offer', 'Presented the Offer'),
                    ('offer_accepted', 'Offer Accepted'),
                    ('pending_start_date', 'Pending Start Date'),
                    ('started', 'Started'),
                    ('no_show', 'No Show'),
                    ('probation_passed', 'Probation Passed'),
                    ('probation_not_passed', 'Probation Not Passed'),
                    (
                        'terminated_during_warranty_period',
                        'Terminated During Warranty Period',
                    ),
                    (
                        'terminated_during_probation_period',
                        'Terminated During Probation Period',
                    ),
                    (
                        'resigned_during_warranty_period',
                        'Resigned During Warranty Period',
                    ),
                    (
                        'resigned_during_probation_period',
                        'Resigned During Probation Period',
                    ),
                ],
                max_length=64,
            ),
        ),
        migrations.AlterField(
            model_name='proposalstatus',
            name='stage',
            field=models.CharField(
                choices=[
                    ('associated', 'Associated'),
                    ('pre_screening', 'Pre-Screening'),
                    ('submissions', 'Submissions'),
                    ('screening', 'Screening'),
                    ('interviewing', 'Interviewing'),
                    ('offering', 'Offering'),
                    ('hired', 'Hired'),
                ],
                max_length=32,
            ),
        ),
    ]
