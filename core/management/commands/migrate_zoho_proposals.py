from distutils.util import strtobool

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ValidationError

from core.management.commands.migrate_zoho_jobs import get_job_zoho_id_from_zoho_data
from core.models import (
    Job,
    Agency,
    JobStatus,
    Proposal,
    ProposalStatus,
    Candidate,
    SHORTLIST_PROPOSAL_STATUS_GROUPS,
)
from core.zoho import ZohoRecruitClient, zoho_data_to_dict
from core.utils import org_filter


LONGLIST = 'longlist'
SHORTLIST = 'shortlist'

JOB_STATUS_MAPPING = {
    'On - Hold': JobStatus.ON_HOLD.key,
    'Pitching - not yet secured': '',
    'Cancelled': '',
    'In-progress': JobStatus.OPEN.key,
    'Filled': JobStatus.FILLED.key,
    'Inactive': '',
}

# TODO(ZOO-831): zoho mapping
PROPOSAL_STATUS_NAME_MAPPING = {
    'Unqualified': 'Interviewed - Not Interested',
    'CCM 1': 'First interview',
    'DO NOT CONTACT': 'Interviewed - Not Suitable',
    'Rejected by client': 'Client declined',
    'Interviewing with Client (Do not use)': 'First interview',
    'Qualified': 'Interviewed - Interested',
    'HCCR - Interviewed - Not Suitable - Interested': 'Interviewed - Not Interested',
    'Offer-Declined': 'Offer Declined',
    'Pending interview (HCCR)': 'Interviewed - Interested',
    'HCCR - Interested - Buy-in': 'Interviewed - Interested',
    'Unplaceable': 'Interviewed - Not Suitable',
    'Submitted-to-client': 'Pending review',
    'Interviewed - not interested(Do not Use)': 'Interviewed - Not Interested',
    'Not Interviewed, Not Qualified': 'Contacted - Not Interested',
    'Rejected by Candidate': 'Candidate Quits Process',
    'Interviewed - not suitable': 'Interviewed - Not Suitable',
    'Poached - not interested': 'Contacted - Not Interested',
    'HCCR - Interviewed - Suitable - Not Interested': 'Interviewed - Not Interested',
    'HCCR - Interested - Pending buy-in': 'Contacted - Pending Interview',
    'Contact in Future': 'Contacted - Not Interested',
    'Skill Assesment': 'Interviewed - Pending feedback',
    'Buy-in': 'Interviewed - Pending feedback',
    'Attempted to Contact': 'Not Contacted',
    'Interview-Scheduled': 'Contacted - Pending Interview',
    'Interviewed - not interested': 'Interviewed - Not Interested',
    'Interview-in-Progress': 'Interviewed - Pending feedback',
    'CCM 4': 'Third interview',
    'HCCR - Interviewed - Not Interested': 'Interviewed - Not Interested',
    'Offer-Made': 'Offer Sent',
    'Interviewed - not suitable(Do not Use)': 'Interviewed - Not Suitable',
    'HCCR - Internal Interview': 'Interviewed - Pending feedback',
    'Offer-Withdrawn': 'Client declined',
    'Rejected': 'Client declined',
    'HCCR - Interviewed - Interested': 'Interviewed - Interested',
    'Interview-to-be-Scheduled': 'CV Approved',
    'Contacted': 'Contacted - Pending Interview',
    'Placed': 'Offer Accepted',
    'Offer Stage (Do not Use)': 'Offer Prep',
    'Identified': 'Not Contacted',
    'CCM 2': 'Second interview',
    'Placed (Do Not Use)': 'Offer Accepted',
    'Declined by Candidate': 'Candidate Quits Process',
    'Associated': 'Not Contacted',
    'Hired': 'Offer Accepted',
    'Interviewing with Client': 'First interview',
    'CCM 3': 'Third interview',
    'HCCR - Interested - Pending resume': 'Interviewed - Interested',
    'New': 'Not Contacted',
    'Approved by client': 'CV Approved',
    'Offer-Accepted': 'Offer Accepted',
    'Offer': 'Offer Sent',
    'Interviewed (HCCR)': 'Interviewed - Pending feedback',
    'No-Show': 'Candidate Quits Process',
    'Client-Rejected-From-Interview': 'Client declined',
}

PROPOSAL_STATUSES = {}
for status in ProposalStatus.objects.filter(default=True):
    PROPOSAL_STATUSES[status.status_en] = status


def get_status_stage(status):
    # TODO(ZOO-831)
    return SHORTLIST if status.group in SHORTLIST_PROPOSAL_STATUS_GROUPS else LONGLIST


def migrate_zoho_proposals(zoho_auth_token, agency, default_user):
    zoho_client = ZohoRecruitClient(zoho_auth_token, 'JobOpenings')
    jobs = Job.objects.filter(org_filter(agency) & Q(status=JobStatus.OPEN.key))
    candidates = Candidate.objects.filter(
        org_filter(agency) & ~Q(zoho_id='') & ~Q(zoho_id=None)
    )

    created = 0
    not_found = 0

    with transaction.atomic():
        for job in jobs:
            print(f'Processing job with id {job.zoho_id}')
            proposals = []

            for zoho_data in zoho_client.get_all_records(
                params={'id': job.zoho_id},
                endpoint='getAssociatedCandidates',
                index_range=200,
            ):
                try:
                    fields_data = zoho_data_to_dict(zoho_data['FL'])
                except:
                    print(zoho_data)
                    continue
                candidate = candidates.filter(
                    zoho_id=fields_data['CANDIDATEID']
                ).first()
                if not candidate:
                    not_found += 1
                    continue

                status = PROPOSAL_STATUSES[
                    PROPOSAL_STATUS_NAME_MAPPING[fields_data['STATUS']]
                ]

                if not status:
                    print(f'Can not found status {fields_data["STATUS"]}')
                    continue

                stage = get_status_stage(status)

                suitability = fields_data.get('RATING', None)
                suitability = int(float(suitability)) if suitability else None

                proposal = Proposal(
                    candidate=candidate,
                    job=job,
                    stage=stage,
                    status=status,
                    suitability=suitability,
                    created_by=job.assignees.first() or default_user,
                )
                proposals.append(proposal)
                created += 1

            Proposal.objects.bulk_create(proposals)

    return jobs.count(), created, not_found


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('zoho_auth_token', nargs='?', type=str)
        parser.add_argument('agency_id', nargs=1, type=int)
        parser.add_argument('default_user_id', nargs='?', type=int)

    def handle(self, *args, **options):
        zoho_auth_token = options['zoho_auth_token']
        agency = Agency.objects.get(pk=options['agency_id'][0])
        default_user = agency.members.filter(pk=options['default_user_id']).first()

        while True:
            try:
                print(f'Default Proposals creator is {default_user.full_name}.\n')
                message = (
                    'Import Proposals to "{}" Agency? '
                    'Make sure you Candidates and Jobs'
                    'are already imported. [y/n] '.format(agency.name)
                )
                if not strtobool(input(message)):
                    print('Import canceled')
                    return

                break
            except ValueError:
                print('Answer must be either y or n')

        jobs, created, not_found = migrate_zoho_proposals(
            zoho_auth_token, agency, default_user
        )

        print(f'Successfully create {created} proposals for {jobs} jobs.')
        if not_found:
            print(f'Can not found {not_found} candidates')
