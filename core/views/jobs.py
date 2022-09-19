from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action, api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from core import filters as f
from core import models as m
from core import serializers as s
from core.annotations import (
    annotate_job_agency_member_have_access_since,
    annotate_job_live_proposals,
    annotate_job_proposal_pipeline,
    annotate_job_hired_count,
)
from core.constants import CREATE_UPDATE_ACTIONS, UPDATE_ACTIONS
from core.mixins import ValidateModelMixin
from core.notifications import (
    NOTIFY_JOB_FIELDS_COMPARE,
    NOTIFY_JOB_FIELDS_COMPARE_BY_MATCHING_KEY,
    notify_agency_assigned_job_member,
    # TODO: Restore or remove once notification feature is specified
    # notify_client_assigned_agency,
    # notify_client_updated_job,
    # notify_client_admin_assigned_manager,
    # notify_job_is_filled,
)
from core.permissions import (
    AgencyBaseAccessPolicy,
    BaseAccessPolicy,
    JobFilesAccessPolicy,
    JobPostingAccessPolicy,
    JobsAccessPolicy,
)
from core.utils import (
    compare_model_dicts,
    fix_for_yasg,
    require_user_profile,
)
from core.views.views import FileViewSet


def update_decorator(name):
    return method_decorator(
        name=name,
        decorator=swagger_auto_schema(
            responses={HTTP_200_OK: s.JobUpdateResponseSerializer}
        ),
    )


