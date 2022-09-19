# Generated by Django 2.1.7 on 2019-03-13 14:52

import django.db.models.deletion
from django.db import migrations, models

GROUP_PERMISSIONS = {
    'Recruiters': (
        'view_jobfile',
    ),
    'Talent Associates': (
        'add_jobfile',
        'view_jobfile',
        'change_jobfile',
        'delete_jobfile',
    ),
    'Hiring Managers': (
        'add_jobfile',
        'view_jobfile',
        'change_jobfile',
        'delete_jobfile',
    ),
}


def add_job_file_permissions(apps, schema_editor):
    """Add Job File Permissions."""
    db_alias = schema_editor.connection.alias

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    for g in GROUP_PERMISSIONS:
        group = Group.objects.using(db_alias).get(name=g)
        for p in GROUP_PERMISSIONS[g]:
            permission = Permission.objects.using(db_alias).get(codename=p)
            group.permissions.add(permission)
            group.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0056_candidate_summary_not_required'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Job')),
            ],
        ),
        migrations.RunPython(
            add_job_file_permissions, migrations.RunPython.noop
        )
    ]
