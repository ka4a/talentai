# Generated by Django 2.2.5 on 2019-09-23 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0104_job_assignee'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
