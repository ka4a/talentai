from django.contrib.postgres.fields.array import ArrayField
from django.db.models import Max, Q, Prefetch, JSONField, IntegerField
from django.db.models.expressions import Case, Value, When
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema, no_body
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.response import Response

from core import filters as f
from core import models as m
from core import serializers as s
from core.tasks import email_public_candidate_application_confirmation

from core.notifications import (
    notify_candidate_proposed_for_job,
    notify_client_changed_proposal_status,
    notify_interview_assessment_added,
    notify_proposal_interview_canceled,
    notify_proposal_interview_confirmed,
    notify_proposal_interview_rejected,
    notify_proposal_moved,
    notify_job_is_filled,
    notify_client_candidate_public_application,
    notify_interview_schedule_sent,
)
from core.permissions import (
    BaseAccessPolicy,
    ProposalInterviewsAccessPolicy,
    ProposalQuestionAccessPolicy,
    ProposalsAccessPolicy,
)
from core.utils import (
    compare_model_dicts,
    fix_for_yasg,
    has_profile,
    require_user_profile,
)

from core.constants import (
    CREATE_ACTIONS,
    DEFAULT_CLIENT_QUICK_ACTION_MAPPING,
    UPDATE_ACTIONS,
    CREATE_UPDATE_ACTIONS,
)


