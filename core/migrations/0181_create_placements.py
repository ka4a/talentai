from django.db import migrations
from django.utils.timezone import now


def create_placements(apps, schema_editor):
    Fee = apps.get_model('core', 'Fee')
    Placement = apps.get_model('core', 'Placement')
    FeeSplitAllocation = apps.get_model('core', 'FeeSplitAllocation')
    Job = apps.get_model('core', 'Job')
    JobAgencyContract = apps.get_model('core', 'JobAgencyContract')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    fee_qs = Fee.objects.filter(proposal_id__isnull=False)

    agency_content_type = ContentType.objects.get(app_label='core', model='agency')

    agency_jobs_qs = Job.objects.filter(org_content_type=agency_content_type,)

    for job in agency_jobs_qs:
        job_agency_contract_qs = JobAgencyContract.objects.filter(
            agency_id=job.org_id, job=job,
        )
        if not job_agency_contract_qs.exists():
            JobAgencyContract.objects.create(agency_id=job.org_id, job=job)

    for fee in fee_qs:
        if fee.placement_id is None:
            placement = Placement(
                proposal=fee.proposal,
                current_salary=fee.target_salary,
                offered_salary=fee.offered_salary,
                signed_at=fee.nbv_date,  # former fee.signed_at
                starts_work_at=fee.nfi_date,  # former fee.starts_work_at
            )
        else:
            placement = fee.placement

        split_allocation = FeeSplitAllocation.objects.filter(fee_id=fee.id).first()

        if split_allocation:
            placement.candidate_source = split_allocation.candidate_source

        placement.save()
        fee.placement = placement

        job_agency_contract = JobAgencyContract.objects.filter(
            agency=fee.agency, job=fee.proposal.job,
        ).first()

        is_job_contract_changed = False

        if job_agency_contract.contract_type is None:
            job_agency_contract.contract_type = fee.contract_type
            is_job_contract_changed = True

        if not job_agency_contract.contact_person_name:
            job_agency_contract.contact_person_name = fee.contact_person_name
            is_job_contract_changed = True

        if job_agency_contract.industry is None:
            job_agency_contract.industry = fee.industry
            is_job_contract_changed = True

        if job_agency_contract.signed_at is None:
            job_agency_contract.signed_at = now()
            is_job_contract_changed = True

        if not job_agency_contract.is_filled_in:
            job_agency_contract.is_filled = True
            is_job_contract_changed = True

        if is_job_contract_changed:
            job_agency_contract.is_filled_in = True
            job_agency_contract.save()

        fee.job_contract = job_agency_contract

        fee.save()


def revert_create_placements(apps, schema_editor):
    Fee = apps.get_model('core', 'Fee')
    FeeSplitAllocation = apps.get_model('core', 'FeeSplitAllocation')
    AgencyClientInfo = apps.get_model('core', 'AgencyClientInfo')

    fee_qs = Fee.objects.all()

    for fee in fee_qs:
        if fee.placement:
            fee.proposal = fee.placement.proposal
            fee.current_salary = fee.placement.current_salary
            fee.offered_salary = fee.placement.offered_salary
            fee.signed_at = fee.placement.signed_at
            fee.starts_work_at = fee.placement.starts_work_at

            split_allocation = FeeSplitAllocation.objects.filter(fee_id=fee.id).first()

            if split_allocation:
                split_allocation.candidate_source = fee.placement.candidate_source
                split_allocation.save()

        job_contract = fee.job_contract
        client_info = AgencyClientInfo.objects.filter(
            client_id=job_contract.job.client_id, agency_id=fee.agency_id,
        ).first()

        fee.ios_ioa = client_info.ios_ioa if client_info else 'ios'
        fee.contract_type = job_contract.contract_type
        fee.industry = job_contract.industry
        fee.contact_person_name = job_contract.contact_person_name

        fee.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0180_fee_fields'),
    ]

    operations = [
        migrations.RunPython(create_placements, revert_create_placements),
    ]
