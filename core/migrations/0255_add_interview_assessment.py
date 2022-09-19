# Generated by Django 2.2.19 on 2021-04-29 01:31

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0254_add_interview_notes'),
    ]

    operations = [
        migrations.CreateModel(
            name='HiringCriterionAssessment',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'rating',
                    models.PositiveSmallIntegerField(
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(5),
                        ],
                    ),
                ),
                (
                    'hiring_criterion',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='core.HiringCriterion',
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='ProposalInterviewAssessment',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'decision',
                    models.CharField(
                        choices=[
                            ('hire', 'Hire!'),
                            ('proceed', 'Proceed'),
                            ('keep', 'Keep'),
                            ('reject', 'Reject'),
                        ],
                        max_length=7,
                    ),
                ),
                ('notes', models.TextField(blank=True)),
                (
                    'hiring_criteria',
                    models.ManyToManyField(
                        related_name='_proposalinterviewassessment_hiring_criteria_+',
                        through='core.HiringCriterionAssessment',
                        to='core.HiringCriterion',
                    ),
                ),
                (
                    'interview',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='assessment',
                        to='core.ProposalInterview',
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name='hiringcriterionassessment',
            name='interview',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='core.ProposalInterviewAssessment',
            ),
        ),
    ]
