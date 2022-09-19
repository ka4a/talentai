from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations

GROUP_NAMES = [
    'Talent Associates',
    'Hiring Managers',
    'Recruiters',
    'Agency Managers',
    'Agency Administrators',
]
GROUP_PERMISSIONS = [
    'delete_proposal'
]


def iterate_over_groups(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    # Create Permission objects
    emit_post_migrate_signal(0, False, db_alias)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    for group_name in GROUP_NAMES:
        group = Group.objects.using(db_alias).get(name=group_name)
        perms = Permission.objects.using(db_alias).filter(
            codename__in=GROUP_PERMISSIONS
        ).all()
        yield group, perms


def add_candidate_permissions(apps, schema_editor):
    """Add add, change and delete Candidate perms to Client Users."""
    for group, perms in iterate_over_groups(apps, schema_editor):
        group.permissions.add(*perms)


def remove_candidate_permissions(apps, schema_editor):
    """Remove add, change and delete Candidate perms from Client Users."""
    for group, perms in iterate_over_groups(apps, schema_editor):
        group.permissions.remove(*perms)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0116_add_candidate_field_source_details'),
    ]

    operations = [
        migrations.RunPython(
            add_candidate_permissions,
            remove_candidate_permissions
        ),
    ]
