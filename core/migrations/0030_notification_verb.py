# Generated by Django 2.1.2 on 2019-02-11 22:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_candidate_li_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='verb',
            field=models.CharField(choices=[('agency_proposed_candidate_for_job', '{actor.name} proposed {action_object.name} for "{target.title}"'), ('client_declined_candidate', '{actor.name} declined {action_object.name} for "{target.title}"'), ('talent_assigned_manager_for_job', '{actor.full_name} assigned you to "{target.title}"'), ('client_approved_candidate', '{actor.name} approved {action_object.name} for "{target.title}"'), ('client_updated_job', '{actor.name} updated "{target.title}"'), ('client_created_contract', '{actor.name} created contract with your agency'), ('client_assigned_agency_for_job', '{actor.name} assigned your agency to "{target.title}"')], max_length=255),
        ),
    ]
