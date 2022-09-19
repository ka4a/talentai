from collections import namedtuple, OrderedDict
from datetime import timedelta, datetime

from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, F, Avg, DurationField, Count, FloatField, Case
from django.db.models import When, CharField, Value, Max, Min, Subquery
from django.db.models.functions import ExtractDay, Cast, TruncDay, TruncMonth, TruncWeek
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core import models as m
from core import serializers as s
from core import filters as f
from core.annotations import aggregate_proposals_stats, annotate_count_by_date
from core.models import User, Proposal
from core.permissions import (
    IsTalentAssociate,
    add_permissions,
    get_permission_profiles_have_access,
)
from core.utils import require_user_profile, fix_for_yasg


class BaseGranularity(object):
    @staticmethod
    def add(d):
        raise NotImplementedError

    @staticmethod
    def floor(d):
        raise NotImplementedError

    @classmethod
    def range(cls, start_date, end_date):
        _add = cls.add

        i = start_date
        while i < end_date:
            yield i
            i = _add(i)

    @classmethod
    def ceil(cls, d):
        floored = cls.floor(d)
        return cls.add(floored)

    @staticmethod
    def subtract(d):
        raise NotImplementedError

    @staticmethod
    def trunc(d):
        raise NotImplementedError


class MonthGranularity(BaseGranularity):
    @staticmethod
    def add(d):
        if d.month == 12:
            return d.replace(year=d.year + 1, month=1)

        return d.replace(month=d.month + 1)

    @staticmethod
    def floor(d):
        return d.replace(day=1)

    @staticmethod
    def subtract(d):
        if d.month == 1:
            return d.replace(year=d.year - 1, month=12)

        return d.replace(month=d.month - 1)

    @staticmethod
    def trunc(d):
        return TruncMonth(d)


class WeekGranularity(BaseGranularity):
    @staticmethod
    def add(d):
        return d + timedelta(weeks=1)

    @staticmethod
    def floor(d):
        """Return Monday of `d` week"""

        return d - timedelta(days=d.weekday())

    @staticmethod
    def subtract(d):
        return d - timedelta(weeks=1)

    @staticmethod
    def trunc(d):
        return TruncWeek(d)


class DayGranularity(BaseGranularity):
    @staticmethod
    def add(d):
        return d + timedelta(days=1)

    @staticmethod
    def floor(d):
        return datetime.combine(d, datetime.min.time()).date()

    @staticmethod
    def subtract(d):
        return d - timedelta(days=1)

    @staticmethod
    def trunc(d):
        return TruncDay(d)


GRANULARITY = {
    'week': WeekGranularity,
    'month': MonthGranularity,
    'day': DayGranularity,
}


def count_overlapping_periods(granularity, date_ranges, start_date=None, end_date=None):
    """

    accepts list of dates [(start_date, end_date), ...]
    returns {
        period_first_date (month, week):
        count of overlapping periods for this period
    }
    """

    periods = [
        (
            granularity.floor(period_start.date()),
            # checks if not closed
            (
                granularity.floor(period_end.date())
                if period_end
                else granularity.floor(timezone.now().date())
            ),
        )
        for period_start, period_end in date_ranges
    ]

    if start_date is None and periods:
        start_date = min(i[0] for i in periods)

    if end_date is None and periods:
        end_date = max(i[1] for i in periods)

    if start_date is None or end_date is None:
        return []

    result = {
        d: 0
        for d in granularity.range(
            granularity.floor(start_date), granularity.ceil(end_date)
        )
    }

    for period_start, period_end in periods:
        for chart_point in granularity.range(period_start, granularity.add(period_end)):
            if chart_point in result:
                result[chart_point] += 1

    return sorted(result.items(), key=lambda x: x[0])


def get_jobs_of_owner(user):
    return m.Job.objects.filter(owner=user)


def get_jobs_of_hiring_manager(user):
    return m.Job.objects.filter(_managers=user)


def get_jobs_by_function(function):
    return m.Job.objects.filter(function=function)


def gen_add_first_none_item(queryset):
    yield None
    yield from queryset


