# Generated by Django 2.2.17 on 2020-12-20 18:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


APPOINTMENT_TEMPLATES = [
    {'appointment_type': 'general', 'default_order': 10},
    {'appointment_type': 'technical_fit', 'default_order': 20},
    {'appointment_type': 'cultural_fit', 'default_order': 30},
]


def update_appointment_templates(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    AppointmentTemplate = apps.get_model('core', 'AppointmentTemplate')
    AppointmentTemplate.objects.all().delete()
    for item in APPOINTMENT_TEMPLATES:
        appointment_template = AppointmentTemplate.objects.using(db_alias).create(
            default=True, **item
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0206_new_default_appointment_templates'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobappointmenttemplate',
            name='interviewer',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='appointment_templates',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='proposalappointment',
            name='interviewer',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='proposal_appointments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='proposalappointment',
            name='order',
            field=models.PositiveIntegerField(default=10),
        ),
        migrations.AlterField(
            model_name='jobappointmenttemplate',
            name='description',
            field=models.TextField(blank=True, max_length=1024),
        ),
        migrations.RunPython(update_appointment_templates, migrations.RunPython.noop),
    ]
