# Generated by Django 2.1.7 on 2019-03-11 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0051_job_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='current_position',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
    ]
