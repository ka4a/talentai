from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from django.db.models import (
    F,
    Value,
    IntegerField,
    CharField,
    DateField,
    Q,
    Max,
    Case,
    When,
)
from django.db.models.functions import Concat, Cast
from rest_framework.permissions import IsAuthenticated

from core.serializers import ApprovalSerializer, ApprovalQuerySerializer
from core.models import Fee, Proposal, FeeApprovalType
from talentai.ordering_filters import CamelCaseOrderingFilter
from core.permissions import IsAgencyUser

integer_field = IntegerField(null=True)
char_field = CharField(blank=True, null=True)
date_field = DateField()
CONCAT_DIVIDER = Value(' ')
NULL = Value(None)


def get_full_name_func(first_name_field, last_name_field):
    return Concat(first_name_field, CONCAT_DIVIDER, last_name_field)


def approval_qs_from_fees(queryset):
    return queryset.values(
        'job_contract_id',
        'proposal_id',
        'bill_description',
        'submitted_at',
        contract_type=F('job_contract__contract_type'),
        job_title=F('job_contract__job__title'),
        available_since=F('created_at'),
        fee_status=F('status'),
        fee_id=Cast(F('id'), char_field),
        candidate_name=Case(
            When(
                Q(placement__isnull=False),
                then=get_full_name_func(
                    'placement__proposal__candidate__first_name',
                    'placement__proposal__candidate__last_name',
                ),
            ),
            When(
                Q(proposal__isnull=False),
                then=get_full_name_func(
                    'proposal__candidate__first_name', 'proposal__candidate__last_name',
                ),
            ),
            default=Value(None, char_field),
        ),
        client_name=F('job_contract__job__client__name'),
        submitted_by_name=get_full_name_func(
            'submitted_by__first_name', 'submitted_by__last_name'
        ),
    )


def approval_qs_from_proposals(queryset):
    return queryset.values(
        job_contract_id=F('job__agency_contracts__id'),
        proposal_id=F('id'),
        bill_description=Value(None, char_field),
        contract_type=F('job__agency_contracts__contract_type'),
        job_title=F('job__title'),
        available_since=Cast(
            Max(
                'status_history__changed_at',
                filter=Q(status_history__status__group='offer_accepted'),
            ),
            date_field,
        ),
        fee_status=Value(None, char_field),
        fee_id=Value(None, integer_field),
        submitted_by_name=Value(None, char_field),
        submission_date=Value(None, char_field),
        candidate_name=get_full_name_func(
            'candidate__first_name', 'candidate__last_name'
        ),
        client_name=F('job__client__name'),
    )


@method_decorator(
    name='list',
    decorator=swagger_auto_schema(query_serializer=ApprovalQuerySerializer()),
)
class ApprovalViewSet(GenericViewSet, ListModelMixin):
    permission_classes = [IsAuthenticated, IsAgencyUser]
    serializer_class = ApprovalSerializer
    # filter backends set explicitly to avoid trying to do things unions can't do
    filter_backends = [CamelCaseOrderingFilter]

    def get_queryset(self):
        approval_type = self.request.query_params.get('type')

        profile = self.request.user.profile

        is_fee = approval_type == FeeApprovalType.FEE.key
        is_placement = approval_type == FeeApprovalType.PLACEMENT.key

        if is_fee or is_placement:
            qs = approval_qs_from_fees(
                Fee.objects.filter(
                    profile.fee_filter, placement__isnull=not is_placement
                )
            )

        elif approval_type == FeeApprovalType.PROPOSAL.key:
            qs = approval_qs_from_proposals(
                profile.apply_proposals_filter(
                    Proposal.objects.filter(
                        status__group='offer_accepted',
                        placement__isnull=True,
                        job__agency_contracts__agency=profile.org.id,
                        job__agency_contracts__is_filled_in=True,
                        job__agency_contracts__contract_type__isnull=False,
                    )
                )
            )

        else:
            qs = Fee.objects.none()

        return qs.order_by('-available_since')
