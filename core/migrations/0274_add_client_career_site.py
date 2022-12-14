# Generated by Django 3.1.13 on 2021-08-16 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0273_add_flags_to_external_jobs'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='career_site_slug',
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='client',
            name='is_career_site_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
