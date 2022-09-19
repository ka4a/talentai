# Generated by Django 2.2.11 on 2020-04-30 13:30

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0182_remove_placement_fields_from_fee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobfile',
            name='file',
            field=models.FileField(
                max_length=256, upload_to=core.models.get_jobfile_upload_to
            ),
        ),
    ]
