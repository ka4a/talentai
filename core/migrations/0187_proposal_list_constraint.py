# Generated by Django 2.2.11 on 2020-06-18 15:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0186_proposal_listed_at'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='proposal',
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        models.Q(_negated=True, stage='shortlist'),
                        ('shortlisted_by__isnull', False),
                        _connector='OR',
                    ),
                    models.Q(
                        models.Q(_negated=True, stage='longlist'),
                        ('longlisted_by__isnull', False),
                        _connector='OR',
                    ),
                ),
                name='stage_data_exists',
            ),
        ),
    ]
