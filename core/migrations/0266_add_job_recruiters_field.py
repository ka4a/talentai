# Generated by Django 3.1.10 on 2021-06-04 07:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0265_remove_old_statuses_from_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='recruiters',
            field=models.ManyToManyField(
                blank=True, related_name='primary_jobs', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name='job',
            name='recruiter',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
