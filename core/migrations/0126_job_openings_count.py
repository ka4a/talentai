# Generated by Django 2.2.8 on 2019-12-26 06:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0125_link_to_candidate_original'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='openings_count',
            field=models.IntegerField(default=1),
        ),
    ]