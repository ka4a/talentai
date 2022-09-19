# Generated by Django 2.1.2 on 2019-02-03 17:45

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_update_agency_recruiter_reg'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_activated',
            field=models.BooleanField(default=True, editable=False),
        ),
        migrations.AddField(
            model_name='user',
            name='on_activation_action',
            field=models.CharField(blank=True, editable=False, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='on_activation_params',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, editable=False, null=True),
        ),
    ]