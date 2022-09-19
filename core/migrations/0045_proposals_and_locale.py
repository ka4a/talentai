# Generated by Django 2.1.7 on 2019-03-05 16:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0044_fix_candidate_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientproposalstatus',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proposal_statuses', to='core.Client'),
        ),
        migrations.AlterField(
            model_name='proposal',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proposals', to='core.Job'),
        ),
        migrations.AlterField(
            model_name='user',
            name='locale',
            field=models.CharField(choices=[('en', 'English'), ('ja', 'Japanese')], default='en', max_length=8),
        ),
    ]