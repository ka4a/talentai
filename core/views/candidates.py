from django.contrib.contenttypes.models import ContentType
from django.db.models import (
    Max,
    Q,
    Prefetch,
    F,
)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as drf_filters
from drf_multiple_model.mixins import FlatMultipleModelMixin
from drf_yasg.openapi import Parameter
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from reversion.models import Version

from core import filters as f
from core import models as m
from core import serializers as s
from core.annotations import annotate_candidate_has_jobs_proposed_to
from core.constants import (
    CREATE_ACTIONS,
    UPDATE_ACTIONS,
    CREATE_UPDATE_ACTIONS,
    CANDIDATE_FILE_TYPES,
)


from core.mixins import ValidateModelMixin
from core.notifications import notify_mentioned_users_in_comment
from core.pagination import MultipleModelLimitPagination
from core.permissions import (
    BaseAccessPolicy,
    CandidateCommentsAccessPolicy,
    CandidateFilesAccessPolicy,
    CandidatesAccessPolicy,
)
from core.tasks import convert_resume
from core.utils import (
    fix_for_yasg,
    require_user_profile,
    LinkedinProfile,
    poly_relation_filter,
)
from core.views.views import FileViewSet
from core.check_candidate_duplication import check_candidate_duplication
from talentai import ordering_filters


