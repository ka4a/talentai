# Generated by Django 2.2.17 on 2020-12-24 11:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0207_proposal_and_job_appointment_updates'),
    ]

    operations = [
        migrations.RenameField(
            model_name='candidate',
            old_name='first_name_ja',
            new_name='first_name_kanji',
        ),
        migrations.RenameField(
            model_name='candidate', old_name='last_name_ja', new_name='last_name_kanji',
        ),
        migrations.AddField(
            model_name='candidate',
            name='first_name_katakana',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AddField(
            model_name='candidate',
            name='last_name_katakana',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AddField(
            model_name='candidate',
            name='middle_name',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
    ]
