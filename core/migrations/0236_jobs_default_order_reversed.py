# Generated by Django 2.2.19 on 2021-03-10 05:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0235_jobs_default_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='job', options={'ordering': ('-created_at',)},
        ),
    ]