def get_related_jobs(queryset, pk, get_label, get_jobs, qs_wrapper=None):
    if pk:
        queryset = queryset.filter(id=pk)
    elif qs_wrapper:
        queryset = qs_wrapper(queryset)

    mapping = ((item, get_jobs(item)) for item in queryset)

    return mapping, get_label


def owner_profile_query(**kwargs):
    prefixes = [
        'owner__hiringmanager__{}',
        'owner__talentassociate__{}',
    ]
    result = None

    for prefix in prefixes:
        profile_type_query = Q(
            **{prefix.format(key): value for key, value in kwargs.items()}
        )
        result = result | profile_type_query if result else profile_type_query

    return result


def get_related_jobs_via_filter(user, filter_type, filter_value=None):

    if filter_type == 'team':

        def get_jobs_of_team(team=None):
            if team is None:
                return m.Job.objects.filter(
                    owner_profile_query(teams__isnull=True, id__isnull=False),
                    org_id=user.profile.org.id,
                    org_content_type=ContentType.objects.get_for_model(
                        user.profile.org
                    ),
                )

            if isinstance(team.organization, m.Client):
                return m.Job.objects.filter(owner_profile_query(teams=team))

            raise NotImplementedError

        return get_related_jobs(
            queryset=user.profile.org.teams.all(),
            pk=filter_value,
            get_label=lambda team: team.name if team else _('Unassigned department'),
            get_jobs=get_jobs_of_team,
            qs_wrapper=gen_add_first_none_item,
        )

    if filter_type == 'hiring_manager':
        return get_related_jobs(
            queryset=m.User.objects.filter(hiringmanager__client=user.profile.client),
            pk=filter_value,
            get_label=lambda user: user.full_name,
            get_jobs=get_jobs_of_hiring_manager,
        )

    if filter_type == 'owner':
        return get_related_jobs(
            queryset=user.profile.client.members,
            pk=filter_value,
            get_label=lambda user: user.full_name,
            get_jobs=get_jobs_of_owner,
        )

    if filter_type in {'job_category', 'function'}:
        return get_related_jobs(
            queryset=m.Function.objects.all(),
            pk=filter_value,
            get_label=lambda function: function.title,
            get_jobs=lambda function: user.profile.apply_jobs_filter(
                get_jobs_by_function(function)
            ),
        )

    raise ValueError('Invalid filter type')


def filter_jobs_open(jobs, start_date, end_date):
    return jobs.filter(Q(closed_at__gte=start_date) | Q(closed_at__isnull=True)).filter(
        published=True, published_at__lt=end_date,
    )


def get_job_open_average(jobs):
    return (
        jobs.filter(published=True, closed_at__isnull=False,)
        .annotate(
            open_period=ExtractDay(
                Cast(F('closed_at') - F('published_at'), DurationField())
            )
        )
        .aggregate(Avg('open_period'))['open_period__avg']
    )


def get_hiring_managers(user):
    return User.objects.filter(manager_for_jobs__client=user.profile.client).distinct()


def get_conversion_ratios(proposals, table_description):
    result = []

    for initial_status, status_list in table_description:
        row = {'id': initial_status, 'from_status': initial_status}
        result.append(row)

        for proposal_status in status_list:
            passed = Cast(
                Count(
                    'id',
                    distinct=True,
                    filter=Q(status_history__status__group=proposal_status),
                ),
                FloatField(),
            )
            total = Cast(
                Count(
                    'id',
                    distinct=True,
                    filter=Q(status_history__status__group=initial_status),
                ),
                FloatField(),
            )

            r = proposals.aggregate(
                passed_ann=passed,
                total_ann=total,
                result_ann=Case(
                    When(Q(total_ann=0), then=0),
                    default=passed / total,
                    output_field=FloatField(),
                ),
            )

            row[proposal_status] = r['result_ann']

    return result


STATUS_GROUPS = ('new', 'approved', 'interviewing', 'offer', 'offer_accepted')


def get_conversion_ratio(proposals, groups=STATUS_GROUPS):
    result = []

    for status_group in groups:
        passed = Cast(
            Count(
                'id',
                distinct=True,
                filter=Q(status_history__status__group=status_group),
            ),
            FloatField(),
        )

        result.append(
            {
                'status_group': status_group,
                'value': proposals.aggregate(result_ann=passed)['result_ann'],
            }
        )

    return result


