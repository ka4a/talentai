# Generated by Django 2.2.17 on 2021-02-08 01:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0221_appointment_templates_default_order'),
    ]

    operations = [
        migrations.RemoveField(model_name='candidate', name='field_of_study',),
    ]
