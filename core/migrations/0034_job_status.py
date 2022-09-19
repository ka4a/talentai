# Generated by Django 2.1.7 on 2019-02-15 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_candidate_cv'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='status',
            field=models.CharField(choices=[('open', 'Open'), ('on_hold', 'On Hold'), ('filled', 'Filled'), ('closed', 'Closed')], default='open', max_length=16),
        ),
    ]