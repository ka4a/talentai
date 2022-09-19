from collections import defaultdict
from itertools import count

from django.db.models import Q, Exists, OuterRef, Max, F, Value, Case, When
from django.db.models.functions import Concat
from django_filters import rest_framework as filters
from rest_framework import filters as drf_filters
from rest_framework.settings import api_settings
from reversion.models import Version

from core import models as m
from core.utils import get_user_org, get_bool_annotation


class AgencyFilter(filters.FilterSet):
    """Filter set for Agency."""

    working_with = filters.BooleanFilter(method='working_with_filter')

    function_focus__in = filters.BaseInFilter(
        field_name='function_focus', lookup_expr='in'
    )
    categories_filter = filters.BaseInFilter(method='categories_filter_filter')

    class Meta:  # noqa
        model = m.Agency
        fields = ('working_with', 'categories_filter')

    def working_with_filter(self, queryset, name, value):
        """Filter by Contracts if it is the User Client."""
        profile = self.request.user.profile

        if hasattr(profile, 'client'):
            return m.Agency.objects.filter(
                contracts__client=profile.client,
                contracts__status=m.ContractStatus.INITIATED.key,
            )

        return queryset

    def categories_filter_filter(self, queryset, name, value):
        """Filter each category group separately.

        E.g. if we have category groups A and B,
        an agency should have both
        (with __in filter it could have just one)
        """
        categories = m.AgencyCategory.objects.filter(id__in=value).values_list(
            'group', 'id'
        )

        category_ids_by_group = defaultdict(set)

        for g, i in categories:
            category_ids_by_group[g].add(i)

        exist_queries = [
            Exists(
                m.Agency.categories.through.objects.filter(
                    agency=OuterRef('id'), agencycategory__in=ids,
                )
            )
            for ids in category_ids_by_group.values()
        ]

        # for each group we have a separate annotation
        annotations = {
            f'_have_category_group_{i}': q for i, q in zip(count(), exist_queries)
        }

        return queryset.annotate(**annotations).filter(
            # all annotations should be true
            **{k: True for k in annotations.keys()}
        )


class ContractFilterSet(filters.FilterSet):
    """Filter set for Contracts"""

    status__in = filters.BaseInFilter(field_name='status', lookup_expr='in')

    class Meta:
        model = m.Contract
        fields = ('status__in',)


class ProposalFilterSet(filters.FilterSet):
    """Filter set for Proposal."""

    candidate__agency = filters.ModelChoiceFilter(queryset=m.Agency.objects.all())
    status__in = filters.BaseInFilter(field_name='status', lookup_expr='in')
    status_group_category__in = filters.BaseInFilter(
        method='status_group_category__in_filter'
    )

    client__in = filters.BaseInFilter(field_name='job__client', lookup_expr='in')
    stage = filters.Filter(method='stage_filter')
    job = filters.Filter(field_name='job', lookup_expr='exact')
    extra_fields = filters.Filter(method='extra_fields_filter')
    is_placement_available = filters.BooleanFilter(
        method='is_placement_available_filter'
    )
    job_contract = filters.Filter(field_name='job__agency_contracts__id')

    class Meta:  # noqa
        model = m.Proposal
        fields = (
            'job',
            'candidate__agency',
            'stage',
            'status',
            'status__group',
            'status__in',
            'status_group_category__in',
            'job',
            'job_contract',
            'extra_fields',
        )

    def stage_filter(self, queryset, name, value):
        if value == 'rejected':
            return queryset.filter(is_rejected=True)
        else:
            queryset = queryset.filter(status__stage=value, is_rejected=False)
            queryset = queryset.annotate(
                status_last_changed_at=Max('status_history__changed_at')
            )
            group_order = m.ProposalStatusGroup.get_stage_keys(value)
            queryset = queryset.order_by(
                Case(
                    *[
                        When(status__group=group, then=len(group_order) - pos)
                        for pos, group in enumerate(group_order)
                    ]
                ),
                'status_last_changed_at',
            )
            return queryset

    def extra_fields_filter(self, queryset, name, value):
        extra_fields = value.split(',')

        if 'hired_at' in extra_fields:
            queryset = queryset.annotate(
                hired_at=Max(
                    'status_history__changed_at',
                    filter=Q(
                        status_history__status__stage=m.ProposalStatusStage.HIRED.key,
                        status_history__status__group=m.ProposalStatusGroup.PENDING_START.key,
                    ),
                )
            )
        if 'job_created_by_name' in extra_fields:
            queryset = queryset.annotate(
                job_created_by_name=Concat(
                    'job__owner__first_name', Value(' '), 'job__owner__last_name'
                ),
            )

        user = self.request.user
        if isinstance(user.org, m.Agency):
            if 'fee_id' in extra_fields:
                queryset = queryset.annotate(fee_id=F('placement__fee__id'))

            if 'can_see_placement' in extra_fields:
                queryset = queryset.annotate(
                    can_see_placement=Exists(
                        m.Fee.objects.filter(
                            user.profile.fee_filter,
                            placement__proposal_id=OuterRef('id'),
                        )
                    )
                )
            if 'can_edit_placement' in extra_fields:
                queryset = queryset.annotate(
                    can_edit_placement=Exists(
                        m.Fee.objects.filter(
                            user.profile.editable_fee_filter,
                            placement__proposal_id=OuterRef('id'),
                        )
                    )
                )
            if 'can_create_placement' in extra_fields:
                condition = Q(
                    status__group=m.ProposalStatusGroup.PENDING_START.key,
                    placement__isnull=True,
                )

                if isinstance(user.profile, m.Recruiter):
                    condition = condition & Q(created_by=user)

                queryset = queryset.annotate(
                    can_create_placement=get_bool_annotation(condition)
                )

        return queryset

    def status_group_category__in_filter(self, queryset, name, value):
        # TODO(ZOO-829) depreciate
        # groups = set()

        # for group_category in value:
        #     group_category_groups = m.PROPOSAL_STATUS_GROUP_CATEGORIES.get(
        #         group_category
        #     )

        #     if group_category_groups:
        #         groups.update(group_category_groups)

        # return queryset.filter(status__group__in=groups)
        return queryset


