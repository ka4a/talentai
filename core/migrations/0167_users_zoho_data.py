# Generated by Django 2.2.11 on 2020-04-07 08:53

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0166_job_missing_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='zoho_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='zoho_id',
            field=models.CharField(blank=True, max_length=32),
        ),
    ]