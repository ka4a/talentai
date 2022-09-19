import core.models
from core.models import MoneyField
from django.db import migrations, models
from django.db.models.deletion import CASCADE
from django.conf import settings
import django.db.models.deletion
import djmoney.models.fields
from djmoney.models.fields import CurrencyField

CURRENCIES = [
    ('CAD', '$'),
    ('HKD', '$'),
    ('USD', '$'),
    ('BRL', 'R$'),
    ('GBP', '£'),
    ('CNY', '¥'),
    ('JPY', '¥'),
    ('KRW', '₩'),
    ('EUR', '€'),
    ('INR', '₹'),
]

BILL_DESCRIPTIONS = [
    ('af', 'AF'),
    ('slf', 'SLF'),
    ('ff', 'FF'),
    ('monthly', 'Monthly'),
    ('internal', 'Internal'),
    ('external', 'External'),
    ('placement_fee', 'Placement Fee'),
]

CONTRACT_TYPES = [
    ('mts', 'MTS'),
    ('retainer', 'Retainer'),
    ('contingent', 'Contingent'),
]

INDUSTRIES = [
    ('architecture_and_construction', 'Architecture & Construction'),
    ('automobile_or_aviation_and_aerospace', 'Automobile / Aviation & Aerospace',),
    ('banking_and_financial_services', 'Banking & Financial Services'),
    ('consulting', 'Consulting'),
    ('education_or_training_or_coaching', 'Education / Training / Coaching',),
    ('electronic_goods', 'Electronic Goods'),
    ('energy_and_natural_resources', 'Energy & Natural Resources'),
    ('fintech', 'Fintech'),
    ('food_and_beverage_or_fmcg', 'Food & Beverage / FMCG'),
    ('hardware', 'Hardware'),
    (
        'healthcare_or_pharmaceutical_or_life_sciences',
        'Healthcare / Pharmaceutical / Life Sciences',
    ),
    ('it_or_technology_or__digital_and_telecom', 'IT / Technology/ Digital & Telecom',),
    ('insurance', 'Insurance'),
    ('legal_and_compliance', 'Legal & Compliance'),
    (
        'leisure_or_hospitality_or_restaurants_or_travel_and_tourism',
        'Leisure / Hospitality / Restaurants / Travel & Tourism',
    ),
    ('manufacturing_or_industrial', 'Manufacturing / Industrial'),
    (
        'media_or_art_and_entertaiment_or_communication_or_agency',
        'Media / Art & Entertaiment / Communication / Agency',
    ),
    ('public_sector', 'Public Sector'),
    (
        'real_estate_or_property_and_construction',
        'Real Estate / Property & Construction',
    ),
    ('recruitment', 'Recruitment'),
    (
        'retail_or_fashion_or_luxury_or_consumer_goods',
        'Retail / Fashion / Luxury / Consumer Goods',
    ),
    ('services', 'Services'),
    ('software', 'Software'),
    (
        'transportation_or_shipping_or_logistics',
        'Transportation / Shipping / Logistics',
    ),
]

