# Generated by Django 2.2.11 on 2020-04-14 13:30

from django.db import migrations, models
from django.db.models import Max

NEW_STATUS_GROUP_CHOICES = [
    ('new', 'New'),
    ('proceeding', 'Proceeding'),
    ('approved', 'CV approved'),
    ('rejected', 'CV rejected'),
    ('interviewing', 'Interviewing'),
    ('offer', 'Offer'),
    ('offer_accepted', 'Offer Accepted'),
    ('offer_declined', 'Offer Declined'),
    ('candidate_quit', 'Candidate Quits Process'),
    ('closed', 'Closed'),
    ('not_contacted', 'Not Contacted'),
    ('not_interested', 'Contacted - Not Interested'),
    ('pending_interview', 'Contacted - Pending Interview'),
    ('interested', 'Interviewed - Interested'),
    ('not_interested_after_interview', 'Interviewed - Not Interested'),
    ('pending_feedback', 'Interviewed - Pending feedback'),
    ('not_suitable', 'Interviewed - Not Suitable'),
]

REMOVED_ORGANIZATION_PROPOSAL_STATUS_GROUPS = [
    'not_contacted',
    'interested',
    'not_interested',
    'not_interested_after_interview',
    'pending_feedback',
    'pending_interview',
    'not_suitable',
    'interviewed_internally',
    'early_rejected',
]

REPLACED_GROUPS = (
    ('interviewed_internally', 'interested'),
    ('early_rejected', 'not_suitable'),
)

RENAMED = (
    ('Rejected', 'Interviewed - Not Suitable'),
    ('Not contacted', 'Not Contacted'),
    ('Interested', 'Interviewed - Interested'),
    ('Not interested', 'Contacted - Not Interested'),
    ('Pending feedback', 'Interviewed - Pending feedback'),
)

NEW = (
    ('not_interested_after_interview', 'Interviewed - Not Interested'),
    ('pending_interview', 'Contacted - Pending Interview'),
)


def replace_default_status(model, group, status):
    model.objects.filter(status__group=group, status__default=True,).update(
        status=status
    )


def get_max_field(model, field):
    return model.objects.all().aggregate(max=Max(field))['max']


def rename_statuses(apps, schema_editor):
    ProposalStatusHistory = apps.get_model('core', 'ProposalStatusHistory')
    ProposalStatus = apps.get_model('core', 'ProposalStatus')
    OrganizationProposalStatus = apps.get_model('core', 'OrganizationProposalStatus')
    Proposal = apps.get_model('core', 'Proposal')

    interested = ProposalStatus.objects.filter(group='interested', default=True).first()

    replace_default_status(Proposal, 'interviewed_internally', interested)
    replace_default_status(ProposalStatusHistory, 'interviewed_internally', interested)
    OrganizationProposalStatus.objects.filter(
        status__group='interviewed_internally', status__default=True
    ).delete()

    ProposalStatus.objects.filter(group='interviewed_internally', default=True).delete()

    OrganizationProposalStatus.objects.filter(
        status__group__in=REMOVED_ORGANIZATION_PROPOSAL_STATUS_GROUPS
    ).delete()

    for group, name in NEW:
        identity = dict(group=group, status_en=name, default=True,)
        if ProposalStatus.objects.filter(**identity).exists():
            continue
        next_default_order = get_max_field(ProposalStatus, 'default_order') + 10

        ProposalStatus.objects.create(**identity, default_order=next_default_order)

    for group, new_group in REPLACED_GROUPS:
        ProposalStatus.objects.filter(group=group).update(group=new_group)

    for name, new_name in RENAMED:
        ProposalStatus.objects.filter(status_en=name, default=True).update(
            status_en=new_name
        )


def rename_statuses_back(apps, schema_editor):
    ProposalStatus = apps.get_model('core', 'ProposalStatus')

    ProposalStatus.objects.filter(group='not_suitable').update(group='early_rejected')

    for new_name, name in RENAMED:
        ProposalStatus.objects.filter(status_en=name).update(status_en=new_name)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0170_job_zoho_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposalstatus',
            name='group',
            field=models.CharField(
                choices=[
                    *NEW_STATUS_GROUP_CHOICES,
                    ('interviewed_internally', 'Interviewed internally'),
                    ('early_rejected', 'Rejected'),
                ],
                max_length=32,
            ),
        ),
        migrations.RunPython(rename_statuses, rename_statuses_back),
        migrations.AlterField(
            model_name='proposalstatus',
            name='group',
            field=models.CharField(choices=NEW_STATUS_GROUP_CHOICES, max_length=32),
        ),
    ]
