# Generated by Django 3.1.10 on 2021-06-04 09:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0267_migrate_job_recruiter_to_recruiters'),
    ]

    operations = [
        migrations.RemoveField(model_name='job', name='recruiter',),
    ]
