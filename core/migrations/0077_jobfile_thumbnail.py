# Generated by Django 2.1.7 on 2019-06-05 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0076_candidate_resume_thumbnail'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobfile',
            name='thumbnail',
            field=models.FileField(blank=True, upload_to=''),
        ),
    ]
