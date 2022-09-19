from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth import update_session_auth_hash
from django.db.models import (
    Q,
    F,
    CharField,
    Exists,
    OuterRef,
    Count,
)
from django.db.models.functions import Concat
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from drf_yasg.openapi import Parameter
from drf_yasg.utils import swagger_auto_schema, no_body
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from core import filters as f
from core import models as m
from core import serializers as s
from core.annotations import annotate_proposal_deal_pipeline_metrics
from core.constants import (
    CREATE_ACTIONS,
    CREATE_DELETE_ACTIONS,
    UPDATE_ACTIONS,
    VALIDATE_ACTIONS,
)
from core.email import send_reset_password_link
from core.mixins import ValidateModelMixin
from core.notifications import (
    notify_client_created_contract,
    notify_client_admin_assigned_manager,
)
from core.permissions import (
    AgencyBaseAccessPolicy,
    BaseAccessPolicy,
    FeePermission,
    FeeSplitAllocationPermission,
    IsAgencyUser,
    IsClientUser,
    ManagersAccessPolicy,
    NoteActivityAccessPolicy,
    RoleClientPermissions,
    add_permissions,
    IsOrganizationUser,
    IsOwnOrganization,
    get_permission_actions_available_to,
    get_permission_profiles_have_access,
)
from core.user_activation import get_agency_admin_activation_data
from core.utils import (
    compare_model_dicts,
    convert_request_meta_to_dict,
    fix_for_yasg,
    get_bool_annotation,
    get_country_list,
    org_filter,
    require_user_profile,
    set_drf_sensitive_post_parameters,
)
from core.utils.view import create_file_download_response, upload_photo_view
from core.views.user_activate_account import send_activation_link
from core.zoho import save_zoho_candidate, ZohoImportError, get_zoho_candidate


User = get_user_model()


class LocaleViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False)
    @swagger_auto_schema(operation_id='locale_data_read')
    def get_locale(self, request, format=None):
        locale = {}

        if request.user.is_authenticated:
            profile = request.user.profile

            locale['countries'] = get_country_list()
            locale['consulting_fee_types'] = m.ConsultingFeeType.get_dropdown_options()
            locale[
                'candidate_internal_statuses'
            ] = m.CandidateInternalStatus.get_dropdown_options()
            locale['functions'] = [
                {'value': function.id, 'label': function.title}
                for function in m.Function.objects.all()
            ]
            locale['job_categories'] = locale['functions']
            locale['bill_descriptions'] = {
                contract.key: (
                    bill.dropdown_option
                    for bill in m.BillDescription.get_available_for_contract(
                        contract.key
                    )
                )
                for contract in m.JobContractTypes
            }

            locale['industries'] = m.Industry.get_dropdown_options()
            locale['skill_domains'] = m.SkillDomain.get_dropdown_options()
            locale['work_experiences'] = m.JobWorkExperience.get_dropdown_options()

            if profile:
                qs_org_proposal_statuses = m.OrganizationProposalStatus.objects.filter(
                    org_filter(profile.org)
                )
                locale['proposal_longlist_statuses'] = s.ProposalStatusSerializer(
                    m.ProposalStatus.objects.filter(
                        stage__in=m.ProposalStatusStage.get_longlist_keys()
                    ),
                    many=True,
                ).data
                locale['proposal_shortlist_statuses'] = s.OrgProposalStatusSerializer(
                    qs_org_proposal_statuses.filter(
                        status__stage__in=m.ProposalStatusStage.get_shortlist_keys()
                    ),
                    many=True,
                ).data
                locale['proposal_reasons_declined'] = [
                    {
                        'value': option.id,
                        'label': option.text,
                        'has_description': option.has_description,
                    }
                    for option in m.ReasonDeclineCandidateOption.objects.all()
                ]
                locale['proposal_reasons_not_interested'] = [
                    {
                        'value': option.id,
                        'label': option.text,
                        'has_description': option.has_description,
                    }
                    for option in m.ReasonNotInterestedCandidateOption.objects.all()
                ]

                locale['candidate_source_choices'] = [
                    {'value': value, 'label': label}
                    for value, label in m.CandidateSources.choices
                ]
                locale[
                    'candidate_source_details'
                ] = m.CANDIDATE_SOURCE_DETAILS_PROPERTIES

                if hasattr(profile, 'agency'):
                    locale['client_types'] = m.ClientType.get_dropdown_options()
                    locale[
                        'job_contract_types'
                    ] = m.JobContractTypes.get_dropdown_options()
                    locale['contract_types'] = m.ContractType.get_dropdown_options()
                    locale['invoice_on'] = m.InvoiceOn.get_dropdown_options()
                    locale[
                        'proposal_deal_stages'
                    ] = m.ProposalDealStages.get_dropdown_options()
                    locale['invoice_statuses'] = m.InvoiceStatus.get_dropdown_options()

        locale['pagination_schema'] = m.FrontendSettingsSchema.PAGINATION_SCHEMA
        locale['countries'] = get_country_list()
        locale['disable_signup'] = settings.DISABLE_SIGNUP

        return Response(locale)


class DataViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False)
    @swagger_auto_schema(query_serializer=s.OrgStatusesQuerySerializer)
    def get_org_proposal_statuses(self, *args, **kwargs):
        query_serializer = s.OrgStatusesQuerySerializer(
            data=self.request.query_params, context={'request': self.request}
        )
        query_serializer.is_valid(raise_exception=True)

        org_id = query_serializer.validated_data['org_id']
        org_type = query_serializer.validated_data['org_type']

        if org_type == 'client':
            queryset = m.OrganizationProposalStatus.client_objects
        else:
            queryset = m.OrganizationProposalStatus.agency_objects
        queryset = (
            queryset.filter(org_id=org_id, org_content_type__model=org_type)
            .order_by('order', 'status__stage', 'status__group')
            .distinct('order', 'status__stage', 'status__group')
        )
        return Response(s.OrgProposalStatusSerializer(queryset, many=True,).data)


class UserViewSet(mixins.CreateModelMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = s.UserSerializer

    @action(methods=['get'], detail=False)
    @swagger_auto_schema(
        operation_id='user_read_current', responses={200: s.UserSerializer()}
    )
    def read_current(self, request, format=None):
        return Response(s.UserSerializer(request.user).data)

    @action(methods=['patch'], detail=False)
    @swagger_auto_schema(
        operation_id='user_update_settings',
        request_body=s.UserUpdateSerializer,
        responses={200: s.UserUpdateSerializer()},
    )
    def update_settings(self, request, format=None):
        set_drf_sensitive_post_parameters(request)

        serializer = s.UserUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        locale = serializer.validated_data.get('locale')
        response = Response(serializer.data)
        if locale:
            translation.activate(locale)
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, locale)

        if serializer.validated_data.get('new_password'):
            # Updating the password logs out all other sessions for the user
            # except the current one.
            update_session_auth_hash(self.request, request.user)

        return response

    @action(methods=['patch'], detail=False)
    @swagger_auto_schema(
        operation_id='user_update_legal',
        request_body=s.UpdateUserLegalSerializer,
        responses={200: s.UpdateUserLegalSerializer()},
    )
    def update_legal(self, request, format=None):
        serializer = s.UpdateUserLegalSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=['post'], detail=False, parser_classes=(MultiPartParser,))
    @swagger_auto_schema(
        operation_id='user_upload_photo',
        responses={200: 'OK'},
        consumes=['multipart/form-data'],
        manual_parameters=[
            Parameter(name='file', in_='formData', required=True, type='file')
        ],
    )
    def upload_photo(self, request, *args, **kwargs):
        return upload_photo_view(request, request.user)

    @action(methods=['get'], detail=False)
    @swagger_auto_schema(
        operation_id='user_download_photo', responses={200: 'OK'},
    )
    def download_photo(self, request, *args, **kwargs):
        return create_file_download_response(request.user.photo)

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(
        operation_id='user_delete_photo', responses={200: 'OK'},
    )
    def delete_photo(self, request, *args, **kwargs):
        request.user.photo.delete()
        request.user.save()

        return Response({'detail': _('Saved.')})

    @action(methods=['get'], detail=False)
    @swagger_auto_schema(
        operation_id='user_notifications_count',
        responses={200: s.NotificationsCountSerializer()},
    )
    def notifications_count(self, request, format=None):
        return Response(
            s.NotificationsCountSerializer(
                {'count': request.user.unread_notifications_count}
            ).data
        )


class TeamViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (BaseAccessPolicy,)
    serializer_class = s.TeamSerializer
    queryset = m.Team.objects.all()
    pagination_class = None

    @fix_for_yasg
    def get_queryset(self):
        """Get current user org's teams."""
        roles = (m.ClientAdministrator, m.AgencyAdministrator, m.AgencyManager)
        if type(self.request.user.profile) in roles:
            return self.request.user.profile.org.teams.all()

        return self.request.user.profile.teams.all()


class ManagerViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Viewset to retrieve, assign and remove Job Managers."""

    permission_classes = (ManagersAccessPolicy,)
    serializer_class = s.UserSerializer
    queryset = User.objects.all()
    search_fields = ('id', 'first_name', 'last_name', 'email')
    ordering_fields = ('name_full', 'email')

    @fix_for_yasg
    def get_queryset(self):
        """Limit queryset to Hiring Managers of User's Client."""
        return self.request.user.profile.client.members.annotate(
            name_full=Concat(F('first_name'), F('last_name'), output_field=CharField())
        )

    def extract_user_and_job(self):
        serializer = s.ManagerAssignRemoveFromJobSerializer(
            data=self.request.data, context={'request': self.request}
        )
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(pk=self.request.data['user'])
        job = m.Job.objects.get(pk=self.request.data['job'])

        return user, job

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(
        request_body=s.ManagerAssignRemoveFromJobSerializer, responses={200: ''},
    )
    def assign(self, request, format=None):
        """Assign the User as the Manager for the Job."""
        user, job = self.extract_user_and_job()

        if user in job.managers:
            return Response(
                {'detail': _('User is already assigned as a Job Manager.')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user and job:
            old = s.CreateUpdateJobSerializer(job, context={'request': request}).data
            job.assign_manager(user)
            new = s.CreateUpdateJobSerializer(job, context={'request': request}).data

            notify_client_admin_assigned_manager(
                self.request.user,
                job,
                compare_model_dicts(old, new, compare_as_set=['managers']),
            )

        job.assign_manager(user)

        return Response({'detail': _('User assigned as a Job Manager.')})

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(
        request_body=s.ManagerAssignRemoveFromJobSerializer, responses={200: ''}
    )
    def remove_from_job(self, request, format=None):
        """Dismiss the User from Managers of the Job."""
        user, job = self.extract_user_and_job()

        if user not in job.managers:
            return Response(
                {'detail': _('User is not a Manager of this Job.')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job.withdraw_manager(user)

        return Response({'detail': _('User removed from Job Managers.')})

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(
        request_body=s.ManagerInviteSerializer, responses={200: ''},
    )
    def invite(self, request, format=None):
        """Create a User, assign as Hiring Manager, send a restore link."""
        serializer = s.ManagerInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        request.user.profile.client.assign_standard_user(user)

        send_reset_password_link(
            request,
            user.email,
            'invite/invite_sent_email.html',
            'invite/invite_sent_subject.txt',
            email_context={'client': user.profile.client.name},
        )

        return Response({'detail': _('Invite link sent.')})


class LoginView(viewsets.ViewSet):
    @action(methods=['post'], detail=True)
    @swagger_auto_schema(
        operation_id='user_login',
        request_body=s.UserLoginSerializer,
        responses={200: s.UserSerializer()},  # TODO: error response?
    )
    def login(self, request, format=None):
        set_drf_sensitive_post_parameters(request)

        serializer = s.UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.user and not serializer.user.is_active:
            return Response(
                {'detail': _('Your account is deactivated.')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            request,
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )

        if user is not None:
            login(request, user)
            if not (user.is_staff or user.is_superuser):
                # normal user sessions expire after a day
                request.session.set_expiry(settings.SESSION_NON_ADMIN_COOKIE_AGE)
                request.session.save()
            response = Response(s.UserSerializer(user).data)

            translation.activate(user.locale)
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user.locale)

            return response

        return Response(
            {'detail': _('Email or password is not valid.')},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(methods=['post'], detail=True)
    @swagger_auto_schema(operation_id='user_logout')
    def logout(self, request, format=None):
        logout(request)

        return Response({'detail': _('Logged out.')})


class RegistrationCheckEmailView(viewsets.ViewSet):
    @action(methods=['post'], detail=True)
    @swagger_auto_schema(
        operation_id='registration_check_email',
        request_body=s.RegistrationCheckEmailSerializer,
    )
    def check_email(self, request, format=None):
        serializer = s.RegistrationCheckEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reg_type = serializer.validated_data['type']
        email = serializer.validated_data['email']

        agency_exists = m.Agency.get_by_email_domain(email) is not None

        if reg_type == 'client' and agency_exists:
            return Response(
                {'detail': _('Email\'s domain is used by an agency.')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {'type': reg_type, 'email': email, 'agency_exists': agency_exists}
        )


class RecruiterRegistrationView(viewsets.ViewSet):
    @action(methods=['post'], detail=True)
    @swagger_auto_schema(
        operation_id='recruiter_sign_up_register',
        request_body=s.RecruiterRegistrationSerializer,
    )
    def register(self, request, format=None):
        set_drf_sensitive_post_parameters(request)

        serializer = s.RecruiterRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        agency = m.Agency.get_by_email_domain(serializer.validated_data['email'])

        activation_data = get_agency_admin_activation_data(
            agency=agency, job=serializer.validated_data.get('via_job')
        )

        user = serializer.save(is_activated=False, **activation_data)

        send_activation_link(request, user)

        return Response(
            {
                'message': _(
                    'Your account was created. '
                    'Please check your email to activate your account.'
                )
            }
        )


class AgencyRegistrationViewSet(viewsets.ViewSet):
    """Viewset for the AgencyRegistrationRequestSerializer model."""

    queryset = m.AgencyRegistrationRequest.objects.all()

    @swagger_auto_schema(request_body=s.AgencyRegistrationRequestSerializer)
    def create(self, request):
        if settings.DISABLE_SIGNUP:
            return Response(
                {'message': _('Signup disabled')}, status=status.HTTP_403_FORBIDDEN
            )
        serializer = s.AgencyRegistrationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        r = serializer.save(
            ip=request.META['REMOTE_ADDR'],
            headers=convert_request_meta_to_dict(request),
        )

        if r.created:
            message = _('Your account was created.')
        else:
            message = _('Your account was created and is pending approval.')

        return Response({'message': message})


class ClientRegistrationViewSet(viewsets.ViewSet):
    """Viewset for the ClientRegistrationRequest model."""

    queryset = m.ClientRegistrationRequest.objects.all()

    @swagger_auto_schema(request_body=s.ClientRegistrationRequestSerializer)
    def create(self, request):
        if settings.DISABLE_SIGNUP:
            return Response(
                {'message': _('Signup disabled')}, status=status.HTTP_403_FORBIDDEN
            )
        serializer = s.ClientRegistrationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(
            ip=request.META['REMOTE_ADDR'],
            headers=convert_request_meta_to_dict(request),
        )

        return Response(
            {'message': _('Your account was created and is pending approval.')}
        )


class ClientViewSet(viewsets.ModelViewSet):
    """Viewset for the Client model."""

    queryset = m.Client.objects.all()
    serializer_class = s.ClientSerializer
    permission_classes = (IsAuthenticated, RoleClientPermissions)
    search_fields = ('id', 'name')

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return s.YasgClientSerializer

        profile = self.request.user.profile

        if self.action in ['create', 'update', 'partial_update'] and hasattr(
            profile, 'agency'
        ):
            return s.CreateUpdateAgencyClientSerializer

        return s.ClientSerializer

    @fix_for_yasg
    def get_queryset(self):
        """Filter queryset for different types of Users."""
        user = self.request.user
        profile = user.profile

        if user.is_superuser:
            return self.queryset

        if not (profile and profile.org):
            return self.queryset.none()

        return profile.org.apply_available_clients_filter(self.queryset)


class FileViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = Serializer
    parser_classes = (MultiPartParser,)

    def generic_retrieve_file_view(self, pk, file_field):
        """Download File"""
        file_record = get_object_or_404(self.get_queryset(), pk=pk)
        file = getattr(file_record, file_field)
        if file is None or file.name == '':
            return Response({'detail': _('Not found.')}, 404)

        filename = file.name.split('/')[-1]
        response = HttpResponse(file, content_type='application/force-download')
        response['Content-Disposition'] = 'inline; filename="{}"'.format(filename)

        return response

    def retrieve(self, request, *args, **kwargs):
        return self.generic_retrieve_file_view(kwargs['pk'], 'file')


class AgencyViewSet(viewsets.ModelViewSet):
    """Viewset for the Agency model."""

    queryset = m.Agency.objects.distinct()
    serializer_class = s.AgencySerializer
    permission_classes = (
        DjangoModelPermissions,
        IsAuthenticated,
        IsOwnOrganization,
        IsOrganizationUser,
    )
    search_fields = ('id', 'name')
    filterset_class = f.AgencyFilter
    ordering_fields = ('id', 'name', 'contract_ann')

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        """Filter queryset for different types of Users."""
        user = self.request.user

        if hasattr(user.profile, 'agency'):
            return self.queryset.filter(pk=user.profile.agency.pk)

        if hasattr(user.profile, 'client'):
            return self.queryset.annotate(
                contract_ann=Exists(
                    m.Contract.objects.filter(
                        status=m.ContractStatus.INITIATED.key,
                        client=user.profile.client,
                        agency=OuterRef('pk'),
                    )
                )
            )

    def get_serializer_class(self):
        if self.action == 'list':
            return s.AgencyListSerializer

        return self.serializer_class

    def get_object(self):
        if self.kwargs.get('pk') == 'current':
            self.kwargs['pk'] = self.request.user.profile.agency_id

        return super().get_object()


class ContractViewSet(viewsets.ModelViewSet):
    """Viewset for the Contract model."""

    queryset = m.Contract.objects.all()
    permission_classes = (
        IsAuthenticated,
        IsOrganizationUser,
        get_permission_profiles_have_access(
            m.ClientAdministrator, m.AgencyAdministrator
        ),
        get_permission_actions_available_to(
            CREATE_DELETE_ACTIONS, [m.ClientAdministrator]
        ),
        get_permission_actions_available_to(
            UPDATE_ACTIONS, [m.ClientAdministrator, m.AgencyAdministrator]
        ),
    )
    filterset_class = f.ContractFilterSet

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        """Return Contracts based on User type."""
        return m.Contract.objects.filter(self.request.user.profile.contracts_filter)

    def get_serializer_class(self):
        user = self.request.user

        if self.action in CREATE_ACTIONS:
            return s.CreateContractSerializer

        if self.action in UPDATE_ACTIONS:
            if getattr(self, 'swagger_fake_view', False):
                return s.YasgUpdateContractSerializer

            if type(user.profile) == m.ClientAdministrator:
                return s.ClientUpdateContractSerializer

            if type(user.profile) == m.AgencyAdministrator:
                return s.AgencyUpdateContractSerializer

        return s.ContractSerializer

    def perform_update(self, serializer):
        contract = serializer.instance
        was_signed = contract.is_signed
        contract = serializer.save()
        if not was_signed and contract.is_signed:
            contract.status = m.ContractStatus.INITIATED.key
            contract.save()

    def perform_create(self, serializer):
        """Set Contract client field value to the User Client."""
        contract = serializer.save(client=self.request.user.profile.client,)
        notify_client_created_contract(self.request.user, contract)

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(responses={200: 'OK'},)
    @add_permissions([IsClientUser()])
    def invite_multiple_agencies(self, request):
        """Find all agencies by filter and invite them"""
        client = request.user.profile.client

        # Creating filters
        filter = AgencyViewSet.filterset_class(request.data, request=request)
        filter.is_valid()

        # Generating QS
        agencies_qs = m.Agency.objects.all()
        agencies_qs = filter.filter_queryset(agencies_qs)

        # Searching in QS
        agency_view = AgencyViewSet()
        mock_request = lambda: None
        setattr(
            mock_request, 'query_params', {'search': request.data.get('search', None)}
        )

        if mock_request.query_params['search'] is not None:
            agencies_qs = SearchFilter().filter_queryset(
                mock_request, agencies_qs, agency_view
            )

        # Get agencies without contracts
        agencies_qs = agencies_qs.filter(contracts__isnull=True)

        # # Creating contracts
        contracts = (
            m.Contract(agency_id=agency.id, client=client) for agency in agencies_qs
        )
        contracts_qs = m.Contract.objects.bulk_create(contracts)

        for contract in contracts_qs:
            notify_client_created_contract(request.user, contract)

        return Response(len(agencies_qs))


class NotificationsViewSet(viewsets.ModelViewSet):
    """Viewset for Notification model."""

    queryset = m.Notification.objects.order_by('-timestamp').all()
    serializer_class = s.NotificationSerializer
    permission_classes = (IsAuthenticated,)
    filterset_fields = ('unread', 'verb')

    @fix_for_yasg
    def get_queryset(self):
        """Return Notification objects only for current user."""
        return self.queryset.filter(recipient=self.request.user)

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(
        operation_id='notifications_mark_all_as_read',
        request_body=no_body,
        responses={200: 'OK'},
    )
    def mark_all_as_read(self, request, format=None):
        """Mark all User notifications as read."""
        self.get_queryset().update(unread=False)
        return Response({})

    @action(methods=['post'], detail=True)
    @swagger_auto_schema(
        operation_id='notifications_mark_as_read',
        request_body=no_body,
        responses={200: 'OK'},
    )
    def mark_as_read(self, request, pk=None):
        """Mark the given Notification as read."""
        notification = get_object_or_404(self.get_queryset(), pk=pk)
        notification.unread = False
        notification.save()
        return Response({})


class DashboardViewSet(viewsets.ViewSet):
    """Viewset for dashboard data."""

    permission_classes = (BaseAccessPolicy,)

    @action(methods=['get'], detail=False)
    def get_statistics(self, request, *args, **kwargs):
        proposals = request.user.profile.apply_proposals_filter(
            m.Proposal.shortlist.all()
        )
        jobs = request.user.profile.apply_jobs_filter(m.Job.objects)

        return Response(
            {
                'total_candidates_submitted': proposals.count(),
                'pending_cv_review': proposals.filter(status__group='new').count(),
                'interviewing': proposals.filter(status__group='interviewing').count(),
                'offer_stage': proposals.filter(status__group='offer').count(),
                'wins': proposals.filter(status__group='offer_accepted').count(),
                'live_jobs': jobs.filter(
                    published=True, status=m.JobStatus.OPEN.key
                ).count(),
            }
        )


class ZohoViewSet(viewsets.ViewSet):
    permission_classes = (BaseAccessPolicy,)

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(
        request_body=s.ZohoGetSerializer, responses={200: s.ZohoCandidateSerializer()},
    )
    def get_candidate(self, request, *args, **kwargs):
        serializer = s.ZohoGetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        candidate_zoho_id = serializer.get_candidate_zoho_id()

        try:
            candidate_data = get_zoho_candidate(
                request.user.profile.org, candidate_zoho_id
            )
        except ZohoImportError as e:
            return Response({'detail': e.message}, status=status.HTTP_400_BAD_REQUEST)

        zoho_candidate_serializer = s.ZohoCandidateSerializer(
            data=candidate_data, context={'request': request}
        )
        zoho_candidate_serializer.is_valid(raise_exception=True)

        return Response(
            {
                'email': None,
                'first_name': None,
                'last_name': None,
                **zoho_candidate_serializer.validated_data,
            }
        )

    @action(methods=['post'], detail=False)
    @swagger_auto_schema(
        request_body=s.ZohoCandidateSerializer,
        responses={200: s.CandidateSerializer()},
    )
    def save_candidate(self, request, *args, **kwargs):
        serializer = s.ZohoCandidateSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        candidate = save_zoho_candidate(serializer.validated_data, request.user,)

        return Response(
            s.CandidateSerializer(candidate, context={'request': request}).data
        )


class FeedbackViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = m.Feedback.objects.none()
    serializer_class = s.FeedbackSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        """Set current user to 'created_by' field"""
        serializer.save(created_by=self.request.user,)


class AgencyCategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = m.AgencyCategory.objects.all()
    serializer_class = s.AgencyCategorySerializer
    pagination_class = None


class FunctionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = m.Function.objects.all()
    serializer_class = s.FunctionSerializer
    pagination_class = None


class TagViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = m.Tag.objects.annotate(
        candidates_count=Count('candidate_tags')
    ).order_by('-candidates_count')

    serializer_class = s.TagSerializer
    pagination_class = None
    filterset_class = f.TagFilterSet

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        user = self.request.user
        return user.profile.apply_tags_filter(self.queryset)


class AgencyClientInfoViewSet(
    viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin
):
    queryset = m.AgencyClientInfo.objects.all()
    permission_classes = (AgencyBaseAccessPolicy,)
    serializer_class = s.AgencyClientInfoSerializer
    lookup_field = 'client'

    def get_object(self):
        profile = self.request.user.profile
        client_id = self.kwargs.get('client')
        client = get_object_or_404(
            profile.org.apply_available_clients_filter(m.Client.objects),
            **{'pk': client_id},
        )

        if not self.queryset.filter(client=client, agency=profile.agency).exists():
            return m.AgencyClientInfo.objects.create(
                client=client, agency=profile.agency
            )

        return super().get_object()

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        profile = self.request.user.profile
        return self.queryset.filter(agency=profile.agency)


class FeeViewSet(
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = m.Fee.objects.prefetch_related(
        'placement',
        'placement__proposal',
        'job_contract__job',
        'placement__proposal__candidate',
    )

    permission_classes = (
        IsAuthenticated,
        IsAgencyUser,
        FeePermission,
    )

    serializer_class = s.FeeSerializer

    @fix_for_yasg
    def get_queryset(self):
        user = self.request.user

        if isinstance(user.org, m.Agency):
            queryset = self.queryset.filter(user.profile.fee_filter)

            if self.action == 'retrieve':
                queryset = queryset.annotate(
                    is_editable=get_bool_annotation(user.profile.editable_fee_filter)
                )

            return queryset

        return self.queryset.none()

    def handle_status_change(self, serializer):
        if serializer.validated_data['status'] == m.FeeStatus.PENDING.key:
            serializer.validated_data['submitted_by'] = self.request.user
            return

        if status == m.FeeStatus.APPROVED.key:
            instance = getattr(serializer, 'instance', None)
            proposal = serializer.validated_data['proposal']
            proposal.create_comment_placed(
                instance.submitted_by
                if instance and instance.submitted_by
                else self.request.user
            )


class FeeSplitAllocationViewSet(
    viewsets.GenericViewSet,
    ValidateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = m.FeeSplitAllocation.objects.all()

    permission_classes = (
        IsAuthenticated,
        IsAgencyUser,
        FeeSplitAllocationPermission,
    )

    serializer_class = s.FeeSplitAllocationSerializer

    def get_serializer_class(self):
        if self.action in VALIDATE_ACTIONS:
            return s.ValidateCandidateSplitAllocationSerializer

        return self.serializer_class

    @fix_for_yasg
    def get_queryset(self):
        user = self.request.user

        if isinstance(user.org, m.Agency):
            queryset = self.queryset.prefetch_related('fee').filter(
                fee__in=m.Fee.objects.filter(user.profile.fee_filter)
            )

            queryset = queryset.annotate(fee_status=F('fee__status'))

            return queryset

        return self.queryset.none()

    @action(methods=['post'], detail=True, parser_classes=(MultiPartParser,))
    @swagger_auto_schema(
        responses={200: s.CandidateSplitAllocationFileSerializer},
        consumes=['multipart/form-data'],
        request_body=s.FileSerializer,
    )
    def upload_file(self, request, pk):
        file = request.data.get('file', None)
        if file is None:
            return Response({'detail': _('No file in request data.')}, 400)

        instance = self.get_object()
        instance.file = file
        instance.save()

        serializer = s.CandidateSplitAllocationFileSerializer(instance)
        return Response(serializer.data)

    @action(methods=['delete'], detail=True)
    def delete_file(self, request, pk):
        instance = self.get_object()
        instance.file.delete()
        instance.save()

        return Response({'detail': _('File deleted')})

    @action(methods=['get'], detail=True, parser_classes=(MultiPartParser,))
    def get_file(self, request, pk):
        instance = self.get_object()
        file = instance.file

        if not (file and file.file):
            return Response({'detail': _('File not found.')}, 404)

        filename = file.name.split('/')[-1]
        response = HttpResponse(file.file, content_type='application/force-download',)
        response['Content-Disposition'] = 'inline; filename="{}"'.format(filename)
        return response


class DealPipelineViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (AgencyBaseAccessPolicy,)
    serializer_class = s.DealPipelineProposalSerializer
    queryset = m.Proposal.objects.select_related('candidate', 'job', 'status')
    filterset_class = f.DealPipelineFilterSet
    search_fields = (
        'candidate__first_name',
        'candidate__last_name',
        'job__title',
        'job__responsibilities',
    )

    @fix_for_yasg
    @require_user_profile
    def get_queryset(self):
        profile = self.request.user.profile
        return annotate_proposal_deal_pipeline_metrics(
            profile.apply_proposals_filter(
                self.queryset.filter(
                    ~Q(status__deal_stage=m.ProposalDealStages.OUT_OF.key)
                )
            ),
            profile.org,
        )

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(
        operation_id='get_deal_pipeline_metrics',
        responses={200: s.DealPipelineMetricsSerializer()},
    )
    def predicted_values(self, request, *args, **kwargs):
        profile = self.request.user.profile
        coefficients = profile.agency.deal_pipeline_coefficients

        deal_metrics = {
            'first_round': 0,
            'intermediate_round': 0,
            'final_round': 0,
            'offer': 0,
        }

        proposals = self.get_queryset()
        filtered_ids = {item.id for item in self.filter_queryset(self.get_queryset())}

        job_opening_counters = {
            item['job']: item['job__openings_count']
            for item in list(proposals.values('job', 'job__openings_count').distinct())
        }

        for proposal in proposals:
            # The max number of candidates is equal to max openings value
            if job_opening_counters[proposal.job.pk] > 0:
                if proposal.id in filtered_ids:
                    value = proposal.converted_current_salary
                    deal_metrics[proposal.status.deal_stage] += value

                job_opening_counters[proposal.job.pk] -= 1

        total = {}
        realistic = {}

        for round, value in deal_metrics.items():
            total[round] = int(value * coefficients['hiring_fee'])
            realistic[round] = int(total[round] * coefficients[round])

        total['total'] = sum(total.values())
        realistic['total'] = sum(realistic.values())

        return Response({'total': total, 'realistic': realistic})


class InterviewTemplateViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = m.InterviewTemplate.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = s.InterviewTemplateSerializer


class LegalAgreementViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = m.LegalAgreement.latest_objects.all()
    serializer_class = s.LegalAgreementSerializer
    lookup_field = 'document_type'

    @action(methods=['get'], detail=True)
    @swagger_auto_schema(responses={200: 'OK'},)
    def file(self, request, *args, **kwargs):
        agreement = self.get_object()
        if agreement.file is None or agreement.file.name == '':
            return Response({'detail': _('Not found.')}, 404)

        filename = agreement.file.name.split('/')[-1]
        response = HttpResponse(agreement.file, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="{}"'.format(filename)

        return response


class NoteActivityViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = m.NoteActivity.objects.all()
    permission_classes = (NoteActivityAccessPolicy,)
    filterset_class = f.NoteActivityFilterSet
    serializer_class = s.NoteActivitySerializer

    def filter_queryset(self, queryset):
        if self.action != 'list':
            self.filterset_class = None
        return super().filter_queryset(queryset)

    def list(self, request, *args, **kwargs):
        query_serializer = s.NoteActivityQuerySerializer(
            data=self.request.query_params, context={'request': self.request}
        )
        query_serializer.is_valid(raise_exception=True)

        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        note = serializer.save()
        note.send_notifications()
