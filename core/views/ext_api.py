from django.conf import settings
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import serializers
from django.core.exceptions import ValidationError

from core import models as m
from core.serializers import (
    CheckLinkedinCandidateExists,
    ExtJobSerializer,
    ExtJobQuerySerializer,
    AgencyUserExtJobSerializer,
    AddLinkedInCandidateSerializer,
)
from core.utils import LinkedinProfile, has_profile, fix_for_yasg, require_user_profile


class ExtApiJobListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = m.Job.objects.all()
    search_fields = ('title',)

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        profile = self.request.user.profile

        return (
            profile.apply_jobs_filter(m.Job.objects.all())
            .filter(status=m.JobStatus.OPEN.key)
            .order_by('-created_at')
        )

    def get_serializer_class(self):
        user = self.request.user

        if hasattr(user, 'profile') and hasattr(user.profile, 'agency'):
            return AgencyUserExtJobSerializer

        return ExtJobSerializer


def check_permissions(user, permissions):
    if not user.is_authenticated:
        return Response(
            {'detail': 'not authenticated'}, status=status.HTTP_403_FORBIDDEN
        )

    has_permissions = user.has_perms(permissions) and has_profile(user)

    if not has_permissions:
        return Response(
            {'detail': 'You have no permission'}, status=status.HTTP_403_FORBIDDEN,
        )

    return None


class ExtApiViewSet(viewsets.ViewSet):
    """Endpoints for the browser extension."""

    @action(methods=['get'], detail=False)
    @swagger_auto_schema(
        query_serializer=ExtJobQuerySerializer,
        responses={200: AgencyUserExtJobSerializer(many=True)},
    )
    def job_list(self, request):  # TODO: can be removed after 0.8.0
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return Response([])

        queryset = (
            profile.apply_jobs_filter(m.Job.objects.all())
            .filter(status=m.JobStatus.OPEN.key)
            .order_by('-created_at')
        )

        title = request.query_params.get('title', None)
        if title:
            queryset = queryset.filter(title__icontains=title)

        serializer_class = (
            AgencyUserExtJobSerializer
            if hasattr(profile, 'agency')
            else ExtJobSerializer
        )
        serializer = serializer_class(queryset[:20], many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(
        operation_id='check_linkedin_candidate_exists',
        request_body=CheckLinkedinCandidateExists,
    )
    def check_linkedin_candidate_exists(self, request, format=None):
        error_response = check_permissions(request.user, ['core.view_candidate'])
        if error_response:
            return error_response

        serializer = CheckLinkedinCandidateExists(data=request.data)
        serializer.is_valid(raise_exception=True)
        candidate = (
            request.user.profile.apply_own_candidates_filter(m.Candidate.objects)
            .filter(linkedin_slug=serializer.parse_slug())
            .first()
        )

        return Response({'candidate_id': candidate.id if candidate else None})

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(
        operation_id='add_linkedin_candidate',
        request_body=AddLinkedInCandidateSerializer,
    )
    def add_linkedin_candidate(self, request, format=None):
        user = request.user
        error_response = check_permissions(
            user, ['core.add_candidate', 'core.change_candidate']
        )
        if error_response:
            return error_response

        serializer = AddLinkedInCandidateSerializer(
            data=request.data, context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        raw_linkedin_profile = LinkedinProfile(request.data)
        linkedin_profile = LinkedinProfile(serializer.validated_data)

        if linkedin_profile.slug is None:
            return Response(
                {'detail': 'invalid URL'}, status=status.HTTP_400_BAD_REQUEST
            )

        candidate = user.profile.apply_own_candidates_filter(
            m.Candidate.objects.filter(linkedin_slug=linkedin_profile.slug)
        ).first()

        if not candidate:
            try:
                candidate = m.Candidate.objects.create(
                    organization=user.profile.org,
                    employment_status='fulltime',
                    owner=user,
                    created_by=user,
                    **linkedin_profile.candidate_data,
                )

                if linkedin_profile.photo and linkedin_profile.photo.filename:
                    candidate.photo.save(
                        linkedin_profile.photo.filename, linkedin_profile.photo.file
                    )
                    candidate.save()
            except ValidationError as e:
                raise serializers.ValidationError(e.message_dict)

        candidate.updated_by = user
        candidate.save()

        linkedin_data = m.CandidateLinkedinData.objects.create(
            candidate=candidate, data=raw_linkedin_profile.data, created_by=user
        )

        require_data_merge = any(
            getattr(candidate, key) != value
            for key, value in linkedin_profile.candidate_data.items()
        )

        candidate.experience_details.all().delete()
        for item in linkedin_profile.experience_details:
            m.ExperienceDetail.objects.create(candidate=candidate, **item)

        candidate.education_details.all().delete()
        for item in linkedin_profile.educational_details:
            m.EducationDetail.objects.create(candidate=candidate, **item)

        if linkedin_profile.proposal and candidate:
            proposals = m.Proposal.objects.filter(
                candidate=candidate, job_id=linkedin_profile.proposal['job'],
            )

            if len(proposals) < 1:
                proposal = m.Proposal.objects.create(
                    candidate=candidate,
                    created_by=user,
                    job_id=linkedin_profile.proposal['job'],
                    stage=linkedin_profile.proposal['stage'],
                )
            else:
                error = _(
                    'This candidate has already been submitted'
                    ' for this job by your organization.'
                )
                proposal = proposals.first()
                if proposal.created_by == user:
                    error = _('You have already submitted this candidate to this job')
                return Response(
                    status=status.HTTP_400_BAD_REQUEST, data={'detail': error}
                )

        else:
            proposal = None

        return Response(
            {
                'result': 'OK',
                'candidateId': candidate.id,
                'proposalId': proposal.id if proposal else None,
                'dataId': linkedin_data.id,
                'merge': require_data_merge,
            }
        )
