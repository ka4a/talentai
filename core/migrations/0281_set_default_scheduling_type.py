from django.db import migrations, models


def set_default_scheduling_type(apps, schema_editor):
    ProposalInterviewSchedule = apps.get_model('core', 'ProposalInterviewSchedule')
    ProposalInterviewSchedule.objects.filter(
        scheduling_type=None, default_for_interviews=None
    ).update(scheduling_type='interview_proposal',)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0280_add_interview_scheduling_type'),
    ]

    operations = [
        migrations.RunPython(set_default_scheduling_type, migrations.RunPython.noop)
    ]