NOTIFICATIONS = [
    ('agency_assigned_member_for_job', 'Your agency assigns you to a job'),
    ('candidate_longlisted_for_job', 'Candidate longlisted for a job'),
    ('candidate_shortlisted_for_job', 'Candidate shortlisted for a job'),
    ('client_assigned_agency_for_job', 'Client assigns your agency to a job'),
    (
        'client_changed_proposal_status',
        'Client changes status of a submitted candidate',
    ),
    ('client_created_contract', 'Client creates a contract with your agency'),
    ('client_updated_job', 'Client updates a job'),
    ('contract_initiated_agency', 'Your contract with the client has been initiated.'),
    ('contract_initiated_client', 'Your contract with the agency has been initiated.'),
    ('contract_invitation_accepted', 'Agency accepted invitation'),
    ('contract_invitation_declined', 'Agency declined invitation'),
    ('contract_job_access_revoked_invite_ignored', 'Job access has been removed'),
    ('contract_job_access_revoked_no_agreement', 'Job access has been removed'),
    ('contract_signed_by_one_party', 'Contract is signed by one of the parties'),
    ('fee_approved', 'Candidate placement sent to revision'),
    ('fee_draft', 'Fee is set as draft'),
    ('fee_needs_revision', 'Fee is sent to revision'),
    ('fee_pending', 'Fee is submitted for approval'),
    ('fee_pending_reminder', 'Fee is sent to revision'),
    ('job_is_filled', 'Job is filled up'),
    ('placement_fee_approved', 'Candidate placement sent to revision'),
    ('placement_fee_draft', 'Candidate placement is set as draft'),
    ('placement_fee_needs_revision', 'Candidate placement is sent to revision'),
    ('placement_fee_pending', 'Candidate placement is submitted for approval'),
    ('placement_fee_pending_reminder', 'Candidate placement is sent to revision'),
    ('proposal_appointment_confirmed', 'Proposal appointment confirmed'),
    ('proposal_appointment_confirmed_proposer', 'Proposal appointment confirmed'),
    ('proposal_appointment_rejected', 'Proposal appointment rejected'),
    ('proposal_moved', 'Candidate is reallocated to a different job'),
    ('talent_assigned_manager_for_job', 'Talent Associate assigns you to a job'),
]

IOS_IOA = [('ioa', 'IOA'), ('ios', 'IOS')]


def create_currency_field():
    return CurrencyField(
        default='JPY', editable=False, max_length=3, choices=CURRENCIES
    )