@method_decorator(
    decorator=swagger_auto_schema(query_serializer=s.ProposalRetrieveQuerySerializer),
    name='retrieve',
)
class ProposalViewSet(viewsets.ModelViewSet):
    """Viewset for the Proposal model."""

    queryset = (
        m.Proposal.objects.annotate(last_activity_at=Max('status_history__changed_at'))
        .select_related(
            'job', 'candidate', 'status', 'created_by', 'moved_from_job', 'moved_by',
        )
        .prefetch_related(
            'candidate__organization', 'candidate__languages', 'status_history'
        )
        .all()
    )
    permission_classes = (ProposalsAccessPolicy,)
    filterset_class = f.ProposalFilterSet
    search_fields = ('candidate__first_name', 'candidate__last_name')

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        """Return Proposals based on User type."""

        profile = self.request.user.profile
        queryset = profile.apply_proposals_filter(self.queryset)

        if self.action == 'retrieve':
            org_type = 'client' if hasattr(profile, 'client') else 'agency'
            queryset = queryset.annotate(
                filtered_quick_actions=Case(
                    *[
                        When(
                            **entry['condition'],
                            then=Value(
                                entry['actions'],
                                output_field=ArrayField(base_field=JSONField()),
                            ),
                        )
                        for entry in DEFAULT_CLIENT_QUICK_ACTION_MAPPING
                    ],
                    default=[],
                )
            )
        elif self.action == 'list':
            group_order = m.ProposalStatusGroup.get_keys()
            queryset = queryset.annotate(
                group_order=Case(
                    *[
                        When(
                            status__group=group,
                            then=Value(
                                len(group_order) - pos, output_field=IntegerField()
                            ),
                        )
                        for pos, group in enumerate(group_order)
                    ],
                ),
            ).order_by('group_order', 'last_activity_at',)

        return queryset

    def get_serializer_class(self):
        """Return different serializer if the action is create."""
        if self.action in CREATE_ACTIONS:
            return s.CreateProposalSerializer
        if self.action in UPDATE_ACTIONS:
            if getattr(self, 'swagger_fake_view', False):
                return s.YasgUpdateProposalSerializer

            if (
                has_profile(self.request.user, 'agency')
                and self.get_object().status.stage
                in m.ProposalStatusStage.get_longlist_keys()
            ):
                return s.UpdateProposalByAgencySerializer

            return s.UpdateProposalSerializer

        profile = self.request.user.profile

        if self.action == 'retrieve':
            if profile.has_full_candidate_field_access:
                return s.RetrieveProposalSerializer
            return s.BasicRetrieveProposalSerializer

        if profile.has_full_candidate_field_access:
            return s.ProposalSerializer
        return s.BasicProposalSerializer

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(responses={201: 'CREATED'})
    def batch_create(self, request, *args, **kwargs):
        serializer = s.CreateProposalSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(methods=['patch'], detail=True)
    @swagger_auto_schema(request_body=s.ProposalMoveBodySerializer)
    def move_to_job(self, request, *args, **kwargs):
        """Move proposal to other job."""
        proposal = self.get_object()

        serializer = s.ProposalMoveBodySerializer(
            data=request.data, instance=proposal, context={'request': self.request}
        )
        serializer.is_valid(raise_exception=True)

        serializer.save(
            moved_from_job=proposal.job, moved_by=request.user,
        )

        notify_proposal_moved(self.request.user, proposal)

        return Response({'detail': _('Moved.')})

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(
        responses={201: 'CREATED'}, request_body=s.PublicCreateProposalSerializer
    )
    def public_application(self, request, *args, **kwargs):
        data = request.data
        serializer = s.PublicCreateProposalSerializer(
            data=data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        job = m.Job.objects.get(pk=data['job'])
        posting = getattr(job, data['posting'])
        self.perform_create(
            serializer, user=m.User.objects.get(pk=job.owner.id), posting=posting
        )

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(
        responses={200: 'OK'}, request_body=s.PublicCreateProposalSerializer
    )
    def validate_public_application(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        context_data = self.get_serializer_context()
        context_data['is_create'] = False
        serializer = s.PublicCreateProposalSerializer(
            data=request.data, context=context_data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        return Response({})

    @action(methods=['post'], detail=True)
    @swagger_auto_schema(
        operation_id='proposal_quick_actions',
        responses={200: 'OK'},
        request_body=s.QuickActionRequestSerializer,
    )
    def quick_actions(self, request, *args, **kwargs):
        proposal = self.get_object()
        serializer_context = dict(**self.get_serializer_context(), proposal=proposal)
        serializer = s.QuickActionRequestSerializer(
            data=request.data, context=serializer_context
        )
        serializer.is_valid(raise_exception=True)
        proposal.do_action(
            serializer.validated_data['action'],
            self.request.user,
            serializer.validated_data['to_status'],
        )
        return Response({})

    def perform_create(self, serializer, user=None, posting=None):
        if not user:
            user = self.request.user
        proposals = serializer.save(created_by=user)
        proposal_list = proposals if type(proposals) is list else [proposals]

        for proposal in proposal_list:
            proposal.create_default_interviews()
            proposal.create_default_questions(posting)
            if posting:
                proposal.status = (
                    proposal.job.organization.proposal_statuses.filter(
                        status__stage=m.ProposalStatusStage.ASSOCIATED.key,
                        status__group=m.ProposalStatusGroup.APPLIED_BY_CANDIDATE.key,
                    )
                    .first()
                    .status
                )
            else:
                proposal.status = m.ProposalStatus.longlist.filter(
                    stage=m.ProposalStatusStage.ASSOCIATED.key
                ).first()

            proposal.save()

            m.ProposalStatusHistory.objects.create(
                proposal=proposal,
                status=proposal.status,
                changed_at=proposal.created_at,
                changed_by=user,
            )

            proposal.update_activity(user, updated='stage')
            if posting:
                notify_client_candidate_public_application(proposal)
                # allow delay for possible file uploads
                email_public_candidate_application_confirmation.apply_async(
                    (proposal.id,), countdown=60
                )
            else:
                notify_candidate_proposed_for_job(user, proposal)

    def perform_update(self, serializer):
        user = self.request.user
        old_proposal_status = serializer.instance.status
        old = self.get_serializer(serializer.instance).data
        proposal = serializer.save()
        new = self.get_serializer(serializer.instance).data

        proposal_is_reactivated = old.get('is_rejected', False) and not new.get(
            'is_rejected', True
        )
        if proposal_is_reactivated:
            proposal.decline_reasons.clear()
            proposal.reason_declined_description = ''
            proposal.reasons_not_interested.clear()
            proposal.reason_not_interested_description = ''
            proposal.save()

        diff = compare_model_dicts(old, new, ['status'])
        if 'status' in diff:
            m.ProposalStatusHistory.objects.create(
                proposal=proposal, status=proposal.status, changed_by=user,
            )

            proposal.update_activity(user, updated='status')

            current_interview = proposal.current_interview

            if (
                current_interview is None
                and old_proposal_status.stage != m.ProposalStatusStage.INTERVIEWING.key
            ):
                if proposal.interviews.count() < 1:
                    proposal.job.create_default_interview_templates()
                    proposal.create_default_interviews()

            if (
                proposal.status.stage == m.ProposalStatusStage.HIRED.key
                and proposal.job.status != m.JobStatus.FILLED.key
            ):
                is_filled = proposal.job.set_filled_if_no_openings()
                if is_filled:
                    notify_job_is_filled(user, proposal.job)

            notify_client_changed_proposal_status(user, proposal, diff)


class ProposalQuestionViewSet(viewsets.ModelViewSet):
    queryset = m.ProposalQuestion.objects.all()
    serializer_class = s.ProposalQuestionSerializer
    permission_classes = (ProposalQuestionAccessPolicy,)
    filterset_class = f.ProposalQuestionFilterSet

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        proposals = user.profile.apply_proposals_filter(m.Proposal.objects.all())
        return qs.filter(Q(proposal__in=proposals))


class ProposalCommentViewSet(
    RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Viewset for the ProposalComment model."""

    queryset = m.ProposalComment.objects.order_by('-created_at').all()
    serializer_class = s.ProposalCommentSerializer
    permission_classes = (BaseAccessPolicy,)
    filterset_class = f.ProposalCommentFilterSet

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        """Filter queryset based on User role."""
        user = self.request.user

        proposals = user.profile.apply_proposals_filter(m.Proposal.objects.all())

        return self.queryset.filter(
            Q(proposal__in=proposals)
            & (Q(author__in=user.profile.org.members) | Q(public=True))
        )

    def get_serializer_class(self):
        """Return different serializer if the action is create."""
        if self.action in CREATE_ACTIONS:
            return s.CreateProposalCommentSerializer

        return s.ProposalCommentSerializer


class ProposalInterviewUpdateMixin:
    def perform_update(self, serializer):
        """
        After update, do notification checks
        """
        old_status = serializer.instance.get_status()
        interview = serializer.save()
        user = self.request.user if self.request.user.is_authenticated else None

        schedule_statuses = m.ProposalInterviewSchedule.Status
        scheduling_types = m.ProposalInterviewSchedule.SchedulingType

        new_status = interview.get_status()
        if (
            old_status != new_status
            and interview.scheduling_type != scheduling_types.PAST_SCHEDULING
        ):
            if new_status == schedule_statuses.PENDING_CONFIRMATION:
                notify_interview_schedule_sent(user, interview)

            elif (
                new_status == schedule_statuses.SCHEDULED
                and interview.start_at is not None
                and interview.end_at is not None
            ):
                notify_proposal_interview_confirmed(None, interview)

            elif new_status == schedule_statuses.REJECTED:
                notify_proposal_interview_rejected(None, interview)

            elif new_status == schedule_statuses.CANCELED:
                notify_proposal_interview_canceled(user, interview)


class ProposalInterviewViewSet(
    ProposalInterviewUpdateMixin, viewsets.ModelViewSet, mixins.RetrieveModelMixin
):
    queryset = m.ProposalInterview.objects.all()
    permission_classes = (ProposalInterviewsAccessPolicy,)
    filterset_fields = ('proposal',)

    def get_serializer_class(self):
        if self.action in CREATE_UPDATE_ACTIONS:
            return s.CreateUpdateProposalInterviewSerializer
        return s.ProposalInterviewSerializer

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        return self.queryset.filter(
            proposal__in=self.request.user.profile.apply_proposals_filter(
                m.Proposal.objects.all()
            )
        )

    def format_serializer_data(self, request, data, many=False):
        has_assessment_access = self.permission_classes[0]().has_action_permission(
            request, self, 'assessment'
        )
        if has_assessment_access:
            return data
        if many:
            for entry in data:
                if 'assessment' in entry:
                    entry['assessment'] = None
        else:
            if 'assessment' in data:
                data['assessment'] = None
        return data

    def perform_destroy(self, instance):
        proposal = instance.proposal
        instance.delete()
        proposal.get_or_set_current_interview_maybe()

    @swagger_auto_schema(
        method='post',
        operation_id='proposal_interview_assessment_create',
        responses={201: 'CREATED'},
        request_body=s.ProposalInterviewAssessmentSerializer,
    )
    @swagger_auto_schema(
        method='get',
        operation_id='proposal_interview_assessment_read',
        responses={200: s.ProposalInterviewAssessmentSerializer},
    )
    @action(methods=['post', 'get'], detail=True)
    def assessment(self, request, *args, **kwargs):
        interview = self.get_object()
        if request.method == 'POST':
            is_edit = hasattr(interview, 'assessment')
            serializer = s.ProposalInterviewAssessmentSerializer(
                data=request.data, context={'request': request, 'interview': interview}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            if not is_edit:
                notify_interview_assessment_added(request.user, interview)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )
        else:
            try:
                serializer = s.ProposalInterviewAssessmentSerializer(
                    instance=interview.assessment
                )
                return Response(serializer.data)
            except m.ProposalInterviewAssessment.DoesNotExist:
                return Response({})


class ProposalInterviewPublicViewSet(
    ProposalInterviewUpdateMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = m.ProposalInterview.objects.all()
    serializer_class = s.ProposalInterviewPublicSerializer
    lookup_field = 'public_uuid'