class CandidateLogViewSet(viewsets.GenericViewSet):
    permission_classes = (BaseAccessPolicy,)
    queryset = Version.objects.all()
    serializer_class = s.CandidateVersionSerializer
    filterset_class = f.CandidateLogFilterSet
    diff_exclude_fields = {
        'org_id',
        'resume_thumbnail',
        'resume_ja_thumbnail',
        'cv_ja_thumbnail',
        'zoho_data',
        'li_data',
        'original',
        'updated_by',
        'created_by',
        'created_at',
    }

    @fix_for_yasg
    def get_queryset(self):
        return self.queryset.filter(
            content_type=ContentType.objects.get_for_model(m.Candidate)
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        serializer = self.get_serializer(page, many=True)
        serializer_data = serializer.data

        if len(serializer_data) < 2:
            serializer_data = []
        else:
            for i in range(len(serializer_data) - 1):
                diff = self._diff(
                    serializer_data[i + 1]['data'], serializer_data[i]['data'],
                )
                self._normalize_diff(diff)
                serializer_data[i]['changes'] = diff
        return self.get_paginated_response(serializer_data)

    def _normalize_diff(self, diff):
        for old_new_key in ['old', 'new']:
            if 'languages' in diff:
                diff['languages'][old_new_key] = ', '.join(
                    [
                        str(m.Language.objects.get(pk=pk))
                        for pk in diff['languages'][old_new_key]
                    ]
                )
            user_fields = (
                'owner',
                'name_collect',
                'mobile_collect',
                'activator',
                'lead_consultant',
                'support_consultant',
                'referred_by',
            )
            for field in user_fields:
                if field in diff:
                    value = diff[field][old_new_key]
                    try:
                        diff[field][old_new_key] = (
                            m.User.objects.get(pk=value).full_name if value else value
                        )
                    except m.User.DoesNotExist:
                        diff[field][old_new_key] = _('Deleted User')
            if 'skill_domain' in diff:
                value = diff['skill_domain'][old_new_key]
                try:
                    diff['skill_domain'][old_new_key] = (
                        str(m.SkillDomain.objects.get(pk=value)) if value else value
                    )
                except m.SkillDomain.DoesNotExist:
                    diff['skill_domain'][old_new_key] = _('Deleted Skill')
            if 'industry' in diff:
                value = diff['industry'][old_new_key]
                try:
                    diff['industry'][old_new_key] = (
                        getattr(m.Industry, value.upper()).value if value else value
                    )
                except AttributeError:
                    diff['industry'][old_new_key] = value
            for resume_key in ['resume', 'resume_ja', 'cv_ja']:
                if resume_key in diff:
                    value = diff[resume_key][old_new_key]
                    diff[resume_key][old_new_key] = (
                        value.split('/')[-1] if value else value
                    )
            if 'files' in diff:
                diff['files'][old_new_key] = ', '.join(
                    [value.split('/')[-1] for value in diff['files'][old_new_key]]
                )
            for field in {'education_details', 'experience_details'}:
                if field in diff:
                    diff[field][old_new_key] = ', '.join(diff[field][old_new_key])

    def _diff(self, old, new):
        BLANK_VALUES = (None, '')
        old = old.copy()
        new = new.copy()
        results = {}

        # composite fields
        for version_data in [old, new]:
            if version_data.get('source_details'):
                version_data['source'] += f" - {version_data['source_details']}"

            employment_type = []
            if version_data.get('fulltime'):
                employment_type.append('full-time')
            if version_data.get('parttime'):
                employment_type.append('part-time')
            version_data['desired_employment_type'] = ', '.join(employment_type)

            location = []
            if version_data.get('local'):
                location.append('local')
            if version_data.get('remote'):
                location.append('remote')
            version_data['desired_location'] = ', '.join(location)

            for_del = ['source_details', 'fulltime', 'parttime', 'local', 'remote']
            for key in for_del:
                version_data.pop(key, None)

        for field, value in old.items():
            if field in self.diff_exclude_fields:
                continue
            if field not in new:
                if value not in BLANK_VALUES:
                    results[field] = {'old': value, 'new': None}
            elif value != new[field]:
                if field in {'education_details', 'experience_details', 'files'}:
                    results[field] = {
                        'old': list(set(value) - set(new[field])),
                        'new': list(set(new[field]) - set(value)),
                    }
                elif value not in BLANK_VALUES or new[field] not in BLANK_VALUES:
                    results[field] = {'old': value, 'new': new[field]}

        for field, value in new.items():
            if field in self.diff_exclude_fields:
                continue
            if field not in old:
                if value not in BLANK_VALUES:
                    results[field] = {'old': None, 'new': value}
        return results


class CandidateCommentViewSet(
    FlatMultipleModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Viewset for the CandidateComment and (for list) ProposalComment model.
    FlatMultipleModelMixin is used to query and display both models
    in a flat way.
    """

    queryset = m.CandidateComment.objects.order_by('-created_at').all()
    serializer_class = s.CandidateCommentSerializer
    permission_classes = (CandidateCommentsAccessPolicy,)
    filterset_class = f.CandidateCommentFilterSet
    pagination_class = MultipleModelLimitPagination
    sorting_fields = ['-created_at']

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        """Filter queryset based on User role."""
        user = self.request.user

        return self.queryset.filter(
            (Q(author__in=user.profile.org.members) | Q(public=True))
        )

    def filter_queryset(self, queryset):
        # filtering is done in get_querylist as custom filtersets
        # aren't supported by drf_multiple_model
        return queryset

    def get_querylist(self):
        return [
            {
                'queryset': self.get_queryset().filter(
                    candidate=self.request.query_params['candidate']
                ),
                'serializer_class': s.CandidateCommentSerializer,
            },
            {
                'queryset': m.ProposalComment.objects.filter(
                    proposal__candidate=self.request.query_params['candidate']
                ),
                'serializer_class': s.VerboseProposalCommentSerializer,
            },
        ]

    def format_results(self, results, request):
        """
        Prepares sorting parameters, and sorts results, if(as) necessary
        """
        self.prepare_sorting_fields()
        if self._sorting_fields:
            results = self.sort_results(results)

        try:
            results = results[: int(request.query_params.get('limit'))]
        except TypeError:
            pass

        if request.accepted_renderer.format == 'html':
            # Makes the the results available to the template context by transforming to a dict
            results = {'data': results}

        return results

    def get_serializer_class(self):
        """Return different serializer if the action is create."""
        if self.action in CREATE_ACTIONS:
            return s.CreateCandidateCommentSerializer

        return s.CandidateCommentSerializer

    def perform_create(self, serializer):
        candidate_comment = serializer.save()
        notify_mentioned_users_in_comment(self.request.user, candidate_comment)

    def perform_destroy(self, instance):
        notify_mentioned_users_in_comment(self.request.user, instance, True)
        m.Notification.objects.filter(target_object_id=instance.id).delete()
        instance.delete()


class CandidateMiscFilesViewSet(FileViewSet, mixins.UpdateModelMixin):
    queryset = m.CandidateFile.objects.all()
    permission_classes = (CandidateFilesAccessPolicy,)
    serializer_class = s.CandidateFileSerializer

    def get_serializer_class(self):
        if self.action in UPDATE_ACTIONS:
            return s.UpdateCandidateFileSerializer
        elif self.action == 'public_upload':
            return s.PublicCandidateFileSerializer
        return self.serializer_class

    @fix_for_yasg
    def get_queryset(self):
        profile = self.request.user.profile
        """Return Candidate file based on User type."""

        where = poly_relation_filter('org_id', 'org_content_type', profile.org)

        if self.action in ['retrieve', 'preview']:
            where |= Q(
                is_shared=True,
                candidate__proposals__isnull=False,
                candidate__proposals__in=profile.apply_proposals_filter(
                    m.Proposal.objects.all()
                ),
            )

        return self.queryset.filter(where).distinct()

    @action(methods=['GET'], detail=True)
    def preview(self, request, *args, **kwargs):
        return self.generic_retrieve_file_view(kwargs['pk'], 'preview')

    @action(methods=['post'], detail=False)
    def public_upload(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


@method_decorator(
    name='list',
    decorator=swagger_auto_schema(query_serializer=s.CandidateQuerySerializer()),
)
@method_decorator(
    decorator=swagger_auto_schema(
        query_serializer=s.CandidateRetrieveQuerySerializer()
    ),
    name='retrieve',
)
class CandidateViewSet(viewsets.ModelViewSet):
    """Viewset for the Candidate model."""

    queryset = m.Candidate.archived_objects.prefetch_related(
        Prefetch(
            'education_details',
            queryset=m.EducationDetail.objects.order_by('-date_start'),
        ),
        Prefetch(
            'experience_details',
            queryset=m.ExperienceDetail.objects.order_by('-date_start'),
        ),
    )
    serializer_class = s.CandidateSerializer
    permission_classes = (CandidatesAccessPolicy,)
    filter_backends = [
        drf_filters.DjangoFilterBackend,
        f.CandidateSearchFilter,
        ordering_filters.CamelCaseOrderingFilter,
    ]
    filterset_class = f.CandidateFilterSet
    search_fields = (
        'id',
        'first_name',
        'middle_name',
        'last_name',
        'first_name_kanji',
        'last_name_kanji',
        'first_name_katakana',
        'last_name_katakana',
        'current_country',
        'email',
        'secondary_email',
        'current_position',
        'current_company',
        'certifications__certification',
        'certifications__certification_other',
        'experience_details__occupation',
        'experience_details__company',
        'experience_details__summary',
        'education_details__institute',
        'education_details__department',
    )
    ordering_fields_mapping = {'name': ('first_name', 'last_name')}

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        """Return Candidates based on User type."""
        profile = self.request.user.profile
        queryset = profile.apply_own_candidates_filter(self.queryset)
        if self.action in ['retrieve', 'archive_candidate']:
            queryset = annotate_candidate_has_jobs_proposed_to(queryset)

        include_archived = (
            self.action in ['retrieve', 'destroy', 'restore_candidate']
            or self.request.query_params.get('include_archived') == 'true'
        )
        if not include_archived:
            queryset = queryset.filter(archived=False)

        approved_filter = Q(proposals__placement__fee__status=m.FeeStatus.APPROVED.key)
        queryset = queryset.annotate(
            placement_approved_at=Max(
                F('proposals__placement__fee__approved_at'), filter=approved_filter
            )
        )

        return queryset

    def get_serializer_class(self):
        if self.action in CREATE_UPDATE_ACTIONS:
            return s.CreateUpdateCandidateSerializer
        profile = self.request.user.profile

        if self.action == 'retrieve':
            if profile.has_full_candidate_field_access:
                return s.RetrieveCandidateSerializer
            return s.BasicRetrieveCandidateSerializer
        if profile.has_full_candidate_field_access:
            return s.CandidateSerializer
        return s.BasicCandidateSerializer

    def get_serializer_context(self):
        """Validate and pass other request data to serializer via context."""
        context = super().get_serializer_context()

        if self.action == 'list':
            query_serializer = s.CandidateQuerySerializer(
                data=self.request.GET, context=context
            )
            query_serializer.is_valid(raise_exception=True)
            return {**context, **query_serializer.validated_data}

        return super().get_serializer_context()

    def perform_create(self, serializer):
        """Set Candidate agency field value to the User Agency."""
        serializer.save(organization=self.request.user.profile.org)

    def get_serialized_data(self, serializer_class):
        serializer = serializer_class(
            data=self.request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        return serializer.data

    def get_duplication_check_response(self, data):
        check_results = check_candidate_duplication(data, self.request.user.profile)

        return Response(
            {
                'submitted_by_others': check_results['submitted_by_others'],
                'last_submitted': check_results['last_submitted'],
                'duplicates': s.DuplicatedCandidateSerializer(
                    check_results['queryset'].order_by('-is_absolute'), many=True
                ).data,
                'to_restore': s.DuplicatedCandidateSerializer(
                    check_results['to_restore'], many=True
                ).data,
            }
        )

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(
        operation_id='candidate_check_duplication',
        request_body=s.PossibleDuplicateCandidateSerializer,
    )
    def check_duplication(self, request, **kwargs):
        data = self.get_serialized_data(s.PossibleDuplicateCandidateSerializer)

        return self.get_duplication_check_response(data)

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(
        operation_id='candidate_linkedin_data_check_duplication',
        request_body=s.PossibleDuplicateLinkedInCandidateSerializer,
    )
    def linkedin_data_check_duplication(self, request, **kwargs):
        data = self.get_serialized_data(s.PossibleDuplicateLinkedInCandidateSerializer)

        candidate_data = LinkedinProfile(data).candidate_data

        return self.get_duplication_check_response(candidate_data)

    @action(methods=['patch'], detail=False)
    @swagger_auto_schema(request_body=s.CheckIfLinkedinSubmittedToJobSerializer,)
    def linkedin_url_check_proposed(self, request, **kwargs):
        data = self.get_serialized_data(s.CheckIfLinkedinSubmittedToJobSerializer)

        qs = m.Candidate.objects.filter(linkedin_url=data['linkedin_url'])

        is_exist = qs.exists()
        is_submitted = is_exist and qs.filter(proposals__job_id=data['job']).exists()

        return Response(
            status=status.HTTP_200_OK,
            data={'is_exist': is_exist, 'is_submitted': is_submitted},
        )

    @action(methods=['patch'], detail=True)
    @swagger_auto_schema(operation_id='candidate_archive',)
    def archive_candidate(self, request, pk, **kwargs):
        """Archive candidates instead of deleting them"""
        candidate = self.get_object()

        if candidate.proposed_to_job:
            return Response(
                {"proposed_to_job": candidate.proposed_to_job},
                status=status.HTTP_409_CONFLICT,
            )

        candidate.archived = True
        candidate.save()

        return Response({}, status=status.HTTP_204_NO_CONTENT)

    @action(methods=['patch'], detail=True)
    @swagger_auto_schema(operation_id='candidate_restore')
    def restore_candidate(self, request, pk, **kwargs):
        candidate = self.get_object()

        if candidate:
            candidate.archived = False
            candidate.save()

            serializer = self.serializer_class(candidate, context={'request': request})

            return Response(serializer.data)

        return Response({}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, *args, **kwargs):
        candidate = self.get_object()
        if not getattr(candidate, 'archived'):
            return Response(
                {'detail': _('Candidate is not archived.')},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class CandidateValidateViewSet(ValidateModelMixin, viewsets.GenericViewSet):
    serializer_class = s.ValidateCreateUpdateCandidateSerializer
    queryset = m.Candidate.objects.all()
    get_queryset = CandidateViewSet.get_queryset
    permission_classes = CandidateViewSet.permission_classes


class CandidateLinkedinDataViewSet(viewsets.GenericViewSet):
    """Viewset for the Candidate model."""

    queryset = m.CandidateLinkedinData.objects.all()
    serializer_class = Serializer
    permission_classes = (BaseAccessPolicy,)

    @fix_for_yasg
    def get_queryset(self):
        """Return Candidates based on User type."""
        return self.queryset.filter(
            candidate__in=self.request.user.profile.apply_own_candidates_filter(
                m.Candidate.objects
            )
        )

    @action(methods=['get'], detail=True)
    @swagger_auto_schema(
        operation_id='candidates_linkedin_data_get_candidate_data',
        responses={200: 'OK'},
    )
    def get_candidate_data(self, request, **kwargs):
        """Get Candidate fields data."""
        linkedin_data = self.get_object()

        linkedin_profile = LinkedinProfile(linkedin_data.data)

        return Response(
            {
                'candidate': s.CandidateSerializer(
                    instance=linkedin_data.candidate, context={'request': self.request}
                ).data,
                'patch_data': linkedin_profile.candidate_data,
            }
        )


class CandidateFileViewSet(viewsets.GenericViewSet):
    """Viewset for Candidate files."""

    queryset = m.Candidate.objects.none()
    serializer_class = Serializer
    permission_classes = (CandidateFilesAccessPolicy,)
    parser_classes = (MultiPartParser,)

    @action(methods=['get'], detail=True, parser_classes=(MultiPartParser,))
    @swagger_auto_schema(operation_id='candidates_get_file')
    def get(self, request, pk, ftype):
        """Download Candidate file."""
        if ftype not in CANDIDATE_FILE_TYPES:
            return Response({'detail': _('Incorrect file type.')}, 400)

        available_candidates = request.user.profile.apply_candidates_filter(
            m.Candidate.objects
        )
        candidate = get_object_or_404(available_candidates, pk=pk)

        if getattr(candidate, ftype) and getattr(candidate, ftype).file:
            filename = getattr(candidate, ftype).name.split('/')[-1]
            response = HttpResponse(
                getattr(candidate, ftype).file,
                content_type='application/force-download',
            )
            response['Content-Disposition'] = 'inline; filename="{}"'.format(filename)
            return response

        return Response({'detail': _('File not found.')}, 404)

    @action(methods=['post'], detail=True, parser_classes=(MultiPartParser,))
    @swagger_auto_schema(
        operation_id='candidates_upload_file',
        responses={200: 'OK'},
        consumes=['multipart/form-data'],
        manual_parameters=[
            Parameter(name='file', in_='formData', required=False, type='file')
        ],
    )
    def upload(self, request, pk, ftype):
        """Upload Candidate file."""
        if ftype not in CANDIDATE_FILE_TYPES:
            return Response({'detail': _('Incorrect file type.')}, 400)

        if request.data.get('file', None) is None:
            return Response({'detail': _('No file in request data.')}, 400)

        own_candidates = request.user.profile.apply_own_candidates_filter(
            m.Candidate.objects
        )

        candidate = get_object_or_404(own_candidates.select_for_update(), pk=pk)

        file = request.data.get('file', getattr(candidate, ftype))
        setattr(candidate, ftype, file)

        candidate.save()

        convert_resume.delay(candidate.pk)

        return Response({'detail': _('Candidate file uploaded.')})

    @action(
        methods=['post'], detail=True, parser_classes=(MultiPartParser,),
    )
    @swagger_auto_schema(
        operation_id='candidates_public_upload_file',
        responses={200: 'OK'},
        consumes=['multipart/form-data'],
        manual_parameters=[
            Parameter(name='file', in_='formData', required=False, type='file')
        ],
    )
    def public_upload(self, request, pk, ftype):
        """Upload Candidate file."""
        if ftype not in CANDIDATE_FILE_TYPES:
            return Response({'detail': _('Incorrect file type.')}, 400)

        if request.data.get('file', None) is None:
            return Response({'detail': _('No file in request data.')}, 400)

        # TODO make sure this is a public candidate
        candidate = get_object_or_404(m.Candidate.objects.select_for_update(), pk=pk)

        file = request.data.get('file', getattr(candidate, ftype))
        setattr(candidate, ftype, file)

        candidate.save()

        convert_resume.delay(candidate.pk)

        return Response({'detail': _('Candidate file uploaded.')})

    @action(methods=['delete'], detail=True, parser_classes=(MultiPartParser,))
    @swagger_auto_schema(
        operation_id='candidates_delete_file', responses={200: 'OK'},
    )
    def delete(self, request, pk, ftype):
        """Delete Candidate file."""
        if ftype not in CANDIDATE_FILE_TYPES:
            return Response({'detail': _('Incorrect file type.')}, 400)

        own_candidates = request.user.profile.apply_own_candidates_filter(
            m.Candidate.objects
        )
        candidate = get_object_or_404(own_candidates, pk=pk)
        try:
            getattr(candidate, ftype).file
        except ValueError:
            return Response({'detail': _('File not found.')}, 404)

        getattr(candidate, ftype).delete()
        if ftype == 'resume':
            candidate.resume_thumbnail.delete()
        elif ftype == 'resume_ja':
            candidate.resume_ja_thumbnail.delete()
        elif ftype == 'cv_ja':
            candidate.cv_ja_thumbnail.delete()

        candidate.save()

        return Response({'detail': _('Candidate file deleted.')})


class CandidateNoteViewSet(
    RetrieveModelMixin, UpdateModelMixin, viewsets.GenericViewSet
):
    """Viewset for the Candidate note."""

    queryset = m.Candidate.objects.all()
    serializer_class = s.CandidateNoteUpdateSerializer
    permission_classes = (BaseAccessPolicy,)

    @fix_for_yasg
    def get_queryset(self):
        return self.request.user.profile.apply_candidates_filter(self.queryset)


class CandidateClientBriefViewSet(
    RetrieveModelMixin, UpdateModelMixin, viewsets.GenericViewSet
):
    """Viewset for the Candidate client_brief."""

    queryset = m.Candidate.objects.all()
    serializer_class = s.CandidateClientBriefUpdateSerializer
    permission_classes = (BaseAccessPolicy,)

    @fix_for_yasg
    def get_queryset(self):
        return self.request.user.profile.apply_candidates_filter(self.queryset)
