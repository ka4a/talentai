# Generated by Django 2.2.9 on 2020-02-17 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0140_candidate_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='current_salary',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='candidate',
            name='current_salary_breakdown',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AddField(
            model_name='candidate',
            name='current_salary_currency',
            field=models.CharField(
                choices=[
                    ('JPY', '¥'),
                    ('USD', '$'),
                    ('EUR', '€'),
                    ('CNY', '¥'),
                    ('GBP', '£'),
                    ('KRW', '₩'),
                    ('INR', '₹'),
                    ('CAD', '$'),
                    ('HKD', '$'),
                    ('BRL', 'R$'),
                ],
                default='JPY',
                max_length=16,
            ),
        ),
    ]
