import bleach

from django.db import migrations, transaction, models

CANDIDATE_RICH_FIELDS = [
    'current_salary_breakdown',
    'reason_for_job_changes',
    'companies_already_applied_to',
    'companies_applied_to',
    'summary',
    'client_brief',
]

FEE_RICH_FIELDS = [
    'notes_to_approver',
]

AGENCY_CLIENT_INFO_RICH_FIELDS = [
    'info',
    'notes',
]

CANDIDATE_NOTE_RICH_FIELDS = ['text']


def clean_field(value):
    return bleach.clean(
        value, tags=['p', 'ul', 'li', 'ol', 'strong', 'em', 'u'], attributes={},
    )


def update_fields(model_fields_mapping):
    with transaction.atomic():
        for Model, fields in model_fields_mapping.items():
            for field in fields:
                filter_params = ~models.Q(**{field: ''}) & ~models.Q(**{field: None})

                for instance in Model.objects.filter(filter_params).distinct():
                    value = getattr(instance, field)
                    setattr(instance, field, clean_field(value))
                    instance.save()


def apply_rich_text_fields(apps, schema_editor):
    Candidate = apps.get_model('core', 'Candidate')
    AgencyClientInfo = apps.get_model('core', 'AgencyClientInfo')
    CandidateNote = apps.get_model('core', 'CandidateNote')
    Fee = apps.get_model('core', 'Fee')

    update_fields(
        {
            Candidate: CANDIDATE_RICH_FIELDS,
            AgencyClientInfo: AGENCY_CLIENT_INFO_RICH_FIELDS,
            CandidateNote: CANDIDATE_NOTE_RICH_FIELDS,
            Fee: FEE_RICH_FIELDS,
        }
    )


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0184_proposal_reason_no_candidate'),
    ]
    operations = [
        migrations.RunPython(apply_rich_text_fields, migrations.RunPython.noop)
    ]