@method_decorator(
    name='list', decorator=swagger_auto_schema(query_serializer=s.JobQuerySerializer)
)
@method_decorator(
    name='retrieve',
    decorator=swagger_auto_schema(query_serializer=s.JobDetailQuerySerializer),
)
@update_decorator('update')
@update_decorator('partial_update')
class JobViewSet(viewsets.ModelViewSet):
    """Viewset for the Job model."""

    queryset = m.Job.objects.prefetch_related('client')
    permission_classes = (JobsAccessPolicy,)
    filterset_class = f.JobFilterSet
    search_fields = ('id', 'title', 'mission', 'responsibilities', 'requirements')

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        """Return Jobs based on User type."""
        user = self.request.user

        jobs = user.profile.apply_jobs_filter(self.queryset)
        org = user.profile.org

        if isinstance(org, m.Agency):
            jobs = annotate_job_agency_member_have_access_since(jobs, user)

            jobs = jobs.prefetch_related(
                Prefetch(
                    'agency_contracts',
                    queryset=m.JobAgencyContract.objects.filter(
                        agency=user.profile.org
                    ),
                )
            )

        if isinstance(org, m.Client):
            jobs = jobs.prefetch_related(
                Prefetch(
                    'agencies',
                    queryset=m.Agency.objects.filter(job_contracts__is_active=True),
                )
            )

        if self.action == 'list':
            show_pipeline = self.request.query_params.get('show_pipeline')
            if show_pipeline == 'true':
                jobs = annotate_job_proposal_pipeline(jobs, user.profile)

            show_live_proposal_count = self.request.query_params.get(
                'show_live_proposal_count'
            )
            if show_live_proposal_count == 'true':
                jobs = annotate_job_live_proposals(jobs, user.profile)

        else:
            show_pipeline = self.request.query_params.get('show_pipeline')
            if show_pipeline == 'true':
                jobs = annotate_job_proposal_pipeline(jobs, user.profile)

            jobs = annotate_job_hired_count(jobs)

        return jobs

    def get_serializer_class(self):
        """Return different serializer if the action is create or update."""
        if self.action in CREATE_UPDATE_ACTIONS:
            return s.CreateUpdateJobSerializer

        if self.action == 'list':
            return s.JobListSerializer

        return s.JobSerializer

    def get_serializer_context(self):
        """Validate and pass other request data to serializer via context."""
        context = super().get_serializer_context()

        if self.action == 'list':
            query_serializer = s.JobQuerySerializer(
                data=self.request.GET, context=context
            )
            query_serializer.is_valid(raise_exception=True)
            return {**context, **query_serializer.validated_data}
        elif self.action == 'retrieve':
            query_serializer = s.JobDetailQuerySerializer(
                data=self.request.GET, context=context
            )
            query_serializer.is_valid(raise_exception=True)
            return {**context, **query_serializer.validated_data}

        return super().get_serializer_context()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        job_data = s.JobComparisonSerializer(instance, context=serializer.context).data

        self.perform_update(serializer)
        new_job_data = s.JobComparisonSerializer(
            instance, context=serializer.context
        ).data

        job_diff = compare_model_dicts(
            job_data,
            new_job_data,
            compare=NOTIFY_JOB_FIELDS_COMPARE + ['published'],
            compare_as_set=['agencies', 'managers'],
            compare_by_matching_key=NOTIFY_JOB_FIELDS_COMPARE_BY_MATCHING_KEY,
        )

        job_updates = {
            **self.handle_job_status_changed(job_diff),
            **self.handle_job_published(job_diff),
        }

        for attr, value in job_updates.items():
            setattr(instance, attr, value)
        instance.save()

        # TODO: Restore or remove once notification feature is specified
        # notifiable_update_diff = {
        #     key: job_diff[key] for key in job_diff
        #     if key in NOTIFY_JOB_FIELDS_COMPARE | NOTIFY_JOB_FIELDS_COMPARE_BY_MATCHING_KEY
        # }
        #
        # notify_client_updated_job(self.request.user, instance, notifiable_update_diff)
        #
        # notify_client_assigned_agency(self.request.user, instance, job_diff)
        #
        # notify_client_admin_assigned_manager(self.request.user, instance, job_diff)

        invalidate_prefetched_cache(instance)
        return Response(
            {
                **serializer.data,
                'are_postings_outdated': (
                    instance.has_enabled_postings
                    and are_postings_outdated(job_data, new_job_data)
                ),
            }
        )

    @staticmethod
    def handle_job_status_changed(job_diff):
        status_diff = job_diff.get('status')
        if not status_diff:
            return {}

        was_closed = status_diff['from'] in m.JOB_STATUSES_CLOSED
        is_closed = status_diff['to'] in m.JOB_STATUSES_CLOSED

        if was_closed == is_closed:
            return {}

        if is_closed:
            # TODO: Restore or remove once notification feature is specified
            # if new_job_data['status'] == m.JobStatus.FILLED.key:
            #     notify_job_is_filled(self.request.user, instance)
            # TODO (ZOO-1241): Disable postings also
            return dict(closed_at=timezone.now())

        return dict(closed_at=None)

    @staticmethod
    def handle_job_published(job_diff):
        published_diff = job_diff.get('published')
        if not published_diff:
            return {}

        if not published_diff['from'] and published_diff['to']:
            return dict(published_at=timezone.now())

    @action(methods=['patch'], detail=True)
    @swagger_auto_schema(operation_id='assign_job_member')
    def assign_member(self, request, pk, **kwargs):
        job = self.get_object()

        serializer = s.AssignJobMemberSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        assignee = serializer.validated_data.get('assignee')
        job.assign_member(assignee)

        notify_agency_assigned_job_member(self.request.user, job, assignee.id)

        assignees = s.JobAssigneeSerializer(
            job.assignees, many=True, context={'request': request}
        ).data

        return Response(assignees)

    @action(methods=['patch'], detail=True)
    @swagger_auto_schema(operation_id='withdraw_job_member')
    def withdraw_member(self, request, pk, **kwargs):
        job = self.get_object()

        serializer = s.AssignJobMemberSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        assignee = serializer.validated_data.get('assignee')
        job.withdraw_member(assignee)

        assignees = s.JobAssigneeSerializer(
            job.assignees, many=True, context={'request': request}
        ).data

        return Response(assignees)

    @action(methods=['post'], detail=True)
    @swagger_auto_schema(operation_id='job_import_longlist')
    def import_longlist(self, request, *args, **kwargs):
        job = self.get_object()
        serializer = s.JobImportLonglistSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        job.import_longlist(actor=request.user, **serializer.validated_data)

        return Response({})

    def perform_create(self, serializer):
        job = serializer.save()
        if job.interview_templates.count() < 1:
            job.create_default_interview_templates()


class JobValidateViewSet(ValidateModelMixin, viewsets.GenericViewSet):
    """Viewset for validating Job model."""

    queryset = m.Job.objects.all()
    get_queryset = JobViewSet.get_queryset
    permission_classes = (BaseAccessPolicy,)
    serializer_class = s.CreateUpdateJobSerializer