def take_of_period(qs, func):
    return qs.filter(
        changed_at__in=Subquery(
            qs.values('proposal',)
            .annotate(date=func('changed_at'))
            .values('date',)
            .order_by('date')
        )
    )


def take_first_of_period(qs):
    return take_of_period(qs, Min)


def take_last_of_period(qs):
    return take_of_period(qs, Max)


def get_candidate_statuses_stats(qs, params):
    return list(
        annotate_count_by_date(
            take_first_of_period(qs), 'proposal', 'changed_at', params.granularity.trunc
        )
    )


def get_changed_at_filter(date_start, date_end):
    date_filter = {}
    if date_start:
        date_filter['changed_at__range'] = (date_start, date_end)
    else:
        date_filter['changed_at__lte'] = date_end

    return date_filter


# TODO(ZOO-829) update analytics
# SHORTLISTED_STATUS_GROUPS = ['new']
# INTERVIEWED_STATUS_GROUPS = (
#     SHORTLISTED_STATUS_GROUPS + PROPOSAL_STATUS_GROUP_CATEGORIES['interviewed']
# )
# CONTACTED_STATUS_GROUPS = (
#     INTERVIEWED_STATUS_GROUPS + PROPOSAL_STATUS_GROUP_CATEGORIES['contacted']
# )
# IDENTIFIED_STATUS_GROUPS = (
#     CONTACTED_STATUS_GROUPS + PROPOSAL_STATUS_GROUP_CATEGORIES['identified']
# )
SHORTLISTED_STATUS_GROUPS = (
    INTERVIEWED_STATUS_GROUPS
) = CONTACTED_STATUS_GROUPS = IDENTIFIED_STATUS_GROUPS = []


def get_identified_stats(params, date_end, proposals):
    identified_stats = m.ProposalStatusHistory.objects.filter(
        proposal__in=proposals,
        proposal__job=params.job,
        status__group__in=IDENTIFIED_STATUS_GROUPS,
        changed_at__lte=date_end,
    )

    return get_candidate_statuses_stats(identified_stats, params)


def get_contacted_stats(params, date_end, proposals):
    contacted_stats = m.ProposalStatusHistory.objects.filter(
        proposal__in=proposals,
        status__group__in=CONTACTED_STATUS_GROUPS,
        proposal__job=params.job,
        changed_at__lte=date_end,
    )

    return get_candidate_statuses_stats(contacted_stats, params)


def get_interviewed_stats(params, date_end, proposals):
    interviewed_stats = m.ProposalStatusHistory.objects.filter(
        proposal__in=proposals,
        proposal__job=params.job,
        status__group__in=INTERVIEWED_STATUS_GROUPS,
        changed_at__lte=date_end,
    )

    return get_candidate_statuses_stats(interviewed_stats, params)


def get_shortlisted_stats(params, date_end, proposals):
    shortlist_stats = m.ProposalStatusHistory.objects.filter(
        proposal__in=proposals,
        proposal__job=params.job,
        status__group__in=SHORTLISTED_STATUS_GROUPS,
        changed_at__lte=date_end,
    )

    return get_candidate_statuses_stats(shortlist_stats, params)


def get_proposals_snapshot(apply_proposals_filter, job, date_start, date_end):
    return take_last_of_period(
        apply_proposals_filter(
            m.ProposalStatusHistory.objects.filter(
                proposal__job=job, **get_changed_at_filter(date_start, date_end)
            )
        )
    )


DefaultAnalyticsParameters = namedtuple(
    'DefaultAnalyticsParameters',
    ['filter_type', 'filter_value', 'date_start', 'date_end', 'granularity', 'data'],
)


DefaultJobAnalyticsParameters = namedtuple(
    'DefaultJobAnalyticsParameters', ['date_start', 'date_end', 'granularity', 'job']
)


DefaultProposalsSnapshotParameters = namedtuple(
    'DefaultProposalsSnapshotParameters',
    ['date', 'job', 'granularity', 'date_start', 'date_end'],
)


