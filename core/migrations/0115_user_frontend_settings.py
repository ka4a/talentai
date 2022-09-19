# Generated by Django 2.2.5 on 2019-10-30 12:57

import core.models
import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0114_split_proposed_email_notification_option'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='frontend_settings',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=core.models.FrontendSettingsSchema.get_default_frontend_settings),
        ),
    ]