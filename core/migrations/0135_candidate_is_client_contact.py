# Generated by Django 2.2.9 on 2020-02-10 09:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0134_candidate_internal_status_and_is_met'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='is_client_contact',
            field=models.BooleanField(default=False),
        ),
    ]