def parse_default_parameters(request, serializer=s.StatsQuerySerializer):
    query_serializer = serializer(
        data=request.query_params, context={'request': request}
    )
    query_serializer.is_valid(raise_exception=True)

    filter_type = query_serializer.validated_data['filter_type']
    filter_value = query_serializer.validated_data.get('filter_value')

    date_start = query_serializer.validated_data['date_start']
    date_end = query_serializer.validated_data['date_end']

    granularity = None
    granularity_value = query_serializer.validated_data.get('granularity')
    if granularity_value:
        granularity = GRANULARITY[granularity_value]

    return DefaultAnalyticsParameters(
        filter_type,
        filter_value,
        date_start,
        date_end,
        granularity,
        query_serializer.validated_data,
    )


def parse_default_jd_parameters(request, serializer=s.JobAnalyticsQuerySerializer):
    query_serializer = serializer(
        data=request.query_params, context={'request': request}
    )
    query_serializer.is_valid(raise_exception=True)
    date_start = query_serializer.validated_data.get('date_start')
    date_end = query_serializer.validated_data.get('date_end')
    job = query_serializer.validated_data.get('job')

    granularity = None
    granularity_value = query_serializer.validated_data.get('granularity')
    if granularity_value:
        granularity = GRANULARITY[granularity_value]

    return DefaultJobAnalyticsParameters(date_start, date_end, granularity, job)


def parse_proposal_snapshot_parameters(
    request, serializer=s.ProposalsSnapshotQuerySerializer
):
    query_serializer = serializer(
        data=request.query_params, context={'request': request}
    )
    query_serializer.is_valid(raise_exception=True)

    job = query_serializer.validated_data.get('job')
    date = query_serializer.validated_data.get('date')
    date_start = query_serializer.validated_data.get('date_start')
    date_end = query_serializer.validated_data.get('date_end')

    granularity = None
    granularity_value = query_serializer.validated_data.get('granularity')
    if granularity_value:
        granularity = GRANULARITY[granularity_value]

    return DefaultProposalsSnapshotParameters(
        date, job, granularity, date_start, date_end
    )


def granulate_date_range(params, start='date_start', end='date_end'):
    granularity = params.granularity
    date_start = getattr(params, start)
    date_end = getattr(params, end)

    date_start = granularity.floor(date_start)
    date_end = granularity.add(granularity.floor(date_end))

    return date_start, date_end


