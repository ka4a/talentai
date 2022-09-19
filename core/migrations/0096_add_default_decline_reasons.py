from django.db import migrations

REASON_DECLINE_CANDIDATE_OPTIONS = {
    'did_not_match_expectations': {
        'en': 'Did not match expectations',
        'ja': '期待と一致しませんでした'
    },
    'too_expensive': {
        'en': 'Too expensive',
        'ja': '高過ぎ',
    },
    'concerns_on_fit': {
        'en': 'Concerns on fit',
        'ja': 'フィット感',
    },
    'id_duplicate': {
        'en': 'Is Duplicate',
        'ja': '重複レコード',
    },
}

def generate_default_reason_decline_options(apps, schema_editor):
    ReasonDeclineCandidateOption = apps.get_model('core', 'ReasonDeclineCandidateOption')

    ReasonDeclineCandidateOption.objects.create(
        text_en=REASON_DECLINE_CANDIDATE_OPTIONS['did_not_match_expectations']['en'],
        text_ja=REASON_DECLINE_CANDIDATE_OPTIONS['did_not_match_expectations']['ja'],
    )
    ReasonDeclineCandidateOption.objects.create(
        text_en=REASON_DECLINE_CANDIDATE_OPTIONS['too_expensive']['en'],
        text_ja=REASON_DECLINE_CANDIDATE_OPTIONS['too_expensive']['ja'],
    )
    ReasonDeclineCandidateOption.objects.create(
        text_en=REASON_DECLINE_CANDIDATE_OPTIONS['concerns_on_fit']['en'],
        text_ja=REASON_DECLINE_CANDIDATE_OPTIONS['concerns_on_fit']['ja'],
    )
    ReasonDeclineCandidateOption.objects.create(
        text_en=REASON_DECLINE_CANDIDATE_OPTIONS['id_duplicate']['en'],
        text_ja=REASON_DECLINE_CANDIDATE_OPTIONS['id_duplicate']['ja'],
    )


def delete_default_reason_decline_options(apps, schema_editor):
    ReasonDeclineCandidateOption = apps.get_model('core', 'ReasonDeclineCandidateOption')
    ReasonDeclineCandidateOption.objects.filter(
        text_en=REASON_DECLINE_CANDIDATE_OPTIONS['did_not_match_expectations']['en'],
        text_ja=REASON_DECLINE_CANDIDATE_OPTIONS['did_not_match_expectations']['ja'],
    ).delete()
    ReasonDeclineCandidateOption.objects.filter(
        text_en=REASON_DECLINE_CANDIDATE_OPTIONS['too_expensive']['en'],
        text_ja=REASON_DECLINE_CANDIDATE_OPTIONS['too_expensive']['ja'],
    ).delete()
    ReasonDeclineCandidateOption.objects.filter(
        text_en=REASON_DECLINE_CANDIDATE_OPTIONS['concerns_on_fit']['en'],
        text_ja=REASON_DECLINE_CANDIDATE_OPTIONS['concerns_on_fit']['ja'],
    ).delete()
    ReasonDeclineCandidateOption.objects.filter(
        text_en=REASON_DECLINE_CANDIDATE_OPTIONS['id_duplicate']['en'],
        text_ja=REASON_DECLINE_CANDIDATE_OPTIONS['id_duplicate']['ja'],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0095_add_candidate_decline_reason'),
    ]

    operations = [
        migrations.RunPython(generate_default_reason_decline_options, delete_default_reason_decline_options),
    ]
