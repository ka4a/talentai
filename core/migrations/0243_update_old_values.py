# Generated by Django 2.2.19 on 2021-03-29 12:23

from django.db import migrations


def update_jobs(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    Job = apps.get_model('core', 'Job')
    Job.objects.using(db_alias).update(work_experience='none')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0242_update_job_and_candidate_fields'),
    ]

    operations = [migrations.RunPython(update_jobs, migrations.RunPython.noop)]