class ProposalCommentFilterSet(filters.FilterSet):
    """Filter set for Proposal comments."""

    public = filters.BooleanFilter(method='public_filter')

    class Meta:  # noqa
        model = m.ProposalComment
        fields = ('proposal', 'public')

    def public_filter(self, queryset, name, value):
        """Filter by public field"""
        return queryset.filter(Q(public=value) | Q(system=True, public=True)).distinct()


class ProposalQuestionFilterSet(filters.FilterSet):
    class Meta:  # noqa
        model = m.ProposalQuestion
        fields = ('proposal',)


class JobFilterSet(filters.FilterSet):
    """Filter set for Job."""

    managers = filters.CharFilter(field_name='_managers')
    status__in = filters.BaseInFilter(field_name='status', lookup_expr='in')

    client__in = filters.BaseInFilter(field_name='client', lookup_expr='in')
    client = filters.NumberFilter(field_name='client', lookup_expr='id')

    only_my_jobs = filters.BooleanFilter(method='filter_only_my_jobs')
    is_belong_to_user_org = filters.BooleanFilter(method='filter_is_belong_to_user_org')

    def filter_is_belong_to_user_org(self, queryset, name, value):
        user = self.request.user
        if value:
            return user.profile.org.apply_own_jobs_filter(queryset)

    def filter_only_my_jobs(self, queryset, name, value):
        user = self.request.user
        if value:
            return queryset.filter(Q(_assignees__in=[user]) | Q(owner=user)).distinct()

    class Meta:  # noqa
        model = m.Job
        fields = ('client', 'status', 'status__in', 'managers')


USER_GROUP_FILTER = {
    'Talent Associates': 'talentassociate',
    'Hiring Managers': 'hiringmanager',
}


class StaffFilterSet(filters.FilterSet):
    is_active__in = filters.BaseInFilter(field_name='is_active', lookup_expr='in')

    group = filters.CharFilter(method='group_filter')

    class Meta:  # noqa
        model = m.User
        fields = ('is_active__in',)

    def group_filter(self, queryset, name, value):
        filter_field = USER_GROUP_FILTER.get(value)

        if value:
            queryset = queryset.filter(**{'{}__isnull'.format(filter_field): False})

        return queryset


class SnapshotFilterSet(filters.FilterSet):
    status__in = filters.BaseInFilter(field_name='status', lookup_expr='in')

    class Meta:
        model = m.ProposalStatusHistory
        fields = ('status',)


class CandidateFilterSet(filters.FilterSet):

    tags__in = filters.BaseInFilter(field_name='tags', distinct=True)

    class Meta:
        model = m.Candidate
        fields = ('tags',)


class CandidateSearchFilter(drf_filters.SearchFilter):
    def filter_queryset(self, request, queryset, view):
        user = request.user if request else None
        profile = user.profile if user else None
        org = profile.org if profile else None

        params = request.query_params if request else dict()
        search = params.get(api_settings.SEARCH_PARAM)

        if not org or not search:
            return super().filter_queryset(request, queryset, view)

        org_content_type, org_id = get_user_org(profile)

        return (
            super().filter_queryset(request, queryset, view).distinct()
            | queryset.filter(
                notes__content_type=org_content_type,
                notes__object_id=org_id,
                notes__text__icontains=search,
            ).distinct()
        )


class DealPipelineFilterSet(filters.FilterSet):
    deal_stage__in = filters.BaseInFilter(field_name='status__deal_stage')

    class Meta:
        model = m.Proposal
        fields = ('deal_stage__in', 'status_last_updated_by')


class CandidateLogFilterSet(filters.FilterSet):
    candidate = filters.CharFilter(
        field_name='object_id', lookup_expr='exact', required=True
    )

    class Meta:  # noqa
        model = Version
        fields = ('candidate',)


class CandidateCommentFilterSet(filters.FilterSet):
    class Meta:  # noqa
        model = m.CandidateComment
        fields = ('candidate',)


class TagFilterSet(filters.FilterSet):
    class Meta:  # noqa
        model = m.Tag
        fields = ('type',)


class NoteActivityFilterSet(filters.FilterSet):
    class Meta:  # noqa
        model = m.NoteActivity
        fields = (
            'proposal',
            'candidate',
            'job',
        )

    def filter_queryset(self, queryset):
        user = self.request.user
        profile = user.profile if user else None
        params = self.request.query_params

        queryset = super().filter_queryset(queryset)
        if not profile:
            return queryset

        param_model_pairs = [
            ('job', m.Job),
            ('candidate', m.Candidate),
            ('proposal', m.Proposal),
        ]
        for param, model in param_model_pairs:
            if param not in params:
                continue
            fn_string = f'apply_{param}s_filter'
            filter_fn = getattr(profile, fn_string, None)
            if filter_fn is None:
                raise NotImplementedError(f'{profile.group} missing {fn_string}')
            list_of_ids = filter_fn(model.objects.all()).values_list('id', flat=True)
            query = {f'{param}__in': list_of_ids}
            queryset = queryset.filter(**query)
        return queryset
