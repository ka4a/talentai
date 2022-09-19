# Generated by Django 2.1.7 on 2019-06-10 14:15

from django.db import migrations, models

import core.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0077_jobfile_thumbnail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidate',
            name='resume_thumbnail',
            field=models.FileField(blank=True, null=True, upload_to='resume-thumbnails'),
        ),
        migrations.AlterField(
            model_name='jobfile',
            name='thumbnail',
            field=models.FileField(blank=True, upload_to=core.models.get_jobfile_thumbnail_upload_to),
        ),
    ]