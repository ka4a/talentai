# Gtext_enerated by Django 2.2.11 on 2020-04-24 11:42

from django.db import migrations, models

REASON_NOT_INTERESTED_TEXTS = [
    {'text_en': 'Not looking for a Job', 'text_ja': '転職を考えていません'},
    {'text_en': 'Not interested in Company', 'text_ja': '会社に興味ありません'},
    {'text_en': 'Not interested in Role', 'text_ja': 'ロールに興味ありません'},
    {'text_en': 'Salary expectation don\'t match', 'text_ja': '希望通りの給与ではありません'},
    {'text_en': 'Cannot relocate', 'text_ja': '転勤できません'},
]

OTHER = {
    'text': 'Other',
    'text_en': 'Other',
    'text_ja': 'その他',
    'has_description': True,
}


def create_reasons_not_interested(apps, schema_editor):
    ReasonDeclined = apps.get_model('core', 'ReasonDeclineCandidateOption')

    other = ReasonDeclined.objects.filter(text_en=OTHER['text_en']).first()
    if other:  # if migration was ran before
        other.has_description = True
        other.text = OTHER['text']
        other.text_ja = OTHER['text_ja']
        other.save()
    else:
        ReasonDeclined.objects.create(**OTHER)

    ReasonNotInterested = apps.get_model('core', 'ReasonNotInterestedCandidateOption')

    for reason_text in REASON_NOT_INTERESTED_TEXTS:
        ReasonNotInterested.objects.create(
            **reason_text, text=reason_text['text_en'], has_description=False
        )

    ReasonNotInterested.objects.create(**OTHER)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0183_job_files_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReasonNotInterestedCandidateOption',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('text', models.CharField(max_length=255)),
                ('has_description', models.BooleanField(default=False)),
                ('text_en', models.CharField(max_length=255, null=True)),
                ('text_ja', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='proposal',
            name='reason_declined_description',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='proposal',
            name='reason_not_interested_description',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='reasondeclinecandidateoption',
            name='has_description',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='proposal',
            name='reasons_not_interested',
            field=models.ManyToManyField(to='core.ReasonNotInterestedCandidateOption'),
        ),
        migrations.RunPython(create_reasons_not_interested, migrations.RunPython.noop),
    ]
