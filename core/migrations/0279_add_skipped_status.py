# Generated by Django 3.1.13 on 2021-10-07 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0278_add_message_for_candidate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposalinterviewschedule',
            name='status',
            field=models.CharField(choices=[('to_be_scheduled', 'To Be Scheduled'), ('pending', 'Pending Candidate Confirmation'), ('scheduled', 'Scheduled'), ('rejected', 'Rejected'), ('canceled', 'Canceled'), ('skipped', 'Skipped')], default='to_be_scheduled', max_length=20),
        ),
    ]