def create_money_field():
    return MoneyField(null=True, decimal_places=0, max_digits=19)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0179_rename_placement_to_fee'),
    ]

    operations = [
        migrations.RenameModel('JobAgency', 'JobAgencyContract'),
        migrations.RenameField('Fee', 'signed_at', 'nbv_date'),
        migrations.RenameField('Fee', 'starts_work_at', 'nfi_date'),
        migrations.AddField(
            model_name='agencyclientinfo',
            name='ios_ioa',
            field=models.CharField(choices=IOS_IOA, default='ioa', max_length=3),
        ),
        migrations.AddField(
            model_name='jobagencycontract',
            name='signed_at',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            'Fee', 'bill_description', models.CharField(max_length=200,)
        ),
        migrations.AlterField(
            'Fee',
            'ios_ioa',
            models.CharField(choices=IOS_IOA, default='ioa', max_length=3, null=True),
        ),
        migrations.AddField(
            model_name='jobagencycontract',
            name='contact_person_name',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='fee',
            name='contact_person_name',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='jobagencycontract',
            name='contract_type',
            field=models.CharField(choices=CONTRACT_TYPES, max_length=10, null=True,),
        ),
        migrations.AlterField(
            model_name='fee',
            name='contract_type',
            field=models.CharField(choices=CONTRACT_TYPES, max_length=10, null=True,),
        ),
        migrations.AddField(
            model_name='jobagencycontract',
            name='industry',
            field=models.CharField(choices=INDUSTRIES, max_length=59, null=True,),
        ),
        migrations.AlterField(
            model_name='fee',
            name='industry',
            field=models.CharField(choices=INDUSTRIES, max_length=59, null=True,),
        ),
        migrations.AddField(
            model_name='jobagencycontract',
            name='is_filled_in',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobagencycontract',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='fee', name='offered_salary', field=create_money_field(),
        ),
        # To make sure further migration is reversible
        migrations.AlterField(
            model_name='fee',
            name='offered_salary_currency',
            field=create_currency_field(),
        ),
        migrations.AlterField(
            model_name='fee', name='target_salary', field=create_money_field(),
        ),
        migrations.AlterField(
            model_name='fee',
            name='target_salary_currency',
            field=create_currency_field(),
        ),
        migrations.AlterField(
            model_name='FeeSplitAllocation',
            name='fee',
            field=models.OneToOneField(
                to='core.Fee',
                on_delete=models.CASCADE,
                related_name='split_allocation',
            ),
        ),
        migrations.AlterField(
            model_name='fee',
            name='agency',
            field=models.ForeignKey(
                on_delete=CASCADE, related_name='fees', to='core.Agency'
            ),
        ),
        migrations.AlterField(
            model_name='fee',
            name='agency',
            field=models.ForeignKey(
                on_delete=CASCADE, related_name='fees', to='core.Agency'
            ),
        ),
        migrations.AlterField(
            model_name='fee',
            name='created_by',
            field=models.ForeignKey(
                on_delete=CASCADE,
                related_name='created_fees',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='fee',
            name='invoice_status',
            field=models.CharField(
                choices=[
                    ('paid', 'Paid'),
                    ('overdue', 'Overdue'),
                    ('sent', 'Sent'),
                    ('not_sent', 'Not Sent'),
                ],
                default='not_sent',
                max_length=8,
            ),
        ),
        migrations.AlterField(
            model_name='fee',
            name='proposal',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='fee',
                to='core.Proposal',
            ),
        ),
        migrations.CreateModel(
            name='Placement',
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
                ('signed_at', models.DateField(auto_created=True)),
                (
                    'current_salary_currency',
                    djmoney.models.fields.CurrencyField(
                        choices=CURRENCIES, default='JPY', editable=False, max_length=3,
                    ),
                ),
                (
                    'current_salary',
                    core.models.MoneyField(decimal_places=0, max_digits=19),
                ),
                (
                    'offered_salary_currency',
                    djmoney.models.fields.CurrencyField(
                        choices=CURRENCIES, default='JPY', editable=False, max_length=3,
                    ),
                ),
                (
                    'offered_salary',
                    core.models.MoneyField(decimal_places=0, max_digits=19),
                ),
                ('starts_work_at', models.DateField()),
                (
                    'candidate_source',
                    models.CharField(
                        blank=True,
                        choices=[
                            ('External Agencies', 'External Agencies'),
                            ('Job Boards', 'Job Boards'),
                            ('Referrals', 'Referrals'),
                            ('Applicants (Direct)', 'Applicants (Direct)'),
                            ('Career Event', 'Career Event'),
                            ('BIC', 'BIC'),
                        ],
                        max_length=19,
                    ),
                ),
                (
                    'candidate_source_details',
                    models.CharField(blank=True, max_length=100),
                ),
                (
                    'proposal',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='placement',
                        to='core.Proposal',
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name='fee',
            name='placement',
            field=models.OneToOneField(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='fee',
                to='core.Placement',
            ),
        ),
        migrations.AddField(
            model_name='fee',
            name='job_contract',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.JobAgencyContract',
                related_name='fees',
            ),
        ),
        migrations.AlterField(
            model_name='jobagencycontract',
            name='agency',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='job_contracts',
                to='core.Agency',
            ),
        ),
        migrations.AlterField(
            model_name='jobagencycontract',
            name='job',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='agency_contracts',
                to='core.Job',
            ),
        ),
        migrations.AlterField(
            model_name='fee', name='nbv_date', field=models.DateField(),
        ),
        migrations.RenameField(
            model_name='user',
            old_name='email_candidate_placement_approved',
            new_name='email_fee_approved',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='email_candidate_placement_draft',
            new_name='email_fee_draft',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='email_candidate_placement_needs_revision',
            new_name='email_fee_needs_revision',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='email_candidate_placement_pending',
            new_name='email_fee_pending',
        ),
        migrations.RenameField(
            model_name='team',
            old_name='notify_if_candidate_placement_approved',
            new_name='notify_if_fee_approved',
        ),
        migrations.AlterField(
            model_name='notification',
            name='verb',
            field=models.CharField(choices=NOTIFICATIONS, max_length=255),
        ),
        migrations.AlterField(
            model_name='placement',
            name='candidate_source',
            field=models.CharField(blank=True, max_length=128),
        ),
    ]