@api_view(['GET'])
@parser_classes((MultiPartParser,))
def get_job_file_public(request, uuid, pk):
    """Viewset for sharing public JobFiles"""
    job_file = get_object_or_404(
        m.JobFile, job__private_posting__public_uuid=uuid, pk=pk
    )
    if job_file.file.name == '':
        return Response({'detail': _('Not found.')}, 404)

    filename = job_file.file.name.split('/')[-1]
    response = HttpResponse(job_file.file, content_type='application/force-download')
    response['Content-Disposition'] = 'inline; filename="{}"'.format(filename)
    return response


class JobFileViewSet(FileViewSet, mixins.UpdateModelMixin):
    """Viewset for the CandidateFile model."""

    queryset = m.JobFile.objects.all()
    permission_classes = (JobFilesAccessPolicy,)
    serializer_class = s.JobFileSerializer

    def get_serializer_class(self):
        if self.action in UPDATE_ACTIONS:
            return s.UpdateJobFileSerializer
        return super().get_serializer_class()

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        """Return Job files based on User type."""
        return self.request.user.profile.apply_job_files_filter(self.queryset)


class JobAgencyContractViewSet(
    viewsets.GenericViewSet, mixins.UpdateModelMixin, mixins.RetrieveModelMixin
):
    permission_classes = (AgencyBaseAccessPolicy,)
    queryset = m.JobAgencyContract.objects.all()
    serializer_class = s.JobAgencyContractSerializer

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        return self.queryset.filter(agency=self.request.user.profile.org,)


class PrivateJobPostingViewSet(
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
):
    queryset = m.PrivateJobPosting.objects.all()
    serializer_class = s.PrivateJobPostingSerializer
    permission_classes = (JobPostingAccessPolicy,)
    lookup_field = 'job_id'
    lookup_url_kwarg = 'job_id'

    def get_queryset(self):
        return super().get_queryset()


class PrivateJobPostingPublicViewSet(
    viewsets.GenericViewSet, mixins.RetrieveModelMixin
):
    """Viewset for the public Job objects."""

    queryset = m.PrivateJobPosting.public_objects.all()
    serializer_class = s.PrivateJobPostingPublicSerializer
    lookup_field = 'public_uuid'
    lookup_url_kwarg = 'uuid'


class PrivateJobPostingValidateViewSet(ValidateModelMixin, viewsets.GenericViewSet):
    queryset = m.PrivateJobPosting.objects.all()
    permission_classes = (BaseAccessPolicy,)
    serializer_class = s.PrivateJobPostingSerializer


class CareerSiteJobPostingViewSet(
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
):
    queryset = m.CareerSiteJobPosting.objects.all()
    serializer_class = s.CareerSiteJobPostingSerializer
    permission_classes = (JobPostingAccessPolicy,)
    lookup_field = 'job_id'
    lookup_url_kwarg = 'job_id'


class CareerSiteJobPostingValidateViewSet(ValidateModelMixin, viewsets.GenericViewSet):
    queryset = m.CareerSiteJobPosting.objects.all()
    permission_classes = (BaseAccessPolicy,)
    serializer_class = s.CareerSiteJobPostingSerializer


def invalidate_prefetched_cache(instance):
    if getattr(instance, '_prefetched_objects_cache', None):
        # If 'prefetch_related' has been applied to a queryset, we need to
        # forcibly invalidate the prefetch cache on the instance.
        instance._prefetched_objects_cache = {}


def are_postings_outdated(job_data, new_job_data):
    comparison_result = compare_posting_fields(job_data, new_job_data)
    return len(comparison_result) > 0


NOT_EDITABLE_FIELDS = {'created_at', 'updated_at'}


def compare_posting_fields(job_data, new_job_data):
    return compare_model_dicts(
        job_data,
        new_job_data,
        compare=[
            field.name
            for field in m.BaseJob._meta.fields
            if field.name not in NOT_EDITABLE_FIELDS
        ],
        compare_by_matching_key=[
            ('skills', 'id', dict(compare=['name'])),
            ('required_languages', 'id', dict(compare=['language', 'level'])),
            ('questions', 'id', dict(compare=['text'])),
        ],
    )
