# Generated by Django 2.1.7 on 2019-03-02 01:41

from django.db import migrations


def remove_job_delete_permission(apps, schema_editor):
    """Remove Job Delete Permissions."""
    db_alias = schema_editor.connection.alias

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    p = Permission.objects.using(db_alias).filter(
        codename='delete_job'
    ).first()

    groups = Group.objects.using(db_alias).filter(
        permissions=p
    ).all()

    for group in groups:
        group.permissions.remove(p)


def add_job_delete_permission(apps, schema_editor):
    """Add Job Delete Permissions."""
    db_alias = schema_editor.connection.alias

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    p = Permission.objects.using(db_alias).filter(
        codename='delete_job'
    ).first()

    groups = Group.objects.using(db_alias).filter(
        name__in=['Talent Associates', 'Hiring Managers']
    ).all()
    for group in groups:
        group.permissions.add(p)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0046_remove_job_position'),
    ]

    operations = [
        migrations.RunPython(
            remove_job_delete_permission, add_job_delete_permission
        ),
    ]
