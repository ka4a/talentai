# Generated by Django 2.2.19 on 2021-03-22 10:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0239_default_user_notification_settings'),
    ]

    operations = [
        migrations.RenameField(
            model_name='candidate', old_name='work_direct', new_name='secondary_phone',
        ),
        migrations.RemoveField(model_name='candidate', name='work_mobile',),
    ]
