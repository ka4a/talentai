# Generated by Django 2.2.9 on 2020-03-13 16:08

from django.db import migrations, models


DEFAULT_CURRENCY_RATES = {
    'JPY': 1.0,
    'USD': 0.0093,
    'EUR': 0.0084,
    'CNY': 0.065,
    'GBP': 0.0075,
    'KRW': 11.31,
    'INR': 0.69,
    'CAD': 0.013,
    'HKD': 0.072,
    'BRL': 0.045,
}


def apply_default_currency_rates(apps, schema_editor):
    CurrencyRate = apps.get_model('core', 'CurrencyRate')

    rates = []
    for currency, rate in DEFAULT_CURRENCY_RATES.items():
        rates.append(CurrencyRate(currency=currency, rate=rate))

    CurrencyRate.objects.bulk_create(rates)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0157_deal_pipeline_coefficients'),
    ]

    operations = [
        migrations.CreateModel(
            name='CurrencyRate',
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
                    'currency',
                    models.CharField(
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
                        max_length=8,
                        unique=True,
                    ),
                ),
                ('rate', models.FloatField()),
            ],
        ),
        migrations.RunPython(apply_default_currency_rates, migrations.RunPython.noop),
    ]
