# Generated by Django 2.2.2 on 2019-07-20 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0092_jobcategory'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='source',
            field=models.CharField(blank=True, choices=[('External Agencies', 'External Agencies'), ('Job Boards', 'Job Boards'), ('Referrals', 'Referrals'), ('Direct Sourced', 'Direct Sourced'), ('Applicants (Direct)', 'Applicants (Direct)'), ('Linkedin', 'Linkedin')], max_length=128),
        ),
    ]
