# Generated by Django 2.2.17 on 2020-11-23 13:18

from django.db import migrations


STAGE_STATUS_ORG_QUICK_ACTION_MAPPING = {
    'associated': {
        'associated_candidate_to_job': {
            'client': [
                (
                    'change_status',
                    'Submit to Hiring Manager',
                    'submissions',
                    'submitted_to_hiring_manager',
                ),
                ('reject', 'Reject Candidate', None, None),
            ],
            'agency': [
                (
                    'change_status',
                    'Submit to Client',
                    'submissions',
                    'submitted_to_client',
                ),
                ('reject', 'Reject Candidate', None, None),
            ],
        },
        'interested_and_suitable': {
            'client': [
                (
                    'change_status',
                    'Submit to Hiring Manager',
                    'submissions',
                    'submitted_to_hiring_manager',
                ),
                ('reject', 'Reject Candidate', None, None),
            ],
            'agency': [
                (
                    'change_status',
                    'Submit to Client',
                    'submissions',
                    'submitted_to_client',
                ),
                ('reject', 'Reject Candidate', None, None),
            ],
        },
    },
    'pre_screening': {
        'contacted': {
            'client': [],
            'agency': [
                (
                    'change_status',
                    'Submit to Client',
                    'submissions',
                    'submitted_to_client',
                ),
                ('reject', 'Reject Candidate', None, None),
            ],
        },
        'met_suitable': {
            'client': [],
            'agency': [
                (
                    'change_status',
                    'Submit to Client',
                    'submissions',
                    'submitted_to_client',
                ),
                ('reject', 'Reject Candidate', None, None),
            ],
        },
    },
    'submissions': {
        'applied_by_candidate': {
            'client': [
                (
                    'change_status',
                    'Submit to Hiring Manager',
                    'submissions',
                    'submitted_to_hiring_manager',
                ),
                ('reject', 'Reject Candidate', None, None),
            ],
            'agency': [
                (
                    'change_status',
                    'Submit to Client',
                    'submissions',
                    'submitted_to_client',
                ),
                ('reject', 'Reject Candidate', None, None),
            ],
        },
        'submitted_by_agent': {
            'client': [
                (
                    'change_status',
                    'Submit to Hiring Manager',
                    'submissions',
                    'submitted_to_hiring_manager',
                ),
                ('reject', 'Reject Candidate', None, None),
            ],
            'agency': [],
        },
        'submitted_by_internal_recruiter': {
            'client': [
                (
                    'change_status',
                    'Submit to Hiring Manager',
                    'submissions',
                    'submitted_to_hiring_manager',
                ),
                ('reject', 'Reject Candidate', None, None),
            ],
            'agency': [],
        },
        'submitted_to_client': {
            'client': [],
            'agency': [
                ('change_status', 'Approved by Client', 'screening', 'suitable',),
                ('reject', 'Reject Candidate', None, None),
            ],
        },
        'submitted_to_hiring_manager': {
            'client': [
                (
                    'change_status',
                    'Approved by Hiring Manager',
                    'screening',
                    'suitable',
                ),
                ('reject', 'Rejected by Hiring Manager', None, None),
            ],
            'agency': [],
        },
    },
    'screening': {
        'on_hold': {
            'client': [
                ('schedule_interview', 'Schedule Interview', None, None),
                ('reject', 'Reject Candidate', None, None),
            ],
            'agency': [],
        },
        'on_hold_by_client': {
            'client': [],
            'agency': [
                ('schedule_interview', 'Schedule Interview', None, None),
                ('reject', 'Reject Candidate', None, None),
            ],
        },
        'suitable': {
            'client': [
                ('schedule_interview', 'Schedule Interview', None, None),
                ('reject', 'Reject Candidate', None, None),
            ],
            'agency': [],
        },
        'approved_by_client': {
            'client': [],
            'agency': [
                ('schedule_interview', 'Schedule Interview', None, None),
                ('reject', 'Reject Candidate', None, None),
            ],
        },
    },
    'interviewing': {
        'scheduling_in_progress': {
            'client': [
                ('schedule_interview', 'Schedule Interview', None, None),
                ('reject', 'Reject Candidate', None, None),
            ],
            'agency': [
                ('schedule_interview', 'Schedule Interview', None, None),
                ('reject', 'Reject Candidate', None, None),
            ],
        },
        'confirmed_client_availability': {
            'client': [],
            'agency': [
                ('schedule_interview', 'Schedule Interview', None, None),
                ('reject', 'Reject Candidate', None, None),
            ],
        },
        'confirmed_candidate_availability': {
            'client': [
                ('schedule_interview', 'Schedule Interview', None, None),
                ('reject', 'Reject Candidate', None, None),
            ],
            'agency': [
                ('schedule_interview', 'Schedule Interview', None, None),
                ('reject', 'Reject Candidate', None, None),
            ],
        },
        'scheduled_interview': {
            'client': [('passed_interview', 'Passed Interview', None, None),],
            'agency': [
                ('passed_interview', 'Passed Interview', None, None),
                ('reject', 'Rejected by Client', None, None),
            ],
        },
        'completed_interview_waiting_for_feedback': {
            'client': [('passed_interview', 'Passed Interview', None, None),],
            'agency': [
                ('passed_interview', 'Passed Interview', None, None),
                ('reject', 'Rejected by Client', None, None),
            ],
        },
    },
    'offering': {
        'decided_to_offer': {
            'client': [
                ('change_status', 'Offer Accepted', 'offering', 'offer_accepted'),
                ('reject', 'Offer Declined', None, None),
            ],
            'agency': [
                ('change_status', 'Offer Accepted', 'offering', 'offer_accepted'),
                ('reject', 'Offer Declined', None, None),
            ],
        },
        'prepared_the_offer': {
            'client': [
                ('change_status', 'Offer Accepted', 'offering', 'offer_accepted'),
                ('reject', 'Offer Declined', None, None),
            ],
            'agency': [
                ('change_status', 'Offer Accepted', 'offering', 'offer_accepted'),
                ('reject', 'Offer Declined', None, None),
            ],
        },
        'presented_the_offer': {
            'client': [
                ('change_status', 'Offer Accepted', 'offering', 'offer_accepted'),
                ('reject', 'Offer Declined', None, None),
            ],
            'agency': [
                ('change_status', 'Offer Accepted', 'offering', 'offer_accepted'),
                ('reject', 'Offer Declined', None, None),
            ],
        },
        'offer_accepted': {
            'client': [
                ('change_status', 'Hired', 'hired', 'pending_start_date'),
                ('reject', 'Candidate Backed Out', None, None),
            ],
            'agency': [
                ('change_status', 'Hired', 'hired', 'pending_start_date'),
                ('reject', 'Candidate Backed Out', None, None),
            ],
        },
    },
}


def add_quick_actions(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    ProposalQuickAction = apps.get_model('core', 'ProposalQuickAction')
    ProposalStatus = apps.get_model('core', 'ProposalStatus')

    for stage, status_dict in STAGE_STATUS_ORG_QUICK_ACTION_MAPPING.items():
        for status, org_dict in status_dict.items():
            for org_type, quick_action_tuple_list in org_dict.items():
                for action, label, to_stage, to_status in quick_action_tuple_list:
                    proposal_statuses = (
                        ProposalStatus.objects.using(db_alias)
                        .filter(stage=stage, group=status)
                        .all()
                    )
                    to_proposal_status = (
                        ProposalStatus.objects.using(db_alias)
                        .filter(stage=to_stage, group=to_status)
                        .first()
                    )
                    for proposal_status in proposal_statuses:
                        quick_action = ProposalQuickAction.objects.using(
                            db_alias
                        ).create(
                            proposal_status=proposal_status,
                            action=action,
                            org_type=org_type,
                            label_en=label,
                            to_proposal_status=to_proposal_status,
                        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0218_proposal_quick_actions'),
    ]

    operations = [migrations.RunPython(add_quick_actions, migrations.RunPython.noop)]