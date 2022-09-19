from django.db.models import (
    OuterRef,
    Subquery,
    Count,
    Q,
    Exists,
    Case,
    When,
    F,
    IntegerField,
    FloatField,
)
from django.db.models.functions import Least
from django.contrib.contenttypes.models import ContentType
from djmoney.contrib.exchange.models import Rate as CurrencyRate

from core import models as m
from core.utils import org_filter


def annotate_job_agency_member_have_access_since(qs, user):
    """Add `have_access_since` field, representing since when agency member has
    access to a job
    """
    agency_access = Subquery(
        m.JobAgencyContract.objects.filter(
            job=OuterRef('id'), agency=user.profile.agency
        ).values('created_at')[:1]
    )

    assignee_access = Subquery(
        m.JobAssignee.objects.filter(job=OuterRef('id'), user=user).values(
            'created_at'
        )[:1]
    )

    return qs.annotate(
        have_access_since=Case(
            When(org_filter(user.org), then=F('created_at')),
            default=Least(agency_access, assignee_access),
        )
    ).order_by('-created_at')


# TODO(ZOO-829)
# ACCEPTED_PROPOSAL_STATUS_GROUPS = {'offer_accepted'}
#
# REJECTED_PROPOSAL_STATUS_GROUPS = (
#     set(m.PROPOSAL_STATUS_GROUP_CATEGORIES['closed'])
#     | set(m.PROPOSAL_STATUS_GROUP_CATEGORIES['rejected'])
# ) - ACCEPTED_PROPOSAL_STATUS_GROUPS


def annotate_job_live_proposals(qs, profile):
    return qs.annotate(
        live_proposals_count=Count(
            'proposals',
            filter=(
                Q(
                    # TODO(ZOO-829): might depreciate
                    # might need to revisit if we need to qualify further
                    # proposals__stage='shortlist',
                    proposals__candidate__org_content_type=ContentType.objects.get_for_model(
                        profile.org
                    ),
                    proposals__candidate__org_id=profile.org.id,
                ),
                Q(proposals__is_rejected=False),
            ),
            distinct=True,
        )
    ).order_by('-created_at')


def job_proposal_visible_to_org_filter(org):
    org_type = ContentType.objects.get_for_model(org)

    return Q(org_id=org.id, org_content_type=org_type) | Q(
        proposals__candidate__org_id=org.id,
        proposals__candidate__org_content_type=org_type,
    )


def job_proposal_stage_filter(stage):
    return Q(proposals__status__stage=stage, proposals__is_rejected=False)


def annotate_job_proposal_pipeline(qs, profile):
    visible_to_org = job_proposal_visible_to_org_filter(profile.org)

    return qs.annotate(
        proposals_count=Count(
            'proposals',
            distinct=True,
            filter=Q(
                proposals__status__stage__in=m.ProposalStatusStage.get_shortlist_keys()
            )
            & visible_to_org,
        ),
        proposals_associated_count=Count(
            'proposals',
            filter=job_proposal_stage_filter(m.ProposalStatusStage.ASSOCIATED.key)
            & visible_to_org,
            distinct=True,
        ),
        proposals_pre_screening_count=Count(
            'proposals',
            filter=job_proposal_stage_filter(m.ProposalStatusStage.PRE_SCREENING.key)
            & visible_to_org,
            distinct=True,
        ),
        proposals_submissions_count=Count(
            'proposals',
            filter=job_proposal_stage_filter(m.ProposalStatusStage.SUBMISSIONS.key)
            & visible_to_org,
            distinct=True,
        ),
        proposals_screening_count=Count(
            'proposals',
            filter=job_proposal_stage_filter(m.ProposalStatusStage.SCREENING.key)
            & visible_to_org,
            distinct=True,
        ),
        proposals_interviewing_count=Count(
            'proposals',
            filter=job_proposal_stage_filter(m.ProposalStatusStage.INTERVIEWING.key)
            & visible_to_org,
            distinct=True,
        ),
        proposals_offering_count=Count(
            'proposals',
            filter=job_proposal_stage_filter(m.ProposalStatusStage.OFFERING.key)
            & visible_to_org,
            distinct=True,
        ),
        proposals_hired_count=Count(
            'proposals',
            filter=job_proposal_stage_filter(m.ProposalStatusStage.HIRED.key)
            & visible_to_org,
            distinct=True,
        ),
        proposals_rejected_count=Count(
            'proposals',
            filter=Q(proposals__is_rejected=True) & visible_to_org,
            distinct=True,
        ),
    ).order_by('-created_at')


def annotate_job_hired_count(queryset):
    return queryset.annotate(
        hired_count=Count(
            'proposals__id',
            filter=Q(proposals__status__stage=m.ProposalStatusStage.HIRED.key,),
            distinct=True,
        ),
    ).order_by('-created_at')


def aggregate_proposals_stats(qs):
    # TODO(ZOO-829)
    return qs.aggregate(
        received=Count('id', distinct=True),
        approved=Count(
            'id',
            filter=Q(
                status__stage=m.ProposalStatusStage.SCREENING.key,
                status__group=m.ProposalStatusGroup.QUALIFIED.key,
            ),
            distinct=True,
        ),
        interviewing=Count(
            'id',
            filter=Q(status__stage=m.ProposalStatusStage.INTERVIEWING.key),
            distinct=True,
        ),
        offer=Count(
            'id',
            filter=Q(status__stage=m.ProposalStatusStage.OFFERING.key),
            distinct=True,
        ),
        offer_accepted=Count(
            'id',
            filter=Q(status__stage=m.ProposalStatusStage.HIRED.key),
            distinct=True,
        ),
    )


def annotate_candidate_has_jobs_proposed_to(qs):
    return qs.annotate(
        proposed_to_job=Exists(m.Proposal.objects.filter(candidate=OuterRef('pk')))
    )


def annotate_count_by_date(qs, counted_field, date_field, trunc):
    return (
        qs.values(counted_field)
        .annotate(date=trunc(date_field))
        .values('date')
        .annotate(value=Count(counted_field))
        .values('date', 'value')
        .order_by('date')
    )


def annotate_proposal_deal_pipeline_metrics(qs, agency):
    """Add proposal status order and candidate salary to the proposal qs
    """
    qs = qs.annotate(
        org_status_order=Subquery(
            m.OrganizationProposalStatus.objects.filter(
                status=OuterRef('status'), agency=agency
            ).values('order'),
            output_field=IntegerField(),
        ),
    )
    return (
        qs.filter(
            pk__in=qs.order_by('candidate', '-org_status_order', 'pk').distinct(
                'candidate'
            )
        )
        .annotate(
            exchange_rate=Subquery(
                CurrencyRate.objects.filter(
                    currency=OuterRef('candidate__current_salary_currency')
                ).values('value'),
                output_field=FloatField(),
            ),
        )
        .annotate(
            converted_current_salary=Case(
                When(candidate__current_salary=None, then=0),
                When(exchange_rate=None, then=F('candidate__current_salary')),
                default=F('candidate__current_salary') / F('exchange_rate'),
                output_field=FloatField(),
            )
        )
        .order_by('-org_status_order', '-converted_current_salary', 'pk')
    )