def get_jd_stats(params, get_stats, user):
    date_start, date_end = granulate_date_range(params)

    available_proposals = user.profile.apply_proposals_filter(m.Proposal.objects)
    stats = get_stats(params, date_end, available_proposals)

    result_dict = OrderedDict(
        (date, (0, 0)) for date in params.granularity.range(date_start, date_end)
    )

    dates = [date for date in result_dict.keys()]

    for stat in stats:
        stat_date = stat['date'].date()
        result_date = stat_date if stat_date >= date_start else date_start

        line, diff = result_dict[result_date]
        result_dict[result_date] = (line + stat['value'], diff + stat['value'])

    for date in dates[1:]:
        prev_value, prev_diff = result_dict[params.granularity.subtract(date)]
        value, diff = result_dict[date]

        grown_value = prev_value + value

        result_dict[date] = (grown_value, diff)

    result = [
        {'date': date.isoformat(), 'value': value, 'diff': diff}
        for date, (value, diff) in result_dict.items()
    ]

    return result


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    @action(methods=['get'], detail=False)
    @swagger_auto_schema(query_serializer=s.StatsQuerySerializer)
    @add_permissions([IsTalentAssociate()])
    def conversion_ratio(self, request, *args, **kwargs):
        params = parse_default_parameters(request)
        if not hasattr(request.user, 'profile') or request.user.profile is None:
            return Response({})

        if params.filter_value:
            job_mapping, get_obj_label = get_related_jobs_via_filter(
                request.user, params.filter_type, params.filter_value,
            )
            proposals_filter = Q(
                job__in=filter_jobs_open(
                    next(job_mapping)[1], params.date_start, params.date_end
                )
            )
            proposals = m.Proposal.shortlist.filter(proposals_filter)
        else:
            proposals = request.user.profile.apply_proposals_filter(
                m.Proposal.shortlist.all()
            ).filter(
                job__in=filter_jobs_open(
                    m.Job.objects, params.date_start, params.date_end
                )
            )

        return Response(get_conversion_ratio(proposals))

    @action(methods=['get'], detail=False)
    @swagger_auto_schema(query_serializer=s.StatsQuerySerializer)
    @add_permissions([IsTalentAssociate()])
    def proposal_status_count(self, request, *args, **kwargs):
        params = parse_default_parameters(request)

        job_mapping, get_obj_label = get_related_jobs_via_filter(
            request.user, params.filter_type, params.filter_value,
        )

        result = []

        for obj, job_queryset in job_mapping:
            jobs = filter_jobs_open(job_queryset, params.date_start, params.date_end)
            proposals = Proposal.shortlist.filter(job__in=jobs)
            values = aggregate_proposals_stats(proposals)

            if params.filter_value or any(i > 0 for i in values.values()):
                # add empty results only if specific obj filtered
                result.append({'name': get_obj_label(obj), 'proposal_pipeline': values})

        return Response(result)

    @action(methods=['get'], detail=False)
    @swagger_auto_schema(query_serializer=s.StatsQuerySerializer)
    @add_permissions([IsTalentAssociate()])
    def job_average_open(self, request, *args, **kwargs):
        params = parse_default_parameters(request)

        job_mapping, get_obj_label = get_related_jobs_via_filter(
            request.user, params.filter_type, params.filter_value,
        )

        result = []

        for obj, job_queryset in job_mapping:
            value = get_job_open_average(
                filter_jobs_open(job_queryset, params.date_start, params.date_end)
            )

            if not params.filter_value and not value:
                continue

            result.append({'name': get_obj_label(obj), 'open_period_avg': value})

        return Response(result)

    @action(methods=['get'], detail=False)
    @swagger_auto_schema(query_serializer=s.DateRangeSerializer)
    @add_permissions([IsTalentAssociate()])
    def job_average_open_kpi(self, request, *args, **kwargs):
        query_serializer = s.DateRangeSerializer(
            data=request.query_params, context={'request': request}
        )
        query_serializer.is_valid(raise_exception=True)

        date_start = query_serializer.validated_data['date_start']
        date_end = query_serializer.validated_data['date_end']

        job_queryset = filter_jobs_open(
            request.user.profile.apply_jobs_filter(m.Job.objects), date_start, date_end
        )

        value = get_job_open_average(job_queryset)

        return Response({'value': value})

    @action(methods=['get'], detail=False)
    @swagger_auto_schema(query_serializer=s.StatsChartQuerySerializer)
    @add_permissions([IsTalentAssociate()])
    def open_jobs(self, request, *args, **kwargs):
        params = parse_default_parameters(request, s.StatsChartQuerySerializer)

        if params.filter_value:
            job_mapping, get_obj_label = get_related_jobs_via_filter(
                request.user, params.filter_type, params.filter_value,
            )
            job_queryset = next(job_mapping)[1]
        else:
            job_queryset = request.user.profile.apply_jobs_filter(m.Job.objects)

        job_published_ranges = (
            i[1:]
            for i in filter_jobs_open(
                jobs=job_queryset,
                start_date=params.date_start,
                end_date=params.date_end,
            ).values_list('id', 'published_at', 'closed_at')
        )  # id to force add if .distinct() is used

        result = [
            {'date': d.isoformat(), 'value': open_jobs}
            for d, open_jobs in count_overlapping_periods(
                params.granularity,
                job_published_ranges,
                params.date_start,
                params.date_end,
            )
        ]

        return Response(result)

    @action(methods=['get'], detail=False)
    @add_permissions([IsTalentAssociate()])
    def contracts(self, request, *args, **kwargs):
        return Response(
            {
                'contracts': m.Contract.objects.filter(
                    request.user.profile.contracts_filter
                ).count()
            }
        )

    @action(methods=['get'], detail=False)
    @swagger_auto_schema(query_serializer=s.AnalyticsSourcesQuerySerializer)
    @add_permissions([IsTalentAssociate()])
    def sources(self, request, *args, **kwargs):
        params = parse_default_parameters(request, s.AnalyticsSourcesQuerySerializer)

        if params.filter_value:
            job_mapping, get_obj_label = get_related_jobs_via_filter(
                request.user, params.filter_type, params.filter_value,
            )
            proposals_filter = Q(
                job__in=filter_jobs_open(
                    next(job_mapping)[1], params.date_start, params.date_end
                )
            )
            candidates = m.Proposal.shortlist.filter(proposals_filter)
        else:
            candidates = request.user.profile.apply_proposals_filter(
                m.Proposal.shortlist.filter(
                    Q(
                        job__in=filter_jobs_open(
                            m.Job.objects, params.date_start, params.date_end
                        )
                    )
                )
            )

        if params.data['hired']:
            candidates = candidates.filter(status__group='offer_accepted')

        agency_content_type = ContentType.objects.get(app_label='core', model='agency')

        c = Case(
            When(
                Q(candidate__org_content_type=agency_content_type),
                Value('External Agencies'),
            ),
            default=F('candidate__source'),
            output_field=CharField(),
        )

        result = candidates.values(source_ann=c).annotate(dcount=Count('source_ann'))

        return Response(
            [{'name': i['source_ann'], 'value': i['dcount']} for i in result]
        )

    @action(methods=['get'], detail=False)
    @swagger_auto_schema(query_serializer=s.StatsChartQuerySerializer)
    @add_permissions([IsTalentAssociate()])
    def candidates_hired(self, request, *args, **kwargs):
        params = parse_default_parameters(request, s.StatsChartQuerySerializer)

        candidates = request.user.profile.apply_proposals_filter(
            m.Proposal.shortlist.filter(status__group='offer_accepted')
        )
        if params.filter_value:
            job_mapping, get_obj_label = get_related_jobs_via_filter(
                request.user, params.filter_type, params.filter_value,
            )
            candidates = m.Proposal.shortlist.filter(
                Q(job__in=next(job_mapping)[1])
            ).filter(status__group='offer_accepted')

        hired_dates = (
            candidates.values(
                hired_date_ann=Max(
                    'status_history__changed_at',
                    filter=Q(status__group='offer_accepted'),
                )
            )
            .filter(
                hired_date_ann__gte=params.date_start,
                hired_date_ann__lt=params.date_end,
            )
            .values_list('hired_date_ann')
        )

        result_dict = {
            d: 0
            for d in params.granularity.range(
                params.granularity.floor(params.date_start),
                params.granularity.add(params.granularity.floor(params.date_end)),
            )
        }

        for (hired_date,) in hired_dates:
            result_dict[params.granularity.floor(hired_date.date())] += 1

        result = [{'date': d.isoformat(), 'value': c} for d, c in result_dict.items()]

        return Response(result)

    @action(methods=['get'], detail=False)
    @swagger_auto_schema(query_serializer=s.StatsQuerySerializer)
    @add_permissions([IsTalentAssociate()])
    def candidate_decline_reason(self, request, *args, **kwargs):
        params = parse_default_parameters(request)

        if params.filter_value:
            job_mapping, get_obj_label = get_related_jobs_via_filter(
                request.user, params.filter_type, params.filter_value,
            )
            proposals_filter = Q(
                job__in=filter_jobs_open(
                    next(job_mapping)[1], params.date_start, params.date_end
                )
            )
            candidates = m.Proposal.shortlist.filter(proposals_filter).filter(
                decline_reasons__isnull=False
            )

        else:
            candidates = request.user.profile.apply_proposals_filter(
                m.Proposal.shortlist.filter(
                    Q(
                        job__in=filter_jobs_open(
                            m.Job.objects, params.date_start, params.date_end
                        )
                    )
                ).filter(decline_reasons__isnull=False)
            )

        decline_reasons = {
            i['decline_reasons']: i['id__count']
            for i in candidates.values('decline_reasons').annotate(Count('id'))
        }
        decline_reason_objects = {
            r.id: r.text
            for r in m.ReasonDeclineCandidateOption.objects.filter(
                id__in=decline_reasons.keys()
            )
        }

        results = [
            {'name': decline_reason_objects[reason_id], 'value': count}
            for reason_id, count in decline_reasons.items()
        ]

        return Response(results)

    @action(methods=['get'], detail=False)
    @swagger_auto_schema(query_serializer=s.JobAnalyticsQuerySerializer)
    @add_permissions(
        [
            get_permission_profiles_have_access(
                m.AgencyManager, m.AgencyAdministrator, m.TalentAssociate, m.Recruiter
            )()
        ]
    )
    def candidates_statuses(self, request, *args, **kwargs):
        user = request.user
        params = parse_default_jd_parameters(request)

        identified = get_jd_stats(params, get_identified_stats, user)
        contacted = get_jd_stats(params, get_contacted_stats, user)
        interviewed = get_jd_stats(params, get_interviewed_stats, user)
        shortlisted = get_jd_stats(params, get_shortlisted_stats, user)

        result = {"line_data": [], "diffs": []}

        date_start, date_end = granulate_date_range(params)

        i = 0
        for d in params.granularity.range(date_start, date_end):
            result["line_data"].append(
                {
                    'date': d.isoformat(),
                    "identified": identified[i]['value'],
                    "contacted": contacted[i]['value'],
                    "interviewed": interviewed[i]['value'],
                    "shortlisted": shortlisted[i]['value'],
                }
            )
            result["diffs"].append(
                {
                    "date": d.isoformat(),
                    "identified": identified[i]['diff'],
                    "contacted": contacted[i]['diff'],
                    "interviewed": interviewed[i]['diff'],
                    "shortlisted": shortlisted[i]['diff'],
                }
            )
            i += 1

        return Response(result)


class BaseProposalSnapshotViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = m.ProposalStatusHistory.objects.all()
    permission_classes = (IsAuthenticated,)
    filterset_class = f.SnapshotFilterSet
    serializer_class = s.ProposalsSnapshotSerializer
    ordering_fields = ('changed_at',)

    query_serializer = s.ProposalsSnapshotQuerySerializer

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        params = parse_proposal_snapshot_parameters(self.request)

        date_start, date_end = self.get_date_range(params)

        return get_proposals_snapshot(
            self.apply_proposals_filter, params.job, date_start, date_end
        )

    @swagger_auto_schema(query_serializer=query_serializer)
    @add_permissions(
        [
            get_permission_profiles_have_access(
                m.AgencyManager, m.AgencyAdministrator, m.TalentAssociate, m.Recruiter
            )()
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(methods=['get'], detail=False)
    @swagger_auto_schema(query_serializer=query_serializer)
    @add_permissions([IsTalentAssociate()])
    def hidden_proposals(self, request, *args, **kwargs):
        params = parse_proposal_snapshot_parameters(self.request)

        date_start, date_end = self.get_date_range(params)

        hidden = get_proposals_snapshot(
            self.apply_hidden_proposals_filter, params.job, date_start, date_end
        ).count()

        return Response({"hidden": hidden})

    # Exclude unavailable proposals such as Agencies' longlisted ones
    # TODO: Client/agency contracting should define permissions for
    # TODO: candidates availability. Corresponding filters should be here
    def apply_proposals_filter(self, qs):
        return qs.filter(
            proposal__in=self.request.user.profile.apply_proposals_filter(
                m.Proposal.objects.all()
            )
        )

    def apply_hidden_proposals_filter(self, qs):
        return qs.exclude(
            proposal__in=self.request.user.profile.apply_proposals_filter(
                m.Proposal.objects.all()
            )
        )

    def get_date_range(self, params):
        raise NotImplemented()


class ProposalSnapshotDiffViewSet(BaseProposalSnapshotViewSet):
    def get_date_range(self, params):
        return granulate_date_range(params, 'date', 'date')


class ProposalSnapshotStateViewSet(BaseProposalSnapshotViewSet):
    def get_date_range(self, params):
        date_start, date_end = granulate_date_range(params, 'date_start', 'date')
        return None, date_end
