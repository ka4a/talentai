import decimal
import json
import requests
import uuid
from decimal import Decimal
from typing import OrderedDict

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.db.utils import IntegrityError
from django.utils.timezone import now
from django.utils.translation import get_language, gettext_lazy as _
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from rest_framework.utils import model_meta
from reversion.models import Version

from core import models as m, serializer_fields
from core.constants import QuickActionVerb
from core.utils.model import get_fee_status_update_and_notify
from core.utils import (
    parse_linkedin_slug,
    require_request,
    poly_relation_filter,
    get_user_org,
    filter_out_serializer_fields,
    has_researcher_feature,
    get_unique_emails_filter,
    pop,
)
from core.validators import (
    ModeChoicesValidator,
    ModeRequireFieldsValidator,
    ModeRequirementValidator,
    RequireIfValidator,
    RequireOneOfValidator,
    FieldsSumValidator,
    SplitHasUserValidator,
)
from core.zoho import get_candidate_id_from_zoho_url

ORG_TYPES = ('agency', 'client')


def update_instance_fields(instance, data):
    """Update instance fields with data dict.

    Based on ModelSerializer.update
    """
    info = model_meta.get_field_info(instance)

    for attr, value in data.items():
        if attr in info.relations and info.relations[attr].to_many:
            field = getattr(instance, attr)
            field.set(value)
        else:
            setattr(instance, attr, value)

    return instance


def represent_dt(dt):
    return serializers.DateTimeField().to_representation(dt)


class UserRegistrationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.User
        fields = ('email', 'first_name', 'last_name', 'password', 'country')
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'password': {'write_only': True},
        }

    def validate(self, data):
        try:
            validate_password(password=data.get('password'), user=m.User(**data))
        except ValidationError as e:
            raise serializers.ValidationError({'password': e.messages})

        return super().validate(data)


class ReasonDeclineCandidateOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ReasonDeclineCandidateOption
        fields = ('id', 'text', 'has_description')


class ReasonNotInterestedOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ReasonNotInterestedCandidateOption
        fields = ('id', 'text', 'has_description')


class AgencyRegistrationRequestSerializer(serializers.ModelSerializer):
    """Serializer for the AgencyRegistrationRequest model."""

    user = UserRegistrationRequestSerializer()
    terms_of_service = serializers.BooleanField(required=True, write_only=True)
    token = serializers.CharField(required=False, write_only=True)
    via_job = serializer_fields.JobUuidRelatedField(required=False, write_only=True)

    class Meta:  # noqa
        model = m.AgencyRegistrationRequest
        fields = (
            'name',
            'user',
            'created',
            'terms_of_service',
            'token',
            'via_job',
            'country',
        )
        read_only_fields = ('created',)

    def validate_terms_of_service(self, value):
        if not value:
            self.fields['terms_of_service'].fail('required')

        return value

    def create(self, validated_data):
        validated_data.pop('terms_of_service')
        invite_token = validated_data.pop('token', None)
        user_validated_data = validated_data.pop('user')

        # Country is required for agency users
        country = user_validated_data.get('country', None)
        if not country:
            raise serializers.ValidationError(
                {'user.country': [_('Country is required for Agency Users')]}
            )

        user = m.User.objects.create_user(**user_validated_data)

        instance = m.AgencyRegistrationRequest.objects.create(
            user=user, **validated_data
        )

        if invite_token:
            try:
                with transaction.atomic():
                    agency = instance.approve()

                    invited = m.AgencyInvite.objects.filter(
                        token=invite_token, used_by=None
                    ).update(used_by=agency)

                    if not invited:
                        raise ValueError('Invite is already used')
            except ValueError:
                instance.refresh_from_db()

        return instance


class ClientRegistrationRequestSerializer(serializers.ModelSerializer):
    """Serializer for the ClientRegistrationRequest model."""

    user = UserRegistrationRequestSerializer()
    terms_of_service = serializers.BooleanField(required=True, write_only=True)

    class Meta:  # noqa
        model = m.ClientRegistrationRequest
        fields = ('name', 'user', 'terms_of_service', 'country')

    def validate_terms_of_service(self, value):
        if not value:
            self.fields['terms_of_service'].fail('required')

        return value

    def create(self, validated_data):
        validated_data.pop('terms_of_service')
        user_validated_data = validated_data.pop('user')

        user = m.User.objects.create_user(**user_validated_data)

        instance = m.ClientRegistrationRequest.objects.create(
            user=user, **validated_data
        )
        return instance


class UserProfileOrgSerializer(serializers.Serializer):
    has_zoho_integration = serializers.BooleanField(read_only=True)
    name = serializers.CharField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    is_career_site_enabled = serializers.BooleanField(read_only=True)
    career_site_slug = serializers.CharField(read_only=True)


class UserProfileSerializer(serializers.Serializer):
    org = UserProfileOrgSerializer(read_only=True)


class NotificationSettingSerializer(serializers.ModelSerializer):
    """Serializer for the Notification Types."""

    name = serializers.CharField(source='notification_type_group')
    description = serializers.CharField(source='get_notification_type_group_display')
    email = serializers.BooleanField()

    class Meta:  # noqa
        model = m.NotificationSetting
        fields = ('id', 'name', 'description', 'email')
        read_only_fields = ('name', 'description')


def pagination_validator(value):
    if value not in m.FrontendSettingsSchema.PAGINATION_SCHEMA:
        raise ValidationError(
            f'The value {value} is not allowed. Must be one of '
            f'{m.FrontendSettingsSchema.PAGINATION_SCHEMA}'
        )

    return value


class FrontendSettingsSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

        for field in self.Meta.pagination_fields:
            self.fields[field] = serializers.IntegerField(
                required=False, validators=[pagination_validator]
            )

    class Meta:
        pagination_fields = (
            'dashboard_jobs_show_per',
            'dashboard_proposals_show_per',
            'jobs_show_per',
            'jobs_shortlist_show_per',
            'jobs_longlist_show_per',
            'candidates_show_per',
            'organizations_show_per',
            'agency_directory_show_per',
            'staff_show_per',
            'notifications_show_per',
            'agency_proposals_show_per',
            'client_jobs_show_per',
            'submit_candidates_show_per',
            'proposals_snapshot_show_per',
            'assign_members_show_per',
            'deal_pipeline_candidates_show_per',
            'job_import_longlist_show_per',
            'candidate_placements_show_per',
        )


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    photo = serializers.FileField(read_only=True)

    groups = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')

    profile = UserProfileSerializer(read_only=True)
    notification_settings = NotificationSettingSerializer(many=True, read_only=True)

    is_researcher = serializers.SerializerMethodField(read_only=True)

    def get_is_researcher(self, instance):
        return has_researcher_feature(instance.profile)

    class Meta:  # noqa
        model = m.User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'photo',
            'locale',
            'is_staff',
            'is_active',
            'is_activated',
            'groups',
            'profile',
            'frontend_settings',
            'notification_settings',
            'is_researcher',
            'country',
            'is_legal_agreed',
        )


class PublicUserSerializer(serializers.ModelSerializer):
    """Serializer for User model without sensitive fields like settings."""

    class Meta:  # noqa
        model = m.User
        fields = ('id', 'first_name', 'last_name', 'photo')


class UpdateUserLegalSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.User
        fields = ('is_legal_agreed',)


class UserUpdateSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )
    new_password = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )
    frontend_settings = FrontendSettingsSerializer()
    notification_settings = NotificationSettingSerializer(many=True, required=False)

    class Meta:
        model = m.User
        fields = (
            'email',
            'first_name',
            'last_name',
            'locale',
            'frontend_settings',
            'notification_settings',
            'old_password',
            'new_password',
            'country',
            'is_legal_agreed',
        )

    def validate(self, data):
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if new_password:
            errors = {}

            if not old_password:
                errors['old_password'] = self.fields['old_password'].error_messages[
                    'required'
                ]
            elif not self.instance.check_password(old_password):
                errors['old_password'] = _(
                    'Your old password was entered incorrectly. '
                    'Please enter it again.'
                )

            try:
                user_data = {
                    k: v
                    for k, v in data.items()
                    if k in ['email', 'first_name', 'last_name']
                }
                validate_password(password=new_password, user=m.User(**user_data))
            except ValidationError as e:
                errors['new_password'] = e.messages

            if errors:
                raise ValidationError(errors)

        return super().validate(data)

    def update(self, instance, validated_data):
        validated_data.pop('old_password', None)
        new_password = validated_data.pop('new_password', None)
        frontend_settings = validated_data.pop('frontend_settings', None)
        notification_settings = validated_data.pop('notification_settings', [])

        update_instance_fields(instance, validated_data)

        if new_password:
            instance.set_password(new_password)

        if frontend_settings:
            instance.frontend_settings.update(frontend_settings)

        for setting_data in notification_settings:
            notification_type_group = setting_data.pop('notification_type_group', None)
            setting_data.pop('id', None)
            setting_data.pop('get_notification_type_group_display', None)
            m.NotificationSetting.objects.update_or_create(
                user=instance,
                notification_type_group=notification_type_group,
                defaults=setting_data,
            )

        instance.save()
        return instance


class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)

    @property
    def user(self):
        """Return the User with the given email."""
        user = m.User.objects.filter(email=self.initial_data['email']).first()

        if user and user.check_password(self.initial_data['password']):
            return user


class ContractWithJobsSerializer(serializers.ModelSerializer):
    class _Job(serializers.ModelSerializer):
        class Meta:
            fields = ('id', 'title', 'responsibilities')
            model = m.Job

    jobs = serializers.SerializerMethodField()

    def get_jobs(self, contract):
        if contract.status not in m.CONTRACT_STATUSES_ALLOW_JOBS:
            return []

        return self._Job(
            contract.client.jobs.exclude(
                status__in=m.JOB_STATUSES_CLOSED, published=False
            ),
            many=True,
        ).data


class ContractSerializer(ContractWithJobsSerializer):
    """Serializer for the Contract model."""

    class _Client(serializers.ModelSerializer):
        class Meta:
            fields = ('id', 'name')
            model = m.Client

    class _Agency(serializers.ModelSerializer):
        class Meta:
            fields = ('id', 'name')
            model = m.Agency

    client = _Client(read_only=True)
    agency = _Agency(read_only=True)

    class Meta:  # noqa
        model = m.Contract
        _fields = (
            'id',
            'status',
            'client',
            'agency',
            'jobs',
            'start_at',
            'end_at',
            'fee_currency',
            'initial_fee',
            'fee_rate',
            'is_client_signed',
            'is_agency_signed',
            'days_until_invitation_expire',
        )
        fields = _fields
        read_only_fields = _fields


class CreateContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Contract
        fields = (
            'id',
            'status',
            'agency',
            'invite_duration_days',
        )
        read_only_fields = ('id',)


class YasgUpdateContractSerializer(serializers.ModelSerializer):
    """
    Combination of ClientUpdateContractSerializer and AgencyUpdateContractSerializer
    for swagger spec generator
    """

    class Meta:
        model = m.Contract
        fields = (
            # ClientUpdateContractSerializer
            'id',
            'status',
            'is_client_signed',
            'invite_duration_days',
            # AgencyUpdateContractSerializer
            'is_agency_signed',
        )
        read_only_fields = ('id',)


class ClientUpdateContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Contract
        fields = (
            'id',
            'status',
            'is_client_signed',
            'invite_duration_days',
        )
        read_only_fields = ('id',)


class AgencyUpdateContractSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(
        required=False, choices=m.CONTRACT_STATUSES_AGENCY_ALLOWED_TO_SET
    )

    class Meta:
        model = m.Contract
        fields = (
            'id',
            'status',
            'is_agency_signed',
        )
        read_only_fields = ('id',)


class UserResetPasswordSerializer(serializers.Serializer):
    email = serializers.CharField(required=True, write_only=True)


class UserSetPasswordSerializer(serializers.Serializer):
    uidb64 = serializers.CharField(required=True, write_only=True)
    token = serializers.CharField(required=True, write_only=True)
    new_password1 = serializers.CharField(required=True, write_only=True)
    new_password2 = serializers.CharField(required=True, write_only=True)


class UserChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password1 = serializers.CharField(required=True, write_only=True)
    new_password2 = serializers.CharField(required=True, write_only=True)


class UserActivationFormSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, write_only=True)


class NotificationsCountSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=0)


class YasgClientSerializer(serializers.ModelSerializer):
    """
    Combination of ClientSerializer and CreateUpdateAgencyClientSerializer
    for swagger spec generator
    """

    proposals_count = serializers.SerializerMethodField()
    open_jobs_count = serializers.SerializerMethodField()

    @require_request
    def get_proposals_count(self, obj):
        """Return number of proposals."""
        user = self.context['request'].user

        if not hasattr(user.profile, 'agency'):
            return

        return m.Proposal.objects.filter(
            candidate__agency=user.profile.agency, job__client=obj,
        ).count()

    @require_request
    def get_open_jobs_count(self, obj):
        """Return number of open jobs."""
        user = self.context['request'].user

        if not hasattr(user.profile, 'agency'):
            return

        return user.profile.apply_jobs_filter(
            m.Job.objects.filter(client=obj, status=m.JobStatus.OPEN.key,)
        ).count()

    class Meta:
        model = m.Client
        fields = (
            # ClientSerializerFields
            'id',
            'name',
            'proposals_count',
            'open_jobs_count',
            'owner_agency_id',
        )


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for the Client model."""

    proposals_count = serializers.SerializerMethodField()
    open_jobs_count = serializers.SerializerMethodField()

    class Meta:  # noqa
        model = m.Client
        fields = (
            'id',
            'name',
            'proposals_count',
            'open_jobs_count',
            'country',
            'owner_agency_id',
        )

    @require_request
    def get_proposals_count(self, obj):
        """Return number of proposals."""
        user = self.context['request'].user

        if not hasattr(user.profile, 'agency'):
            return

        return m.Proposal.objects.filter(
            candidate__agency=user.profile.agency, job__client=obj,
        ).count()

    @require_request
    def get_open_jobs_count(self, obj):
        """Return number of open jobs."""
        user = self.context['request'].user

        if not hasattr(user.profile, 'agency'):
            return

        return user.profile.apply_jobs_filter(
            m.Job.objects.filter(client=obj, status=m.JobStatus.OPEN.key,)
        ).count()


class CreateUpdateAgencyClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Client
        fields = ('name',)

    @require_request
    def save(self, **kwargs):
        profile = self.context['request'].user.profile

        return super().save(owner_agency=profile.agency, **kwargs)


class TeamSerializer(serializers.ModelSerializer):
    class Meta:  # noqa
        model = m.Team
        fields = ('id', 'name')
        read_only_fields = fields


class UpdateStaffSerializer(serializers.ModelSerializer):
    class Meta:  # noqa
        model = m.User
        fields = (
            'first_name',
            'last_name',
            'country',
            'locale',
        )


class StaffSerializer(serializers.ModelSerializer):
    """Serializer for org staff User."""

    group = serializers.CharField(read_only=True, source='profile.group_name')

    photo = serializers.FileField(read_only=True)

    class Meta:  # noqa
        model = m.User
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'group',
            'photo',
        )


class RetrieveStaffSerializer(StaffSerializer):
    """Serializer for org staff User details"""

    class Meta(StaffSerializer.Meta):
        fields = StaffSerializer.Meta.fields + (
            'locale',
            'country',
            'last_login',
            'date_joined',
        )


class StaffWithAvatarSerializer(serializers.ModelSerializer):
    photo = serializers.FileField(read_only=True)

    class Meta:  # noqa
        model = m.User
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'photo',
        )


class AgencyMemberSerializer(serializers.ModelSerializer):
    """Serializer for Agency Recruiter."""

    teams = TeamSerializer(many=True, source='profile.teams', read_only=True)

    class Meta:  # noqa
        model = m.User
        fields = ('id', 'first_name', 'last_name', 'email', 'teams')


class AgencySerializer(serializers.ModelSerializer):
    """Serializer for the Agency model."""

    members = AgencyMemberSerializer(many=True, read_only=True)

    class Meta:  # noqa
        model = m.Agency
        fields = ('id', 'name', 'members', 'country')


class AgencyListSerializer(serializers.ModelSerializer):
    """Serializer for Agency for Agency Directory page.

    It has `contract` and `proposals_count` fields.
    """

    contract = serializers.SerializerMethodField()

    members = AgencyMemberSerializer(many=True, read_only=True)
    proposals_count = serializers.SerializerMethodField()

    class Meta:  # noqa
        model = m.Agency
        fields = (
            'id',
            'name',
            'name_ja',
            'website',
            'logo',
            'description',
            'contract',
            'proposals_count',
            'members',
            'categories',
            'function_focus',
        )
        read_only_fields = fields

    @swagger_serializer_method(serializer_or_field=ContractSerializer)
    @require_request
    def get_contract(self, obj):
        """Return serialized Contract data."""
        user = self.context['request'].user

        if not hasattr(user.profile, 'contracts_filter'):
            return

        contract = m.Contract.objects.filter(
            user.profile.contracts_filter, agency=obj
        ).first()

        if contract:
            return ContractSerializer(contract).data

    @require_request
    def get_proposals_count(self, obj):
        """Return number of Proposals made by an Agency."""
        user = self.context['request'].user

        if not hasattr(user.profile, 'client'):
            return

        return m.Proposal.objects.filter(
            job__client=user.profile.org, candidate__agency=obj,
        ).count()


class LanguageSerializer(serializers.ModelSerializer):
    """Serializer for the Language model."""

    formatted = serializers.SerializerMethodField()

    def get_formatted(self, language):
        return str(language)

    class Meta:  # noqa
        model = m.Language
        fields = ('id', 'language', 'level', 'formatted')

    def get_unique_together_validators(self):
        """Remove unique together validation on serializer.

        This serializer isn't used for creating new Languages, therefore
        uniqueness validation from the model is not needed.
        """
        return []


class CandidateQuerySerializer(serializers.Serializer):
    """Serializer for parameter of CandidateSerializer.get_proposed."""

    include_archived = serializers.BooleanField(required=False)

    check_proposed_to = serializer_fields.JobPrimaryKeyRelatedField(
        required=False, help_text='ID of job to check if Candidate is proposed'
    )


class CandidateRetrieveQuerySerializer(serializers.Serializer):
    """Serializer for parameters of retrieve candidate view"""

    extra_fields = serializers.CharField(required=False)


class OrgStatusesQuerySerializer(serializers.Serializer):
    """Serializer for parameter of CandidateSerializer.get_proposed."""

    default_error_messages = {
        'no_access': 'You have no access to organisation proposal statuses'
    }

    org_id = serializers.IntegerField()
    org_type = serializers.ChoiceField(choices=ORG_TYPES)

    @require_request
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        org_id = validated_data.get('org_id')
        org_type = validated_data.get('org_type')

        org = None
        if org_type == 'agency':
            org = m.Agency.objects.get(id=org_id)

        if org_type == 'client':
            org = m.Client.objects.get(id=org_id)

        user_org = self.context['request'].user.profile.org

        if org != user_org:
            if not org.has_contract_with(user_org):
                raise serializers.ValidationError(
                    self.default_error_messages['no_access']
                )

        return validated_data


class OrgMemberSerializer(PublicUserSerializer):
    @require_request
    def to_representation(self, instance):
        user = self.context['request'].user
        instance_profile = getattr(instance, 'profile', None)

        if instance_profile and instance_profile.org == user.profile.org:
            return super().to_representation(instance)


class DurationSerializer(serializers.Serializer):
    date_start = serializers.DateField(required=False, allow_null=True)
    date_end = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        date_start = attrs.get('date_start')
        date_end = attrs.get('date_end')
        currently_pursuing = attrs['currently_pursuing']

        if not currently_pursuing:
            if not date_end:
                raise ValidationError({'date_end': [_('This field may not be blank.')]})

            elif date_start is not None and date_end < date_start:
                raise ValidationError(
                    {'date_end': [_('End date can\'t be less than Start date.')]}
                )

        return super().validate(attrs)


class EducationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.EducationDetail
        fields = (
            'institute',
            'department',
            'degree',
            'date_start',
            'date_end',
            'currently_pursuing',
        )
        extra_kwargs = {
            'degree': {'allow_blank': False},
            'institute': {'allow_blank': False},
        }


class ExperienceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ExperienceDetail
        fields = (
            'occupation',
            'company',
            'summary',
            'location',
            'currently_pursuing',
            'date_start',
            'date_end',
        )
        extra_kwargs = {
            'occupation': {'allow_blank': False},
            'company': {'allow_blank': False},
        }


class CandidateProposalSerializer(serializers.ModelSerializer):
    company = serializers.CharField(source='job.client.name')
    job_name = serializers.CharField(source='job.title')
    job_id = serializers.IntegerField(source='job.id')
    status = serializers.CharField(source='status.status')
    stage = serializers.CharField(source='status.stage')

    class Meta:
        model = m.Proposal
        fields = (
            'id',
            'job_id',
            'company',
            'job_name',
            'stage',
            'status',
        )


class FormEducationDetailSerializer(EducationDetailSerializer, DurationSerializer):
    pass


class FormExperienceDetailSerializer(ExperienceDetailSerializer, DurationSerializer):
    date_start = serializers.DateField(required=False, allow_null=False)


class UpdateCandidateFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.CandidateFile
        fields = ('is_shared', 'title')


class CandidateFileCandidateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)
    file = serializers.FileField(read_only=True)
    thumbnail = serializers.FileField(read_only=True)
    preview = serializers.FileField(read_only=True)

    class Meta:
        model = m.CandidateFile
        fields = ('is_shared', 'id', 'title', 'file', 'preview', 'thumbnail')


class CandidateFileSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)
    thumbnail = serializers.FileField(read_only=True)
    preview = serializers.FileField(read_only=True)
    candidate = serializer_fields.CandidatePrimaryKeyRelatedField(required=True)

    class Meta:
        model = m.CandidateFile
        fields = (
            'id',
            'title',
            'file',
            'is_shared',
            'candidate',
            'preview',
            'thumbnail',
        )

    @require_request
    def create(self, validated_data):
        profile = self.context['request'].user.profile

        return super().create({**validated_data, 'organization': profile.org})


class PublicCandidateFileSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)
    thumbnail = serializers.FileField(read_only=True)
    preview = serializers.FileField(read_only=True)
    candidate = serializers.PrimaryKeyRelatedField(
        queryset=m.Candidate.objects.all(), required=True
    )

    class Meta:
        model = m.CandidateFile
        fields = (
            'id',
            'title',
            'file',
            'is_shared',
            'candidate',
            'preview',
            'thumbnail',
        )

    def create(self, validated_data):
        candidate_owner = validated_data['candidate'].owner

        return super().create(
            {**validated_data, 'organization': candidate_owner.profile.org}
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Tag
        fields = ('id', 'name')


class CandidateTagSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='tag.name')

    class Meta:
        model = m.CandidateTag
        fields = ('name',)


class JobSkillSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='tag.name')

    class Meta:
        model = m.JobSkill
        fields = ('name',)


class CandidateCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.CandidateCertification
        fields = ('id', 'certification', 'certification_other', 'score')
        read_only_fields = ('id',)


CANDIDATE_FLAGS = {
    'original',
    'is_missing_required_fields',
    'archived',
    'is_met',
    'is_client_contact',
}

CANDIDATE_FEATURE_FIELDS = {
    'researcher_feature': ['name_collect', 'mobile_collect'],
}

AGENCY_ONLY_CANDIDATE_FIELDS = [
    'skill_domain',
    'lead_consultant',
    'support_consultant',
    'is_client_contact',
    'activator',
    'client_brief',
]


class BasicCandidateSerializer(serializers.ModelSerializer):
    """Serializer for the Candidate model."""

    photo = serializers.FileField(read_only=True)
    resume = serializers.FileField(read_only=True)
    resume_thumbnail = serializers.FileField(read_only=True)
    resume_ja = serializers.FileField(read_only=True)
    resume_ja_thumbnail = serializers.FileField(read_only=True)
    cv_ja = serializers.FileField(read_only=True)
    cv_ja_thumbnail = serializers.FileField(read_only=True)
    languages = LanguageSerializer(many=True, required=False)

    linkedin_url = serializers.URLField(allow_blank=True, required=False)

    proposed_to_job = serializers.BooleanField(required=False)
    proposed = serializers.SerializerMethodField()
    linkedin_data = serializers.SerializerMethodField()

    education_details = EducationDetailSerializer(many=True, required=False)
    experience_details = ExperienceDetailSerializer(many=True, required=False)

    proposals = CandidateProposalSerializer(many=True, read_only=True)

    is_missing_required_fields = serializers.SerializerMethodField()

    original = serializer_fields.CandidatePrimaryKeyRelatedField(
        required=False, allow_null=True
    )

    tags = CandidateTagSerializer(source='candidatetag_set', many=True, required=False)

    certifications = CandidateCertificationSerializer(many=True, required=False)

    created_by = OrgMemberSerializer(read_only=True)
    updated_by = OrgMemberSerializer(read_only=True)

    # researcher's fields
    name_collect = serializer_fields.OrgMemberPrimaryKeyRelatedField(
        required=False, allow_null=True
    )
    mobile_collect = serializer_fields.OrgMemberPrimaryKeyRelatedField(
        required=False, allow_null=True
    )
    # end researcher's fields

    activator = serializer_fields.OrgMemberPrimaryKeyRelatedField(
        required=False, allow_null=True
    )
    referred_by = serializer_fields.OrgMemberPrimaryKeyRelatedField(
        required=False, allow_null=True
    )

    # extra_fields
    placement_approved_at = serializers.DateField(read_only=True)

    # rich fields
    reason_for_job_changes = serializer_fields.RichTextField(required=False)
    companies_already_applied_to = serializer_fields.RichTextField(required=False)
    companies_applied_to = serializer_fields.RichTextField(required=False)
    summary = serializer_fields.RichTextField(required=False)
    client_brief = serializer_fields.RichTextField(required=False)

    @require_request
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        profile = self.context['request'].user.profile
        researcher_fields = CANDIDATE_FEATURE_FIELDS['researcher_feature']

        if not has_researcher_feature(profile) or instance.organization != profile.org:
            representation = filter_out_serializer_fields(
                representation, researcher_fields
            )

        if not hasattr(profile, 'agency') or instance.organization != profile.org:
            representation = filter_out_serializer_fields(
                representation, AGENCY_ONLY_CANDIDATE_FIELDS
            )

        return representation

    @require_request
    def to_internal_value(self, data):
        profile = self.context['request'].user.profile
        researcher_fields = CANDIDATE_FEATURE_FIELDS['researcher_feature']

        if not has_researcher_feature(profile):
            data = filter_out_serializer_fields(data, researcher_fields)

        if not hasattr(profile, 'agency'):
            data = filter_out_serializer_fields(data, AGENCY_ONLY_CANDIDATE_FIELDS)

        return super().to_internal_value(data)

    @require_request
    def validate_is_client_contact(self, is_client_contact):
        user = self.context['request'].user
        if not isinstance(user.profile.org, m.Agency):
            self.fields['is_client_contact'].fail('agency_only_field')

        return is_client_contact

    @require_request
    def validate(self, attrs):
        validated_data = super().validate(attrs)

        if 'other_desired_benefits' in validated_data:
            other_desired_benefits = validated_data.get('other_desired_benefits')
            if 'other' in other_desired_benefits:
                if not validated_data.get('other_desired_benefits_others_detail'):
                    raise ValidationError(
                        {
                            'other_desired_benefits_others_detail',
                            _('This field is required'),
                        }
                    )
            else:
                validated_data['other_desired_benefits_others_detail'] = ''

        return validated_data

    class Meta:  # noqa
        model = m.Candidate
        fields = (
            'id',
            'photo',
            'first_name',
            'middle_name',
            'last_name',
            'name',
            'name_ja',
            'first_name_kanji',
            'last_name_kanji',
            'first_name_katakana',
            'last_name_katakana',
            'created_at',
            'updated_at',
            'proposed_to_job',
            'proposals',
            'current_company',
            'current_city',
            'current_position',
            'employment_status',
            'linkedin_url',
            'github_url',
            'website_url',
            'twitter_url',
            'summary',
            'fulltime',
            'parttime',
            'local',
            'remote',
            'reason_for_job_changes',
            'languages',
            'resume',
            'resume_thumbnail',
            'resume_ja',
            'resume_ja_thumbnail',
            'cv_ja',
            'cv_ja_thumbnail',
            'proposed',
            'linkedin_data',
            'zoho_id',
            'experience_details',
            'education_details',
            'tags',
            'internal_status',
            *CANDIDATE_FLAGS,
            'created_by',
            'updated_by',
            'current_country',
            'name_collect',
            'mobile_collect',
            'activator',
            'skill_domain',
            'lead_consultant',
            'support_consultant',
            'referred_by',
            'industry',
            'department',
            'client_expertise',
            'client_brief',
            'push_factors',
            'pull_factors',
            'companies_already_applied_to',
            'companies_applied_to',
            'age',
            'nationality',
            'placement_approved_at',
            'birthdate',
            'gender',
            'current_street',
            'current_postal_code',
            'current_prefecture',
            'max_num_people_managed',
            'certifications',
        )
        read_only_fields = (
            'id',
            'agency',
            'name',
            'archived',
            'zoho_id',
            'created_at',
            'proposed_to_job',
            'proposals',
        )
        extra_kwargs = {
            'email': {'allow_blank': True},
            'first_name': {'allow_blank': True},
            'last_name': {'allow_blank': True},
        }

    def get_is_missing_required_fields(self, candidate):
        for field_name in (
            'email',
            'current_position',
            'current_company',
            'source',
            'owner',  # sourced by
            'resume',
        ):
            if not getattr(candidate, field_name, None):
                return True

        if getattr(candidate, 'current_salary') is None:
            return True

        if candidate.languages.count() == 0:
            return True

        return False

    @swagger_serializer_method(serializer_or_field=serializers.BooleanField)
    def get_proposed(self, candidate):
        """Return True if was proposed to job passed via parameter."""
        job = self.context.get('check_proposed_to')

        if not job:
            return

        return m.Proposal.objects.filter(candidate=candidate, job=job).exists()

    @swagger_serializer_method(serializer_or_field=serializers.JSONField)
    @require_request
    def get_linkedin_data(self, candidate):
        """Return linkedin data if User has permission."""
        user = self.context['request'].user
        can_view_raw_data = (
            hasattr(user, 'profile')
            and (
                hasattr(user.profile, 'agency')
                and user.profile.agency.pk in settings.CANDIDATE_RAW_DATA_AGENCY_IDS
            )
            or (
                hasattr(user.profile, 'client')
                and user.profile.client.pk in settings.CANDIDATE_RAW_DATA_CLIENT_IDS
            )
        )

        if can_view_raw_data:
            return candidate.linkedin_data

    def validate_linkedin_url(self, linkedin_url):
        if linkedin_url:
            if parse_linkedin_slug(linkedin_url) is None:
                raise ValidationError(_('LinkedIn URL is not correct'))

            linkedin_url = linkedin_url.split('?', 1)[0].split('#', 1)[0]

            # to validate after query str is removed
            if len(linkedin_url) > 200:
                self.fields['linkedin_url'].fail(
                    'max_length',
                    max_length=(m.Candidate._meta.get_field('linkedin_url').max_length),
                )

        return linkedin_url

    def validate_languages(self, languages):
        """Check if Candidate has unique Languages."""
        if len(languages) != len(set(l.get('language') for l in languages)):
            raise serializers.ValidationError(
                _('Should have only one level of each language.')
            )
        return languages

    def save(self, organization=None):
        """Create and update CandidateNote along with the Candidate."""
        organization = organization or self.instance.organization
        super().save(organization=organization)

        note_data = self.context['request'].data.get('note')
        if note_data is not None:
            self.instance.set_note(
                self.context['request'].user.profile.org,
                serializer_fields.RichTextField().to_internal_value(note_data),
            )

        return self.instance


class CandidateSerializer(BasicCandidateSerializer):
    secondary_email = serializers.EmailField(allow_blank=True, required=False)
    address = serializers.SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=serializers.CharField)
    def get_address(self, candidate):
        perfecture_postal_code_parts = (
            candidate.current_prefecture,
            candidate.current_postal_code,
        )
        prefecture_postal_code = ' '.join(
            part for part in perfecture_postal_code_parts if part
        )

        address_parts = (
            candidate.current_street,
            candidate.current_city,
            prefecture_postal_code,
            candidate.get_current_country_display(),
        )
        return ', '.join(part for part in address_parts if part)

    # salary fields
    current_salary_breakdown = serializer_fields.RichTextField(required=False)
    total_annual_salary = serializers.CharField(read_only=True)

    other_desired_benefits = serializer_fields.UniqueChoiceListField(
        choices=m.Candidate.OTHER_DESIRED_BENEFIT_CHOICES, required=False
    )

    owner = serializer_fields.OrgMemberPrimaryKeyRelatedField(allow_null=True)
    note = serializers.SerializerMethodField()

    @require_request
    def get_note(self, candidate):
        """Return CandidateNote text or empty string if not exists."""
        note_data = candidate.get_note(self.context['request'].user.profile.org)
        return serializer_fields.RichTextField().to_representation(note_data)

    class Meta(BasicCandidateSerializer.Meta):
        fields = BasicCandidateSerializer.Meta.fields + (
            'email',
            'secondary_email',
            'phone',
            'secondary_phone',
            'address',
            'tax_equalization',
            'salary_currency',
            'salary',
            'current_salary_variable',
            'current_salary_currency',
            'current_salary',
            'current_salary_breakdown',
            'total_annual_salary',
            'potential_locations',
            'other_desired_benefits',
            'other_desired_benefits_others_detail',
            'expectations_details',
            'notice_period',
            'job_change_urgency',
            'source',
            'source_details',
            'platform',
            'platform_other_details',
            'owner',
            'note',
        )


class RetrieveCandidateMixin(metaclass=serializers.SerializerMetaclass):
    files = serializers.SerializerMethodField()
    import_source = serializers.CharField(read_only=True)

    def get_files(self, obj):
        request = self.context.get('request')
        if not (request and request.user and request.user.profile):
            return []

        serializer = CandidateFileCandidateSerializer(
            obj.files.filter(
                Q(is_shared=True)
                | poly_relation_filter(
                    'org_id', 'org_content_type', request.user.profile.org
                ),
            ),
            context=self.context,
            many=True,
        )
        return serializer.data

    class Meta:
        fields = ('files', 'import_source')


class RetrieveCandidateSerializer(CandidateSerializer, RetrieveCandidateMixin):
    class Meta(CandidateSerializer.Meta):  # noqa
        fields = CandidateSerializer.Meta.fields + RetrieveCandidateMixin.Meta.fields


class BasicRetrieveCandidateSerializer(
    BasicCandidateSerializer, RetrieveCandidateMixin
):
    class Meta(BasicCandidateSerializer.Meta):
        fields = (
            BasicCandidateSerializer.Meta.fields + RetrieveCandidateMixin.Meta.fields
        )


class CreateUpdateCandidateSerializer(CandidateSerializer):
    files = CandidateFileCandidateSerializer(many=True, required=False)
    tags = TagSerializer(many=True, required=False)

    def create(self, validated_data):
        user = self.context['request'].user

        languages = validated_data.pop('languages', [])
        education_details = validated_data.pop('education_details', [])
        experience_details = validated_data.pop('experience_details', [])
        candidate_tags = validated_data.pop('tags', [])
        certifications = validated_data.pop('certifications', [])
        validated_data.pop('files', [])

        try:
            candidate = m.Candidate.objects.create(
                **validated_data, created_by=user, updated_by=user
            )
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)

        for language in languages:
            candidate.languages.add(
                m.Language.objects.get(
                    language=language['language'], level=language['level']
                )
            )

        org_content_type, org_id = get_user_org(user.profile)

        for candidate_tag in candidate_tags:
            tag, created = m.Tag.objects.get_or_create(
                name=candidate_tag['name'].lower(),
                type='candidate',
                org_content_type=org_content_type,
                org_id=org_id,
                defaults={'organization': user.profile.org, 'created_by': user},
            )
            try:
                with transaction.atomic():
                    m.CandidateTag.objects.create(
                        tag=tag, candidate=candidate, attached_by=user
                    )
            except IntegrityError:
                # skip already attached tag
                pass

        for detail in education_details:
            m.EducationDetail.objects.create(candidate=candidate, **detail)

        for detail in experience_details:
            m.ExperienceDetail.objects.create(candidate=candidate, **detail)

        for certification in certifications:
            m.CandidateCertification.objects.create(
                candidate=candidate, **certification
            )

        return candidate

    def update(self, instance, validated_data):
        user = self.context['request'].user

        languages = validated_data.pop('languages', None)
        education_details = validated_data.pop('education_details', None)
        experience_details = validated_data.pop('experience_details', None)
        certifications = validated_data.pop('certifications', None)
        tags = validated_data.pop('tags', None)
        files = validated_data.pop('files', [])

        update_instance_fields(instance, validated_data)
        try:
            instance.updated_by = user
            instance.save()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)

        file_map = dict()
        for detail in files:
            pk = detail.get('id')
            if pk:
                file_map[pk] = detail

        file_records = m.CandidateFile.objects.filter(id__in=file_map)
        for file in file_records:
            detail = file_map[file.id]
            file.is_shared = detail.get('is_shared')
            file.save()

        if languages is not None:
            instance.languages.clear()
            for language in languages:
                instance.languages.add(
                    m.Language.objects.get(
                        language=language['language'], level=language['level']
                    )
                )

        if tags is not None:
            m.CandidateTag.objects.filter(
                Q(candidate=instance) & ~Q(tag__name__in=tags)
            ).delete()

            org_content_type, org_id = get_user_org(user.profile)

            for candidate_tag in tags:
                tag, created = m.Tag.objects.get_or_create(
                    name=candidate_tag['name'].lower(),
                    type='candidate',
                    org_content_type=org_content_type,
                    org_id=org_id,
                    defaults={'organization': user.profile.org, 'created_by': user,},
                )
                try:
                    with transaction.atomic():
                        m.CandidateTag.objects.create(
                            tag=tag, candidate=instance, attached_by=user
                        )
                except IntegrityError:
                    # skip already attached tag
                    pass

        if education_details is not None:
            m.EducationDetail.objects.filter(candidate=instance).delete()
            for detail in education_details:
                m.EducationDetail.objects.create(candidate=instance, **detail)

        if experience_details is not None:
            m.ExperienceDetail.objects.filter(candidate=instance).delete()
            for detail in experience_details:
                m.ExperienceDetail.objects.create(candidate=instance, **detail)

        if certifications is not None:
            m.CandidateCertification.objects.filter(candidate=instance).delete()
            for certification in certifications:
                m.CandidateCertification.objects.create(
                    candidate=instance, **certification
                )

        return instance

    class Meta:  # noqa
        model = m.Candidate
        fields = CandidateSerializer.Meta.fields + ('files',)
        read_only_fields = CandidateSerializer.Meta.read_only_fields
        extra_kwargs = CandidateSerializer.Meta.extra_kwargs


class ValidateCreateUpdateCandidateSerializer(CreateUpdateCandidateSerializer):
    education_details = FormEducationDetailSerializer(many=True, required=False)
    experience_details = FormExperienceDetailSerializer(many=True, required=False)

    owner = serializer_fields.OrgMemberPrimaryKeyRelatedField(
        required=False, allow_null=True
    )

    class Meta(CreateUpdateCandidateSerializer.Meta):
        extra_kwargs = {
            **CreateUpdateCandidateSerializer.Meta.extra_kwargs,
            'first_name': {
                'required': False,
                'allow_blank': False,
                'allow_null': False,
            },
            'last_name': {'required': False, 'allow_blank': False, 'allow_null': False},
        }


class ZohoCandidateSerializer(CandidateSerializer):
    zoho_data = serializers.JSONField(required=False)
    zoho_id = serializers.CharField()
    education_details = EducationDetailSerializer(many=True, required=False)
    experience_details = ExperienceDetailSerializer(many=True, required=False)

    class Meta(CandidateSerializer.Meta):
        fields = tuple(
            set(CandidateSerializer.Meta.fields + ('zoho_data', 'zoho_id'))
            - {'owner', 'current_country', 'current_salary'}
        )
        extra_kwargs = {
            **CandidateSerializer.Meta.extra_kwargs,
            'email': {'allow_blank': True, 'allow_null': True},
        }


class PossibleDuplicateCandidateSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    last_name_kanji = serializers.CharField(required=False, allow_blank=True)
    first_name_kanji = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    secondary_email = serializers.CharField(required=False, allow_blank=True)
    linkedin_url = serializers.CharField(required=False, allow_blank=True)
    job = serializer_fields.JobPrimaryKeyRelatedField(required=False, allow_null=True)
    zoho_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class PossibleDuplicateLinkedInCandidateSerializer(serializers.Serializer):
    class _BasicContactInfo(serializers.Serializer):
        email = serializers.CharField(required=False)
        linked_in = serializers.CharField(required=True)

    name = serializers.CharField(required=False)
    contact_info = _BasicContactInfo(required=False)
    job = serializer_fields.JobPrimaryKeyRelatedField(required=False, allow_null=True)


class CheckIfLinkedinSubmittedToJobSerializer(serializers.Serializer):
    job = serializer_fields.JobPrimaryKeyRelatedField(required=True)
    linkedin_url = serializers.CharField(required=True)


class DuplicatedCandidateSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.CharField()
    is_absolute = serializers.BooleanField(required=False)
    is_submitted = serializers.BooleanField(required=False)
    linkedin_url = serializers.CharField(required=False, allow_blank=True)


class CandidateNoteUpdateSerializer(CandidateSerializer):
    """Serializer for the Candidate note."""

    class Meta(CandidateSerializer.Meta):  # noqa
        fields = ('id', 'note')


class CandidateClientBriefUpdateSerializer(CandidateSerializer):
    """Serializer for the Candidate client_brief."""

    class Meta(CandidateSerializer.Meta):  # noqa
        fields = ('id', 'client_brief')


class ProposalStatusSerializer(serializers.ModelSerializer):
    """ClientProposalStatus serializer."""

    class Meta:  # noqa
        model = m.ProposalStatus
        fields = (
            'id',
            'group',
            'status',
        )


class ProposalSourceSerializer(serializers.Serializer):
    """Serializer for the Organizaiton."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    organization_type = serializers.SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=serializers.CharField)
    def get_organization_type(self, obj):
        """Return organization type if Client or Agency, otherwise None."""
        if isinstance(obj, m.Agency):
            return 'agency'

        if isinstance(obj, m.Client):
            return 'client'


class JobQuestionSerializer(serializers.ModelSerializer):
    """Serializer for the JobQuestion model."""

    class Meta:  # noqa
        model = m.JobQuestion
        fields = ('id', 'text')


class JobAgencyFilteredListSerializer(serializers.ListSerializer):
    """Job Agency list serializer filtered by User permissions."""

    @require_request
    def to_representation(self, data):
        """Filter data depending on User profile."""
        if not hasattr(self.context['request'].user.profile, 'client'):
            data = []

        return super().to_representation(data)


class JobAgencySerializer(serializers.ModelSerializer):
    """Serializer for Job Agencies."""

    class Meta:  # noqa
        model = m.Agency
        fields = ('id', 'name')
        list_serializer_class = JobAgencyFilteredListSerializer


class JobAssigneeFilteredListSerializer(serializers.ListSerializer):
    """Job Assignee list serializer filtered by User permissions."""

    @require_request
    def to_representation(self, data):
        """Filter data depending on User profile."""
        user = self.context['request'].user
        if not hasattr(user.profile, 'agency'):
            data = []
        else:
            data = user.profile.org.members.filter(pk__in=data)
        return super().to_representation(data)


class JobAssigneeSerializer(PublicUserSerializer):
    """Serializer for Job Assignees"""

    class Meta(PublicUserSerializer.Meta):
        list_serializer_class = JobAssigneeFilteredListSerializer


class AssignJobMemberSerializer(serializers.Serializer):
    assignee = serializer_fields.OrgMemberPrimaryKeyRelatedField()

    class Meta:
        fields = ('assignee',)


class FileSerializer(serializers.Serializer):
    """Serializer for the File request."""

    file = serializers.FileField(required=True)


class JobImportLonglistSerializer(serializers.Serializer):
    candidates = serializer_fields.CandidatePrimaryKeyRelatedField(many=True)
    from_job = serializer_fields.JobPrimaryKeyRelatedField()

    class Meta:
        fields = ('candidates', 'from_job')


class UpdateJobFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.JobFile
        fields = ('title',)


class JobFileSerializer(serializers.ModelSerializer):
    """Serializer for the JobFile object."""

    file = serializers.FileField(required=True)
    thumbnail = serializers.FileField(read_only=True)
    job = serializer_fields.JobPrimaryKeyRelatedField(required=True)

    class Meta:  # noqa
        model = m.JobFile
        fields = ('id', 'title', 'file', 'job', 'thumbnail')


class JobOrganizationSerializer(serializers.Serializer):
    """Serializer for Job Organization."""

    type = serializers.CharField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    name_ja = serializers.CharField(read_only=True)
    logo = serializers.FileField(read_only=True)


class JobFunctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Function
        fields = ('id', 'title')


class JobPublicSerializer(serializers.ModelSerializer):
    """Serializer for the Job public objects."""

    organization = JobOrganizationSerializer()
    questions = JobQuestionSerializer(many=True)
    required_languages = LanguageSerializer(many=True)
    files = JobFileSerializer(many=True, read_only=True, source='jobfile_set')
    skills = JobSkillSerializer(source='jobskill_set', many=True, required=False)
    function = JobFunctionSerializer()

    class Meta:  # noqa
        model = m.Job
        fields = (
            'id',
            'organization',
            'title',
            'country',
            'employment_type',
            'questions',
            'status',
            'published',
            'files',
            'location',
            'function',
            # details
            'mission',
            'responsibilities',
            # requirements
            'requirements',
            'skills',
            'required_languages',
            # job conditions
            'salary_currency',
            'salary_from',
            'salary_to',
            'salary_per',
            'bonus_system',
            'probation_period_months',
            'work_location',
            'working_hours',
            'break_time_mins',
            'flexitime_eligibility',
            'telework_eligibility',
            'overtime_conditions',
            'paid_leaves',
            'additional_leaves',
            'social_insurances',
            'commutation_allowance',
            'other_benefits',
        )
        read_only_fields = ('client',)

    def validate_required_languages(self, languages):
        """Check if Job has unique Languages."""
        if len(languages) != len(set(l.get('language') for l in languages)):
            raise serializers.ValidationError(
                _('Should have only one level of each language.')
            )
        return languages


class ExtJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Job
        fields = ('id', 'title')


class AgencyUserExtJobSerializer(serializers.ModelSerializer):
    company = serializers.CharField(required=False, source='client.name')

    class Meta:
        model = m.Job
        fields = ('id', 'title', 'company')


class ExtJobQuerySerializer(serializers.Serializer):
    title = serializers.CharField()


AGENCY_ONLY_JOB_FIELDS = ['contract_type']
CLIENT_ONLY_JOB_FIELDS = ['hiring_process', 'hiring_criteria']


class JobJobAgencyContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.JobAgencyContract
        fields = ('id', 'is_filled_in', 'contract_type', 'signed_at')


class HiringCriterionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = m.HiringCriterion
        fields = ('id', 'name')


class JobInterviewTemplateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    interviewer = OrgMemberSerializer(read_only=True)

    class Meta:  # noqa
        model = m.JobInterviewTemplate
        fields = ('id', 'interview_type', 'order', 'description', 'interviewer')


class CreateUpdateJobInterviewTemplateSerializer(JobInterviewTemplateSerializer):
    interviewer = serializer_fields.OrgMemberPrimaryKeyRelatedField(
        required=False, allow_null=True
    )


class JobSerializer(JobPublicSerializer):
    """Serializer for the Job model."""

    function = JobFunctionSerializer()
    client_name = serializers.CharField(read_only=True, source='client.name')
    hired_count = serializers.IntegerField(read_only=True)

    agencies = JobAgencySerializer(many=True)
    assignees = JobAssigneeSerializer(many=True)

    managers = serializers.SerializerMethodField()
    talent_associates = serializers.SerializerMethodField()

    required_languages = LanguageSerializer(many=True)

    files = JobFileSerializer(many=True, source='jobfile_set')

    candidate_proposed = serializers.SerializerMethodField()
    user_has_access = serializers.SerializerMethodField()
    created_by = OrgMemberSerializer(read_only=True)
    recruiters = OrgMemberSerializer(many=True, read_only=True)
    agency_contracts = JobJobAgencyContractSerializer(many=True, read_only=True)

    hiring_criteria = HiringCriterionSerializer(many=True)
    social_insurances = serializers.MultipleChoiceField(
        choices=m.JobSocialInsurances.get_choices()
    )
    other_benefits = serializers.MultipleChoiceField(
        choices=m.JobOtherBenefits.get_choices()
    )

    proposals_count = serializers.IntegerField(read_only=True)
    proposals_pipeline = serializers.SerializerMethodField()

    interview_templates = JobInterviewTemplateSerializer(many=True)

    class Meta:  # noqa
        model = m.Job
        fields = (
            'client_id',
            'client_name',
            'id',
            'organization',
            # details
            'title',
            'function',
            'employment_type',
            'department',
            'reason_for_opening',
            'target_hiring_date',
            'mission',
            'responsibilities',
            # requirements
            'requirements',
            'educational_level',
            'work_experience',
            'skills',
            'required_languages',
            # job conditions
            'salary_currency',
            'salary_from',
            'salary_to',
            'salary_per',
            'bonus_system',
            'probation_period_months',
            'work_location',
            'working_hours',
            'break_time_mins',
            'flexitime_eligibility',
            'telework_eligibility',
            'overtime_conditions',
            'paid_leaves',
            'additional_leaves',
            'social_insurances',
            'commutation_allowance',
            'other_benefits',
            # hiring process
            'managers',
            'openings_count',
            'status',
            'recruiters',
            'hiring_criteria',
            'questions',
            'interview_templates',
            'hiring_process',
            # attachments
            'files',
            # metadata
            'published_at',
            'closed_at',
            'created_by',
            'created_at',
            'updated_at',
            'published',
            'priority',
            'agencies',
            'assignees',
            'talent_associates',
            'candidate_proposed',
            'user_has_access',
            'hired_count',
            'country',
            'contract_type',
            'location',
            'agency_contracts',
            'proposals_pipeline',
            'proposals_count',
        )
        read_only_fields = fields

    @require_request
    def get_proposals_pipeline(self, obj):
        if not hasattr(obj, 'proposals_count'):
            return

        if obj.organization != self.context['request'].user.org:
            return

        return {
            'associated': obj.proposals_associated_count,
            'pre_screening': obj.proposals_pre_screening_count,
            'submissions': obj.proposals_submissions_count,
            'screening': obj.proposals_screening_count,
            'interviewing': obj.proposals_interviewing_count,
            'offering': obj.proposals_offering_count,
            'hired': obj.proposals_hired_count,
            'rejected': obj.proposals_rejected_count,
        }

    @require_request
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        profile = self.context['request'].user.profile

        if not hasattr(profile, 'agency'):
            representation = filter_out_serializer_fields(
                representation, AGENCY_ONLY_JOB_FIELDS
            )

        if not hasattr(profile, 'client'):
            representation = filter_out_serializer_fields(
                representation, CLIENT_ONLY_JOB_FIELDS
            )

        return representation

    @require_request
    def to_internal_value(self, data):
        profile = self.context['request'].user.profile

        if not hasattr(profile, 'agency'):
            data = filter_out_serializer_fields(data, AGENCY_ONLY_JOB_FIELDS)

        if not hasattr(profile, 'client'):
            representation = filter_out_serializer_fields(data, CLIENT_ONLY_JOB_FIELDS)

        return super().to_internal_value(data)

    @swagger_serializer_method(serializer_or_field=PublicUserSerializer)
    def get_managers(self, obj):
        """Return managers of the Job."""

        should_return_managers = type(self.context['request'].user.profile) in (
            m.ClientAdministrator,
            m.ClientInternalRecruiter,
            m.ClientStandardUser,
            m.Recruiter,
        )

        if not should_return_managers:
            return []

        return PublicUserSerializer(obj.managers, many=True).data

    @swagger_serializer_method(serializer_or_field=PublicUserSerializer)
    @require_request
    def get_talent_associates(self, obj):
        """Return managers of the Job."""
        if type(self.context['request'].user.profile) != m.Recruiter:
            return []

        return PublicUserSerializer(
            obj.organization.members.filter(talentassociate__isnull=False), many=True
        ).data

    @swagger_serializer_method(serializer_or_field=serializers.BooleanField)
    def get_candidate_proposed(self, job):
        """Return True if Candidate was proposed to this Job."""
        candidate = self.context.get('check_candidate_proposed')

        if not candidate:
            return

        return m.Proposal.objects.filter(job=job, candidate=candidate).exists()

    @swagger_serializer_method(serializer_or_field=serializers.BooleanField)
    @require_request
    def get_user_has_access(self, job):
        """Return True if User has access to this Job."""
        if not hasattr(self.context['request'].user.profile, 'client'):
            return  # only for client side

        user = self.context.get('check_user_has_access')

        if not user:
            return

        # TODO: figure out some way to not query db for that?
        return user.profile.apply_jobs_filter(m.Job.objects.filter(id=job.id)).exists()


class JobListSerializer(JobSerializer):
    live_proposals_count = serializers.IntegerField(read_only=True)
    have_access_since = serializers.DateTimeField(required=False)

    class Meta(JobSerializer.Meta):  # noqa
        fields = list(
            (
                set(JobSerializer.Meta.fields)
                | {'live_proposals_count', 'have_access_since'}
            )
            - {
                'agencies',
                'assignees',
                'required_languages',
                'hired_count',
                'files',
                'function',
                'questions',
                'candidate_requirements',
                'interview_templates',
            }
        )
        read_only_fields = fields


class CreateUpdateJobQuestionSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating JobQuestion objects."""

    id = serializers.IntegerField(label='ID', required=False)

    class Meta:  # noqa
        model = m.JobQuestion
        fields = ('id', 'text')


class ManagerAssignRemoveFromJobSerializer(serializers.Serializer):
    """Serializer for managing Job Managers."""

    user = serializer_fields.ManagersPrimaryKeyRelatedField(
        required=True, write_only=True
    )
    job = serializers.PrimaryKeyRelatedField(
        queryset=m.Job.objects, required=True, write_only=True
    )

    class Meta:  # noqa
        fields = ('user', 'job')

    def validate(self, data):
        """Check if Job and User are from the same Client."""
        if data['job'].organization != data['user'].profile.org:
            raise serializers.ValidationError(
                _('User and Job should belong to the same Organization.')
            )

        return data


class ManagerInviteSerializer(serializers.ModelSerializer):
    """Serializer to invite Hiring Managers."""

    def create(self, validated_data):
        user = m.User.objects.create(**validated_data, password=uuid.uuid4())
        return user

    class Meta:
        model = m.User
        fields = ('first_name', 'last_name', 'email')
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }


class CreateUpdateJobSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Job."""

    function = serializers.PrimaryKeyRelatedField(
        queryset=m.Function.objects.all(), required=False, allow_null=True
    )
    client = serializer_fields.JobClientRelatedField(required=False)

    responsibilities = serializer_fields.RichTextField()
    requirements = serializer_fields.RichTextField()
    questions = CreateUpdateJobQuestionSerializer(many=True)
    required_languages = LanguageSerializer(many=True)

    agencies = serializers.PrimaryKeyRelatedField(
        many=True, queryset=m.Agency.objects.all()
    )
    managers = serializer_fields.ManagersPrimaryKeyRelatedField(many=True)

    recruiters = serializer_fields.OrgMemberPrimaryKeyRelatedField(many=True)
    created_by = OrgMemberSerializer(read_only=True)
    skills = TagSerializer(many=True, required=False)
    social_insurances = serializer_fields.UniqueChoiceListField(
        choices=m.JobSocialInsurances.get_choices(), required=False
    )
    other_benefits = serializer_fields.UniqueChoiceListField(
        choices=m.JobOtherBenefits.get_choices(), required=False
    )

    interview_templates = CreateUpdateJobInterviewTemplateSerializer(many=True)
    hiring_criteria = HiringCriterionSerializer(many=True, required=False)
    openings_count = serializers.IntegerField(min_value=0, required=False)

    class Meta:  # noqa
        model = m.Job
        fields = (
            'id',
            'title',
            'function',
            'employment_type',
            'department',
            'reason_for_opening',
            'target_hiring_date',
            'mission',
            'responsibilities',
            # requirements
            'requirements',
            'educational_level',
            'work_experience',
            'skills',
            'required_languages',
            # job conditions
            'salary_currency',
            'salary_from',
            'salary_to',
            'salary_per',
            'bonus_system',
            'probation_period_months',
            'work_location',
            'working_hours',
            'break_time_mins',
            'flexitime_eligibility',
            'telework_eligibility',
            'overtime_conditions',
            'paid_leaves',
            'additional_leaves',
            'social_insurances',
            'commutation_allowance',
            'other_benefits',
            # hiring process
            'managers',
            'openings_count',
            'status',
            'recruiters',
            'hiring_criteria',
            'questions',
            'interview_templates',
            'hiring_process',
            # attachments
            # metadata
            'published_at',
            'closed_at',
            'created_by',
            'created_at',
            'updated_at',
            'published',
            'agencies',
            'client',
            'country',
        )
        read_only_fields = ('created_by',)
        extra_kwargs = {
            'required_languages': {'required': True},
            'salary_to': {
                'error_messages': {
                    'less_than_salary_from': _('Can\'t be less than Salary From')
                }
            },
            'openings_count': {
                'error_messages': {
                    'not_enough_openings': _(
                        'Can\'t be less than the number of hired candidates'
                    ),
                    'no_permission_to_open': _(
                        'You have no permission to change number of openings'
                    ),
                }
            },
            'status': {
                'error_messages': {
                    'not_enough_openings': _(
                        'Can\'t set job as "Open". Job should have more openings than hired candidates'
                    ),
                    'no_permission_to_open': _(
                        'You have no permission to set this job as "Open"'
                    ),
                    'unfilled_openings': _(
                        'Can\'t set job as "Filled". Job has unfilled openings'
                    ),
                }
            },
        }

    @require_request
    def is_user_allowed_to_open(self):
        if not self.instance:
            return True
        user = self.context['request'].user
        have_global_access = isinstance(
            user.profile,
            (
                m.ClientAdministrator,
                m.ClientInternalRecruiter,
                m.AgencyAdministrator,
                m.AgencyManager,
            ),
        )
        return have_global_access or self.instance.owner == user

    def validate_salary_to(self, salary_to):
        salary_from = self.initial_data.get('salary_from')

        try:
            salary_from = Decimal(salary_from)
        except (TypeError, decimal.InvalidOperation):
            return salary_to

        not_valid = (
            salary_from is not None
            and salary_to is not None
            and salary_from > salary_to
        )

        if not_valid:
            self.fields['salary_to'].fail('less_than_salary_from')

        return salary_to

    def validate_openings_count(self, openings_count):
        if openings_count is None or not self.instance:
            return openings_count

        hired_count = self.instance.get_hired_count()
        if openings_count < hired_count:
            self.fields['openings_count'].fail('not_enough_openings')

        if (
            openings_count != self.instance.openings_count
            and not self.is_user_allowed_to_open()
        ):
            self.fields['openings_count'].fail('no_permission_to_open')

        return openings_count

    def add_error(self, errors, field, error_type):
        if field not in errors:
            errors[field] = []
        errors[field].append(self.fields[field].error_messages[error_type])

    @require_request
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        status = validated_data.get('status')
        openings_count = validated_data.get('openings_count', 0)

        errors = {}
        hired_count = getattr(self.instance, 'hired_count', 0)
        unfilled_openings = openings_count - hired_count
        if status == m.JobStatus.OPEN.key:
            if unfilled_openings <= 0:
                self.add_error(errors, 'status', 'not_enough_openings')

            if not self.is_user_allowed_to_open():
                self.add_error(errors, 'status', 'no_permission_to_open')

        elif status == m.JobStatus.FILLED.key and unfilled_openings > 0:
            self.add_error(errors, 'status', 'unfilled_openings')

        if len(errors):
            raise ValidationError(errors)

        return validated_data

    @require_request
    def create(self, validated_data):
        languages = validated_data.pop('required_languages', [])
        questions = validated_data.pop('questions', [])
        agencies = validated_data.pop('agencies')
        managers = validated_data.pop('managers')
        recruiters = validated_data.pop('recruiters')
        skills = validated_data.pop('skills', [])
        interview_templates = validated_data.pop('interview_templates', [])
        hiring_criteria = validated_data.pop('hiring_criteria', [])

        user = getattr(self.context.get('request'), 'user', None)
        org = user.profile.org

        if 'client' not in validated_data:
            if isinstance(org, m.Client):
                validated_data['client'] = org
            else:
                errors = dict()
                self.add_error(errors, 'client', 'required')
                raise serializers.ValidationError(errors)

        job = m.Job(**validated_data)
        job.organization = org
        job.owner = user

        published = validated_data.get('published')
        job.published_at = now() if published else None

        job.save()

        job.set_agencies(agencies)
        job.set_managers(managers)
        job.set_recruiters(recruiters)

        if isinstance(org, m.Agency):
            job.assign_member(user)
            if org not in job.agencies.all():
                job.assign_agency(org)

        for language in languages:
            job.required_languages.add(
                m.Language.objects.get(
                    language=language['language'], level=language['level']
                )
            )

        for question_data in questions:
            m.JobQuestion.objects.create(job=job, **question_data)

        org_content_type, org_id = get_user_org(user.profile)
        for skill in skills:
            tag, created = m.Tag.objects.get_or_create(
                name=skill['name'].lower(),
                type='skill',
                org_content_type=org_content_type,
                org_id=org_id,
                defaults={'organization': user.profile.org, 'created_by': user},
            )
            try:
                with transaction.atomic():
                    m.JobSkill.objects.create(tag=tag, job=job, attached_by=user)
            except IntegrityError:
                # skip already attached tag
                pass

        for interview_template_data in interview_templates:
            interview_template = m.JobInterviewTemplate.objects.create(
                job=job, **interview_template_data
            )

        for hiring_criterion_data in hiring_criteria:
            hiring_criterion = m.HiringCriterion.objects.create(
                job=job, **hiring_criterion_data
            )

        return job

    @require_request
    def update(self, instance, validated_data):
        questions = validated_data.pop('questions', [])
        languages = validated_data.pop('required_languages', [])
        managers = validated_data.pop('managers', None)
        recruiters = validated_data.pop('recruiters', None)
        agencies = validated_data.pop('agencies', None)
        skills = validated_data.pop('skills', None)
        interview_templates = validated_data.pop('interview_templates', [])
        hiring_criteria = validated_data.pop('hiring_criteria', [])

        user = self.context['request'].user

        if agencies is not None and not isinstance(user.profile.org, m.Agency):
            instance.set_agencies(agencies)

        if managers is not None:
            instance.set_managers(managers)

        if recruiters is not None:
            instance.set_recruiters(recruiters)

        update_instance_fields(instance, validated_data)
        instance.save()

        instance.required_languages.clear()
        for language in languages:
            instance.required_languages.add(
                m.Language.objects.get(
                    language=language['language'], level=language['level']
                )
            )

        m.JobQuestion.objects.filter(job=instance).exclude(
            id__in=[i['id'] for i in questions if i.get('id')]
        ).delete()

        for question_data in questions:
            question_id = question_data.pop('id', None)

            m.JobQuestion.objects.update_or_create(
                job=instance, id=question_id, defaults=question_data
            )

        org_content_type, org_id = get_user_org(user.profile)
        if skills is not None:
            m.JobSkill.objects.filter(
                Q(job=instance) & ~Q(tag__name__in=skills)
            ).delete()

            for skill in skills:
                tag, created = m.Tag.objects.get_or_create(
                    name=skill['name'].lower(),
                    type='skill',
                    org_content_type=org_content_type,
                    org_id=org_id,
                    defaults={'organization': user.profile.org, 'created_by': user},
                )
                try:
                    with transaction.atomic():
                        m.JobSkill.objects.create(
                            tag=tag, job=instance, attached_by=user
                        )
                except IntegrityError:
                    # skip already attached tag
                    pass

        m.JobInterviewTemplate.objects.filter(job=instance).exclude(
            id__in=[i['id'] for i in interview_templates if i.get('id')]
        ).delete()
        for interview_template_data in interview_templates:
            interview_template_id = interview_template_data.pop('id', None)
            interview_template = m.JobInterviewTemplate.objects.update_or_create(
                job=instance,
                id=interview_template_id,
                defaults=interview_template_data,
            )

        m.HiringCriterion.objects.filter(job=instance).exclude(
            id__in=[i['id'] for i in hiring_criteria if i.get('id')]
        ).delete()
        for hiring_criterion_data in hiring_criteria:
            hiring_criterion_id = hiring_criterion_data.pop('id', None)
            hiring_criterion = m.HiringCriterion.objects.update_or_create(
                job=instance, id=hiring_criterion_id, defaults=hiring_criterion_data
            )

        return instance


class JobUpdateResponseSerializer(CreateUpdateJobSerializer):
    are_postings_outdated = serializers.BooleanField(read_only=True)

    class Meta(CreateUpdateJobSerializer.Meta):
        fields = CreateUpdateJobSerializer.Meta.fields + ('are_postings_outdated',)


class JobComparisonSerializer(CreateUpdateJobSerializer):
    agencies = serializers.SerializerMethodField

    def get_agencies(self, instance):
        return {
            contract.agency_id
            for contract in instance.agency_contracts.filter(is_active=True)
        }


class ProposalStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:  # noqa
        model = m.ProposalStatusHistory
        fields = (
            'status',
            'changed_at',
        )


class ProposalJobSerializer(serializers.ModelSerializer):

    org_type = serializers.CharField(source='organization.type', read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)
    managers = PublicUserSerializer(many=True, read_only=True)

    class Meta:  # noqa
        model = m.Job
        fields = (
            'id',
            'org_id',
            'org_type',
            'client_id',
            'client_name',
            'title',
            'priority',
            'managers',
        )
        read_only_fields = fields


class ProposalCandidateSerializerMixin(metaclass=serializers.SerializerMetaclass):
    @require_request
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        user = self.context['request'].user
        if user.profile.org != instance.organization:
            allowed_fields = representation.keys() - CANDIDATE_FLAGS

            return {field: representation[field] for field in allowed_fields}

        return representation

    class Meta:
        excluded = ('internal_status',)


class ProposalCandidateSerializer(
    CandidateSerializer, ProposalCandidateSerializerMixin
):
    class Meta(CandidateSerializer.Meta):
        fields = tuple(
            set(CandidateSerializer.Meta.fields)
            - set(ProposalCandidateSerializerMixin.Meta.excluded)
        )


class BasicProposalCandidateSerializer(
    BasicCandidateSerializer, ProposalCandidateSerializerMixin
):
    class Meta(CandidateSerializer.Meta):
        fields = tuple(
            set(BasicCandidateSerializer.Meta.fields)
            - set(ProposalCandidateSerializerMixin.Meta.excluded)
        )


class HiringCriterionAssessmentSerializer(serializers.ModelSerializer):
    hiring_criterion_id = serializers.IntegerField(source='hiring_criterion.id')
    name = serializers.CharField(source='hiring_criterion.name', read_only=True)

    class Meta:  # noqa
        model = m.HiringCriterionAssessment
        fields = ('id', 'hiring_criterion_id', 'name', 'rating')


class ProposalInterviewAssessmentSerializer(serializers.ModelSerializer):
    hiring_criteria_assessment = HiringCriterionAssessmentSerializer(
        source='hiringcriterionassessment_set', many=True, required=False
    )
    decision_display = serializers.CharField(
        source='get_decision_display', read_only=True
    )

    class Meta:  # noqa
        model = m.ProposalInterviewAssessment
        fields = (
            'id',
            'hiring_criteria_assessment',
            'decision',
            'decision_display',
            'notes',
        )

    def create(self, validated_data):
        interview = self.context['interview']
        hiring_criteria_assessment = []
        hiring_criteria_assessment = validated_data.pop(
            'hiringcriterionassessment_set', []
        )
        instance, _ = m.ProposalInterviewAssessment.objects.update_or_create(
            interview=interview, defaults=validated_data
        )
        instance.hiring_criteria.clear()
        for hiring_criterion_assessment in hiring_criteria_assessment:
            rating = hiring_criterion_assessment.pop('rating', None)
            try:
                hiring_criterion = m.HiringCriterion.objects.get(
                    id=hiring_criterion_assessment['hiring_criterion']['id']
                )
            except m.HiringCriterion.DoesNotExist:
                raise ValidationError(
                    _(f'Invalid Hiring Criterion: {hiring_criterion_assessment}')
                )
            m.HiringCriterionAssessment.objects.update_or_create(
                assessment=instance,
                hiring_criterion=hiring_criterion,
                defaults={'rating': rating},
            )
        return instance


class ProposalInterviewScheduleTimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ProposalInterviewScheduleTimeSlot
        fields = ('id', 'start_at', 'end_at')


class ProposalInterviewScheduleSerializer(serializers.ModelSerializer):
    timeslots = ProposalInterviewScheduleTimeSlotSerializer(
        many=True, allow_null=False, required=False
    )

    class Meta:
        model = m.ProposalInterviewSchedule
        fields = (
            'id',
            'interview',
            'timeslots',
            'creator_timezone',
        )


class ProposalInterviewSerializer(serializers.ModelSerializer):
    class _InvitedUser(serializers.ModelSerializer):
        name = serializers.CharField(required=False)

        class Meta:
            model = m.ProposalInterviewInvite
            read_only_fields = (
                'id',
                'name',
            )
            fields = (
                *read_only_fields,
                'user',
                'email',
            )

    invited = _InvitedUser(many=True, required=False)
    interviewer = OrgMemberSerializer(read_only=True)
    assessment = ProposalInterviewAssessmentSerializer(read_only=True)
    schedules = ProposalInterviewScheduleSerializer(many=True, read_only=True)

    timeslots = ProposalInterviewScheduleTimeSlotSerializer(
        source='current_schedule.timeslots', many=True, required=False
    )
    status = serializers.ChoiceField(
        source='current_schedule.status',
        required=False,
        choices=m.ProposalInterviewSchedule.Status.choices,
    )
    status_display = serializers.CharField(
        source='current_schedule.get_status_display', required=False
    )
    start_at = serializers.DateTimeField(
        source='current_schedule.scheduled_timeslot.start_at',
        default=None,
        required=False,
        allow_null=True,
    )
    end_at = serializers.DateTimeField(
        source='current_schedule.scheduled_timeslot.end_at',
        default=None,
        required=False,
        allow_null=True,
    )
    notes = serializer_fields.RichTextField(
        source='current_schedule.notes', required=False
    )
    pre_schedule_msg = serializer_fields.RichTextField(
        source='current_schedule.pre_schedule_msg', required=False
    )
    scheduling_type = serializers.CharField(
        source='current_schedule.scheduling_type', required=False
    )

    def to_representation(self, instance):
        output = super().to_representation(instance)

        # If current schedule is cancelled it would show date as though it's already scheduled. We want to avoid that
        canceled_statuses = [
            m.ProposalInterviewSchedule.Status.CANCELED,
            m.ProposalInterviewSchedule.Status.REJECTED,
        ]
        if output['status'] in canceled_statuses:
            output['start_at'] = None
            output['end_at'] = None

        return output

    class Meta:
        model = m.ProposalInterview
        fields = (
            'id',
            'status',
            'status_display',
            'proposal',
            'start_at',
            'end_at',
            'invited',
            'timeslots',
            'schedules',
            'description',
            'notes',
            'is_current_interview',
            'interviewer',
            'interview_type',
            'order',
            'assessment',
            'pre_schedule_msg',
            'scheduling_type',
        )


class CreateUpdateProposalInterviewSerializer(ProposalInterviewSerializer):
    custom_error_messages = {
        'non_member': _(
            'Users you\'ve selected are not members'
            ' of organisation which submitted the candidate'
        ),
    }
    proposal = serializer_fields.ProposalPrimaryKeyRelatedField(
        required=False,
        error_messages={
            'not_org_job': _(
                'Job proposal is assigned to belongs to other organisation'
            )
        },
    )
    interviewer = serializer_fields.OrgMemberPrimaryKeyRelatedField(
        required=False, allow_null=True
    )
    to_order = serializers.IntegerField(
        min_value=1,
        write_only=True,
        required=False,
        allow_null=True,
        error_messages={'too_big': _('Order exceeds number of interviews')},
    )

    class Meta:
        model = m.ProposalInterview
        fields = ProposalInterviewSerializer.Meta.fields + ('to_order',)
        validators = [
            ModeRequireFieldsValidator(
                mode_field='scheduling_type',
                required_fields_by_mode={
                    m.ProposalInterviewSchedule.SchedulingType.INTERVIEW_PROPOSAL: [
                        'interviewer',
                        'timeslots',
                    ],
                    m.ProposalInterviewSchedule.SchedulingType.SIMPLE_SCHEDULING: [
                        'interviewer',
                        'start_at',
                        'end_at',
                    ],
                    m.ProposalInterviewSchedule.SchedulingType.PAST_SCHEDULING: [
                        'start_at',
                        'end_at',
                    ],
                },
            ),
            ModeRequireFieldsValidator(
                mode_field='status',
                required_fields_by_mode={
                    status: ['scheduling_type']
                    for status in (
                        m.ProposalInterviewSchedule.Status.PENDING_CONFIRMATION,
                        m.ProposalInterviewSchedule.Status.SCHEDULED,
                    )
                },
                message=_('This field is required while scheduling'),
            ),
            ModeChoicesValidator(
                field='status',
                mode_field='scheduling_type',
                mode_choices={
                    m.ProposalInterviewSchedule.SchedulingType.INTERVIEW_PROPOSAL: [
                        m.ProposalInterviewSchedule.Status.PENDING_CONFIRMATION
                    ],
                    m.ProposalInterviewSchedule.SchedulingType.SIMPLE_SCHEDULING: [
                        m.ProposalInterviewSchedule.Status.SCHEDULED
                    ],
                    m.ProposalInterviewSchedule.SchedulingType.PAST_SCHEDULING: [
                        m.ProposalInterviewSchedule.Status.SCHEDULED
                    ],
                },
                mode_is_required=False,
            ),
        ]

    def validate_timeslots(self, timeslots):
        if timeslots is not None and len(timeslots) == 0:
            raise ValidationError(
                {'timeslots': _('Must specify at least one timeslot')}
            )
        return timeslots

    def validate_proposal(self, proposal):
        if not self.instance and not proposal:
            self.fields['proposal'].fail('required')

        request = self.context.get('request')
        user_org = request.user.profile.org if request else None

        if proposal.job.organization != user_org:
            self.fields['proposal'].fail('not_org_job')

        return proposal

    def validate_to_order(self, to_order):
        if to_order and to_order > self.Meta.model.objects.get_max_order():
            self.fields['to_order'].fail('too_big')

        return to_order

    def validate(self, attrs):
        to_order = attrs.pop('to_order', None)
        data = super().validate(attrs)
        data['to_order'] = to_order
        proposal = data.get('proposal')
        errors = OrderedDict()

        if proposal is None:
            try:
                proposal = self.validate_proposal(
                    getattr(self.instance, 'proposal', None)
                )
            except serializers.ValidationError as error:
                raise ValidationError({'proposal': error.detail})

        invited = data.get('invited', None)
        if invited:
            members_set = set(proposal.candidate.organization.members.all())

            invited_users_set = set()
            for invitation in invited:
                if 'user' in invitation:
                    invited_users_set.add(invitation['user'])

            if not members_set.issuperset(invited_users_set):
                errors['invited'] = self.custom_error_messages['non_member']

        if errors:
            raise ValidationError(errors)
        return data

    @require_request
    def create(self, validated_data):
        model = self.Meta.model
        invited = validated_data.pop('invited', [])

        current_schedule_data = validated_data.pop('current_schedule', None)
        timeslots = current_schedule_data.pop('timeslots', None)
        to_order = validated_data.pop('to_order', None)

        instance = model.objects.create(
            created_by=self.context['request'].user, **validated_data
        )
        if invited:
            for invitation_data in invited:
                m.ProposalInterviewInvite.objects.create(
                    interview=instance, **invitation_data,
                )
        if timeslots:
            schedule = m.ProposalInterviewSchedule.objects.create(
                interview=instance, status=current_schedule_data['status'],
            )
            for timeslot_data in timeslots:
                m.ProposalInterviewScheduleTimeSlot.objects.create(
                    schedule=schedule, **timeslot_data
                )
            instance.current_schedule = schedule
            instance.save()
        if to_order:
            instance.to(to_order)
        instance.proposal.get_or_set_current_interview_maybe()
        return instance

    @staticmethod
    def _update_timeslots(interview, timeslot_data_list):
        interview.scheduled_timeslot = None
        current_schedule = interview.current_schedule

        current_schedule.timeslots.all().delete()
        for timeslot_data in timeslot_data_list:
            m.ProposalInterviewScheduleTimeSlot.objects.create(
                schedule=current_schedule, **timeslot_data
            )

    @staticmethod
    def _update_scheduled_timeslot(schedule, timeslot_data):
        start_at = timeslot_data.get('start_at')
        end_at = timeslot_data.get('end_at')

        if not (start_at and end_at):
            return

        timeslot, _ = m.ProposalInterviewScheduleTimeSlot.objects.get_or_create(
            schedule=schedule, **timeslot_data
        )
        schedule.scheduled_timeslot = timeslot

    @classmethod
    def _update_current_schedule(cls, interview, current_schedule_data):
        schedule_statuses = m.ProposalInterviewSchedule.Status
        status = current_schedule_data.get('status', None)

        current_schedule = interview.current_schedule

        should_create_new_schedule = (
            status is not None
            and status != current_schedule.status
            and current_schedule.status
            in [schedule_statuses.CANCELED, schedule_statuses.REJECTED]
        )

        if should_create_new_schedule:
            current_schedule = m.ProposalInterviewSchedule.objects.create(
                interview=interview
            )
            interview.current_schedule = current_schedule

        timeslots = current_schedule_data.pop('timeslots', [])
        if len(timeslots) > 0:
            cls._update_timeslots(interview, timeslots)

        scheduled_timeslot_data = current_schedule_data.pop('scheduled_timeslot', None)
        if scheduled_timeslot_data:
            cls._update_scheduled_timeslot(current_schedule, scheduled_timeslot_data)

        for field, value in current_schedule_data.items():
            setattr(current_schedule, field, value)

        current_schedule.save()

    @staticmethod
    def _update_invited(instance, invited):
        all_invited = InvitedSetsFromDict(invited)
        # we don't delete all invites because we need to track then new are added
        instance.invited.exclude(
            Q(email__in=all_invited.emails) | Q(user__in=all_invited.users)
        ).delete()

        old_invited = InvitedSetsFromInstance(instance.invited.all())
        new_invited = all_invited - old_invited

        for invitation_data in new_invited.contained(invited):
            m.ProposalInterviewInvite.objects.create(
                interview=instance, **invitation_data,
            )

    def update(self, instance, validated_data):
        """
        depending on the status passed, this may affect more than one ProposalInterviewSchedule objects
        """

        invited = validated_data.pop('invited', None)
        if invited:
            self._update_invited(instance, invited)

        current_schedule_data = validated_data.pop('current_schedule', None)
        if current_schedule_data and instance.current_schedule:
            self._update_current_schedule(instance, current_schedule_data)

        to_order = validated_data.pop('to_order', None)
        if to_order:
            instance.to(to_order)

        return super().update(instance, validated_data)


class ProposalInterviewPublicSerializer(ProposalInterviewSerializer):
    class _JobSerializer(serializers.ModelSerializer):
        client_name = serializers.CharField(source='client.name', read_only=True)
        function = JobFunctionSerializer(read_only=True)
        employment_type_display = serializers.CharField(
            source='get_employment_type_display', read_only=True
        )

        class Meta:  # noqa
            model = m.Job
            fields = (
                'id',
                'title',
                'client_name',
                'function',
                'employment_type',
                'employment_type_display',
                'work_location',
                'country',
                'salary_currency',
                'salary_from',
                'salary_to',
                'salary_per',
            )
            read_only_fields = fields

    custom_error_messages = {
        'no_creation': _('Interview creation is not allowed'),
        'timeslot_chosen': _('Timeslot was already selected'),
    }

    job = _JobSerializer(source='proposal.job', read_only=True)
    candidate_name = serializers.CharField(
        source='proposal.candidate.name', read_only=True
    )
    pre_schedule_msg = serializer_fields.RichTextField(
        source='current_schedule.pre_schedule_msg', read_only=True,
    )
    chosen_timeslot = serializers.PrimaryKeyRelatedField(
        required=False,
        write_only=True,
        queryset=m.ProposalInterviewScheduleTimeSlot.objects.none(),
    )

    is_rejected = serializers.BooleanField(write_only=True, required=False)
    inviter = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['chosen_timeslot'].get_queryset = self.get_chosen_timeslot_queryset

    def get_chosen_timeslot_queryset(self):
        if self.instance:
            return self.instance.current_schedule.timeslots.all()
        return self.queryset

    def get_inviter(self, obj):
        if obj.created_by.profile and obj.created_by.profile.org:
            return obj.created_by.profile.org.name
        else:
            return obj.created_by.full_name

    def validate(self, data):
        is_timeslot_chosen = self.instance.start_at if self.instance else None
        if 'chosen_timeslot' in data and is_timeslot_chosen:
            raise serializers.ValidationError(
                {'chosen_timeslot': self.custom_error_messages['timeslot_chosen']}
            )

        return super().validate(data)

    def create(self, *args, **kwargs):
        raise serializers.ValidationError(self.custom_error_messages['no_creation'])

    @require_request
    def update(self, instance, validated_data):
        timeslot = validated_data.pop('chosen_timeslot', None)
        is_rejected = validated_data.pop('is_rejected', None)
        validated_data.pop('timeslots', None)
        validated_data.pop('current_schedule', None)

        current_schedule = instance.current_schedule
        if is_rejected:
            current_schedule.status = m.ProposalInterviewSchedule.Status.REJECTED
        elif timeslot:
            if current_schedule.scheduled_timeslot:
                raise serializers.ValidationError(
                    self.custom_error_messages['timeslot_chosen']
                )

            current_schedule.scheduled_timeslot = timeslot
            current_schedule.status = m.ProposalInterviewSchedule.Status.SCHEDULED
        current_schedule.save()

        return super().update(instance, validated_data)

    class Meta:
        model = m.ProposalInterview
        read_only_fields = (
            'status',
            'start_at',
            'end_at',
            'timeslots',
            'inviter',
            'notes',
            'job',
            'candidate_name',
            'pre_schedule_msg',
        )
        fields = (*read_only_fields, 'chosen_timeslot', 'is_rejected')
        extra_kwargs = {'timeslots': {'required': False}}


class BasicProposalSerializer(serializers.ModelSerializer):
    """Proposal serializer with limited canidate access."""

    job = ProposalJobSerializer(read_only=True)
    candidate = BasicProposalCandidateSerializer(read_only=True)

    source = ProposalSourceSerializer(read_only=True)
    client_name = serializers.CharField(source='job.client.name')

    status = ProposalStatusSerializer()
    status_history = ProposalStatusHistorySerializer(many=True)
    sub_stage = serializers.CharField(read_only=True)
    stage = serializers.CharField(source='status.stage')

    created_by = PublicUserSerializer(read_only=True)
    moved_by = PublicUserSerializer(read_only=True)
    status_last_updated_by = PublicUserSerializer(read_only=True)

    on_hold = serializers.SerializerMethodField(read_only=True)
    last_activity_at = serializers.DateTimeField(read_only=True)

    decline_reasons = ReasonDeclineCandidateOptionSerializer(many=True, read_only=True)
    reasons_not_interested = ReasonNotInterestedOptionSerializer(
        many=True, read_only=True
    )

    own = serializers.SerializerMethodField(read_only=True)

    fee_id = serializers.IntegerField(read_only=True)

    # annotated fields (requested with "extra_fields" query param)
    hired_at = serializers.DateTimeField(read_only=True)
    job_created_by_name = serializers.CharField(read_only=True)
    can_edit_placement = serializers.BooleanField(read_only=True)
    can_see_placement = serializers.BooleanField(read_only=True)
    can_create_placement = serializers.BooleanField(read_only=True)
    current_interview = ProposalInterviewSerializer(read_only=True)

    @require_request
    def get_candidate(self, candidate):
        user = self.context['request'].user
        if user.profile.org == candidate.organization:
            return self.candidate.to_representation(candidate)

        return ProposalCandidateSerializer(instance=candidate).data

    @swagger_serializer_method(serializer_or_field=serializers.BooleanField)
    @require_request
    def get_on_hold(self, instance):
        """
        :return: Proposal's availability depends on related Job availability (Boolean)
        """
        user = self.context['request'].user

        if not hasattr(user.profile, 'agency'):
            return

        return instance.job not in user.profile.apply_jobs_filter(m.Job.objects.all())

    @require_request
    def get_own(self, proposal):
        user = self.context['request'].user
        created_by_profile = getattr(proposal.created_by, 'profile', None)
        return created_by_profile and user.profile.org == created_by_profile.org

    class Meta:  # noqa
        model = m.Proposal
        fields = (
            'id',
            'job',
            'candidate',
            'source',
            'status',
            'status_history',
            'created_by',
            'created_at',
            'updated_at',
            'moved_by',
            'status_last_updated_by',
            'client_name',
            'on_hold',
            'decline_reasons',
            'reasons_not_interested',
            'own',
            'sub_stage',
            'stage',
            'is_rejected',
            'suitability',
            'reason_not_interested_description',
            'reason_declined_description',
            'is_direct_application',
            'current_interview',
            # annotation
            'last_activity_at',
            'hired_at',
            'job_created_by_name',
            'fee_id',
            'can_edit_placement',
            'can_see_placement',
            'can_create_placement',
        )
        read_only_fields = fields


class ProposalSerializer(BasicProposalSerializer):
    """Proposal serializer with complete candidate access"""

    candidate = ProposalCandidateSerializer(read_only=True)


class QuickActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=QuickActionVerb.get_choices())
    label_en = serializers.CharField()
    label_ja = serializers.CharField()
    to_status = serializers.DictField(default=dict)
    label = serializers.SerializerMethodField()

    def get_label(self, data):
        lang = get_language().lower()
        label = data.get(f'label_{lang}') or data['label_en']
        return label


class ProposalCommentSerializer(serializers.ModelSerializer):
    """Proposal comment serializer."""

    author = serializers.SerializerMethodField()

    class Meta:  # noqa
        model = m.ProposalComment
        fields = ('id', 'proposal', 'author', 'text', 'created_at', 'system')
        read_only_fields = ('id', 'author', 'created_at', 'system')

    @require_request
    def get_author(self, comment):
        user = self.context['request'].user
        if comment.author is None:
            return _('Anonymous User')
        if comment.author.profile is None:
            return ''

        if user.profile.org == comment.author.profile.org or (
            comment.public and not comment.system
        ):
            return PublicUserSerializer(comment.author).data

        return comment.author.profile.org.name


class CreateProposalCommentSerializer(serializers.ModelSerializer):
    """Serializer for creating Proposal comments."""

    proposal = serializer_fields.ProposalPrimaryKeyRelatedField()

    class Meta:  # noqa
        model = m.ProposalComment
        fields = ('id', 'proposal', 'text', 'public')
        read_only_fields = ('id',)

    @require_request
    def create(self, validated_data):
        """Add user for the context to the created object."""
        return m.ProposalComment.objects.create(
            **validated_data,
            author=self.context['request'].user,
            proposal_status=validated_data['proposal'].status,
        )


class ProposalQuestionSerializer(serializers.ModelSerializer):
    answer = serializer_fields.RichTextField()

    class Meta:  # noqa
        model = m.ProposalQuestion
        fields = ('id', 'text', 'answer')
        read_only_fields = (
            'id',
            'text',
        )


class CandidateForProposalRetrieveMixin(metaclass=serializers.SerializerMetaclass):
    def get_files(self, obj):
        request = self.context.get('request')
        if not (request and request.user and request.user.profile):
            return []

        serializer = CandidateFileCandidateSerializer(
            obj.files.filter(is_shared=True), context=self.context, many=True
        )
        return serializer.data

    class Meta:  # noqa
        fields = ('files',)


class RetrieveProposalMixin(metaclass=serializers.SerializerMetaclass):
    quick_actions = QuickActionSerializer(
        source='filtered_quick_actions', many=True, read_only=True
    )
    questions = ProposalQuestionSerializer(many=True, read_only=True)
    interviews = ProposalInterviewSerializer(many=True, read_only=True)
    comments = ProposalCommentSerializer(
        source='proposalcomment_set', many=True, read_only=True
    )

    class Meta:  # noqa
        fields = (
            'comments',
            'interviews',
            'questions',
            'quick_actions',
        )


class BasicRetrieveProposalSerializer(BasicProposalSerializer, RetrieveProposalMixin):
    class _ProposalSerializer(
        BasicRetrieveCandidateSerializer, CandidateForProposalRetrieveMixin
    ):
        class Meta(BasicCandidateSerializer.Meta):
            fields = (
                BasicCandidateSerializer.Meta.fields
                + CandidateForProposalRetrieveMixin.Meta.fields
            )
            read_only_fields = fields

    candidate = _ProposalSerializer(read_only=True)

    class Meta(BasicProposalSerializer.Meta):
        fields = BasicProposalSerializer.Meta.fields + RetrieveProposalMixin.Meta.fields


class RetrieveProposalSerializer(ProposalSerializer, RetrieveProposalMixin):
    class _ProposalSerializer(
        RetrieveCandidateSerializer, CandidateForProposalRetrieveMixin
    ):
        class Meta(CandidateSerializer.Meta):
            fields = (
                CandidateSerializer.Meta.fields
                + CandidateForProposalRetrieveMixin.Meta.fields
            )
            read_only_fields = fields

    candidate = _ProposalSerializer(read_only=True)

    class Meta(ProposalSerializer.Meta):
        fields = BasicProposalSerializer.Meta.fields + RetrieveProposalMixin.Meta.fields


class AvailableProposalIdField(serializer_fields.ProposalPrimaryKeyRelatedField):
    def to_internal_value(self, data):
        return super().to_internal_value(data).id


class CreateProposalSerializer(serializers.ModelSerializer):
    """Serializer for creating Proposal."""

    class Meta:  # noqa
        model = m.Proposal
        fields = ('id', 'job', 'candidate')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=m.Proposal.objects.all(),
                fields=('job', 'candidate'),
                message=_('Candidate is already proposed.'),
            )
        ]

    def validate(self, data):
        if data['job'].status != m.JobStatus.OPEN.key:
            raise ValidationError(_('Job is not open.'))

        return super().validate(data)


class PublicCandidateSerializer(serializers.ModelSerializer):

    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    languages = LanguageSerializer(many=True, required=False)
    linkedin_url = serializers.URLField(allow_blank=True, required=False)
    certifications = CandidateCertificationSerializer(many=True, required=False)
    resume = serializers.FileField(read_only=True)
    resume_thumbnail = serializers.FileField(read_only=True)
    resume_ja = serializers.FileField(read_only=True)
    resume_ja_thumbnail = serializers.FileField(read_only=True)
    cv_ja = serializers.FileField(read_only=True)
    cv_ja_thumbnail = serializers.FileField(read_only=True)

    class Meta:  # noqa
        model = m.Candidate
        fields = (
            'id',
            'owner',
            # name
            'first_name',
            'last_name',
            'first_name_kanji',
            'last_name_kanji',
            'first_name_katakana',
            'last_name_katakana',
            # contact
            'email',
            'phone',
            # online profiles
            'linkedin_url',
            # current employment
            'current_position',
            'current_company',
            # languages
            'languages',
            # certifications
            'certifications',
            # resume
            'resume',
            'resume_thumbnail',
            'resume_ja',
            'resume_ja_thumbnail',
            'cv_ja',
            'cv_ja_thumbnail',
        )
        extra_kwargs = {
            'email': {'required': True, 'allow_blank': False},
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }


class PublicCreateProposalSerializer(serializers.ModelSerializer):
    custom_error_messages = {
        'invalid_job_question_id': _('Job Question ID provided not valid'),
        'posting_not_found': _('Job has no posting: %(posting)s'),
        'hcaptcha_error': _('hCaptcha verification failed'),
    }

    class _QuestionAnswers(serializers.Serializer):
        job_question_id = serializers.IntegerField(write_only=True)
        answer = serializer_fields.RichTextField(write_only=True)

    candidate = PublicCandidateSerializer()
    job = serializers.PrimaryKeyRelatedField(
        queryset=m.Job.objects.all(), required=True
    )
    questions = _QuestionAnswers(many=True, write_only=True, required=False)
    posting = serializers.ChoiceField(
        choices=['private_posting', 'career_site_posting'], write_only=True
    )
    token = serializers.CharField(write_only=True, required=True)

    class Meta:  # noqa
        model = m.Proposal
        fields = ('id', 'job', 'candidate', 'questions', 'posting', 'token')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=m.Proposal.objects.all(),
                fields=('job', 'candidate'),
                message=_('Candidate is already proposed.'),
            )
        ]

    def validate(self, attrs):
        job = attrs.get('job')
        questions = attrs.get('questions', {})
        posting_str = attrs.get('posting')
        posting = getattr(job, posting_str, None)
        token = attrs.get('token')

        if posting is None:
            raise serializers.ValidationError(
                self.custom_error_messages['posting_not_found']
                % {'posting': posting_str}
            )

        valid_questions = set([q['job_question_id'] for q in questions]).issubset(
            set(posting.questions.values_list('id', flat=True))
        )
        if not valid_questions:
            raise serializers.ValidationError(
                self.custom_error_messages['invalid_job_question_id']
            )

        if self.context.get('is_create', True):
            response = requests.post(
                'https://hcaptcha.com/siteverify',
                data={'secret': settings.HCAPTCHA_SECRET_KEY, 'response': token},
            )
            response_json = response.json()
            if not response_json['success']:
                raise serializers.ValidationError(
                    self.custom_error_messages['hcaptcha_error']
                )
        return attrs

    def create(self, validated_data):
        validated_data.pop('token')
        candidate_data = validated_data.pop('candidate')
        languages = candidate_data.pop('languages', [])
        certifications = candidate_data.pop('certifications', [])
        questions = validated_data.pop('questions', [])
        job = validated_data['job']
        posting = getattr(job, validated_data.pop('posting'))
        org_content_type, org_id = get_user_org(job.owner.profile)

        candidate = m.Candidate.objects.filter(
            get_unique_emails_filter(candidate_data['email']),
            org_content_type=org_content_type,
            org_id=org_id,
        ).first()

        if not candidate:
            email = candidate_data.pop('email')
            candidate_defaults = dict(
                **candidate_data,
                owner=job.owner,
                org_content_type=org_content_type,
                org_id=org_id,
                source=m.CandidateSources.DIRECT_APPLY,
                created_by=job.owner,
            )
            try:
                candidate, candidate_created = m.Candidate.objects.get_or_create(
                    email=email,
                    org_content_type=org_content_type,
                    org_id=org_id,
                    defaults=candidate_defaults,
                )
            except ValidationError as e:
                raise serializers.ValidationError({'candidate': e.message_dict})

        for language in languages:
            candidate.languages.add(
                m.Language.objects.get(
                    language=language['language'], level=language['level']
                )
            )

        for ceritification in certifications:
            m.CandidateCertification.objects.create(
                candidate=candidate, **ceritification
            )

        proposal, proposal_created = m.Proposal.objects.get_or_create(
            job=validated_data['job'],
            candidate=candidate,
            defaults=dict(created_by=job.owner, is_direct_application=True),
        )

        for question in questions:
            job_question = posting.questions.get(id=question['job_question_id'])
            m.ProposalQuestion.objects.get_or_create(
                proposal=proposal, text=job_question.text, answer=question['answer']
            )

        return proposal


class CreateProposalThroughCandidateSerializer(CreateProposalSerializer):
    """Serializer for creating Proposal through Candidate serializer."""

    job = serializer_fields.JobPrimaryKeyRelatedField(required=True)

    class Meta:
        model = m.Proposal
        fields = ('job',)


class BaseUpdateProposalSerializer(serializers.ModelSerializer):
    """
    Abstract class with common validation for Update Classes
    """

    decline_reasons = serializers.PrimaryKeyRelatedField(
        queryset=m.ReasonDeclineCandidateOption.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    reasons_not_interested = serializers.PrimaryKeyRelatedField(
        queryset=m.ReasonNotInterestedCandidateOption.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    def validate(self, attrs):
        if 'status' in attrs:
            if (
                self.instance.status.stage == m.ProposalStatusStage.HIRED.key
                and attrs['status'].stage == m.ProposalStatusStage.HIRED.key
            ):
                pass
            elif self.instance.job.status != m.JobStatus.OPEN.key:
                raise ValidationError(_('Job has to be open'))

        return super().validate(attrs)


class YasgUpdateProposalSerializer(BaseUpdateProposalSerializer):
    """
    Combination of UpdateProposalByAgencySerializer and UpdateProposalSerializer
    for swagger spec generator
    """

    status = serializers.PrimaryKeyRelatedField(queryset=m.ProposalStatus.objects.all())

    class Meta:
        model = m.Proposal
        fields = (
            'id',
            'status',
            'is_rejected',
            'suitability',
            'decline_reasons',
            'reasons_not_interested',
            'reason_declined_description',
            'reason_not_interested_description',
        )


class UpdateProposalByAgencySerializer(BaseUpdateProposalSerializer):

    status = serializers.PrimaryKeyRelatedField(
        queryset=m.ProposalStatus.longlist.all()
    )

    class Meta:
        model = m.Proposal
        fields = (
            'status',
            'suitability',
            'decline_reasons',
            'reasons_not_interested',
            'reason_declined_description',
            'reason_not_interested_description',
        )


class UpdateProposalSerializer(BaseUpdateProposalSerializer):
    """Serializer for updating Proposal."""

    decline_reasons = serializers.PrimaryKeyRelatedField(
        queryset=m.ReasonDeclineCandidateOption.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    reasons_not_interested = serializers.PrimaryKeyRelatedField(
        queryset=m.ReasonNotInterestedCandidateOption.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    default_error_messages = {
        **BaseUpdateProposalSerializer.default_error_messages,
        'not_member_of_job_owner': _(
            'Only members of organisation which created the job can modify proposal'
        ),
    }

    class Meta:  # noqa
        model = m.Proposal
        fields = (
            'id',
            'status',
            'is_rejected',
            'suitability',
            'decline_reasons',
            'reasons_not_interested',
            'reason_declined_description',
            'reason_not_interested_description',
        )

    @require_request
    def validate(self, data):
        user = self.context['request'].user
        job = data.get('job')
        if job is None and self.instance is not None:
            job = self.instance.job

        if user.profile.org != job.organization:
            raise ValidationError(
                self.default_error_messages['not_member_of_job_owner']
            )

        return super().validate(data)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for the Notification model."""

    text = serializers.CharField(read_only=True)

    class Meta:  # noqa
        model = m.Notification
        fields = ('id', 'text', 'link', 'timestamp', 'unread', 'verb')


class RegistrationCheckEmailSerializer(serializers.Serializer):
    """Serializer for checking email for recruiter registration."""

    type = serializers.ChoiceField(choices=ORG_TYPES)
    email = serializers.EmailField(required=True)

    def validate_email(self, email):
        user = m.User.objects.filter(email=email).first()

        if user is not None:
            raise ValidationError(_('User with this email address already exists.'))

        return email


class RecruiterRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for recruiter registration."""

    via_job = serializer_fields.JobUuidRelatedField(required=False, write_only=True)
    terms_of_service = serializers.BooleanField(required=True, write_only=True)

    class Meta:  # noqa
        model = m.User
        fields = (
            'email',
            'first_name',
            'last_name',
            'password',
            'via_job',
            'terms_of_service',
            'country',
        )
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'password': {'write_only': True},
            'country': {'required': True},
        }

    @classmethod
    def get_only_user_data(cls, data):
        return {
            k: v for k, v in data.items() if k not in ['via_job', 'terms_of_service']
        }

    def validate(self, data):
        user_data = self.get_only_user_data(data)
        try:
            m.User(**user_data).clean_fields()
            validate_password(password=data.get('password'), user=m.User(**user_data))
        except ValidationError as e:
            raise serializers.ValidationError({'password': e.messages})

        return super().validate(data)

    def validate_email(self, email):
        agency = m.Agency.get_by_email_domain(email)

        if agency is None:
            raise ValidationError(
                _('Your email\'s domain is not connected to an agency.')
            )

        return email

    def validate_terms_of_service(self, value):
        if not value:
            self.fields['terms_of_service'].fail('required')

        return value

    def create(self, validated_data):
        return m.User.objects.create_user(**self.get_only_user_data(validated_data))


class OrgProposalStatusSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='status.id')
    group = serializers.CharField(source='status.group')
    status = serializers.CharField(source='status.status')
    stage = serializers.CharField(source='status.stage')

    class Meta:  # noqa
        model = m.OrganizationProposalStatus
        fields = (
            'id',
            'group',
            'status',
            'stage',
        )


class AddLinkedInCandidateSerializer(serializers.Serializer):
    class _ContactInfo(serializers.Serializer):
        email = serializers.CharField(default='', allow_blank=True, allow_null=True)
        linked_in = serializers.CharField(default='', allow_blank=True, allow_null=True)
        twitter = serializers.ListField(child=serializers.CharField(), required=False)
        website = serializers.ListField(child=serializers.CharField(), required=False)

    class _Pursuable(serializers.Serializer):
        desc = serializers.CharField(default='', allow_blank=True, allow_null=True)
        duration = serializers.CharField(required=False)
        date_start = serializers.DateField(required=False, allow_null=True)
        date_end = serializers.DateField(required=False, allow_null=True)
        currently_pursuing = serializers.BooleanField(
            required=False, default=False, allow_null=True
        )

    class _Education(_Pursuable):
        school = serializers.CharField(default='', allow_blank=True, allow_null=True)
        degree = serializers.CharField(default='', allow_blank=True, allow_null=True)
        fos = serializers.CharField(default='', allow_blank=True, allow_null=True)

    class _Experience(_Pursuable):
        title = serializers.CharField(default='', allow_blank=True, allow_null=True)
        org = serializers.CharField(default='', allow_blank=True, allow_null=True)
        location = serializers.CharField(default='', allow_blank=True, allow_null=True)

    education = _Education(many=True, required=False)
    experience = _Experience(many=True, required=False)
    name = serializers.CharField(
        required=False, default='', allow_blank=True, allow_null=True
    )
    headline = serializers.CharField(
        required=False, default='', allow_blank=True, allow_null=True
    )
    company = serializers.CharField(
        required=False, default='', allow_blank=True, allow_null=True
    )
    city = serializers.CharField(
        required=False, default='', allow_blank=True, allow_null=True
    )
    photo_base64 = serializers.CharField(required=False, default=None, allow_null=True)
    original = serializer_fields.CandidatePrimaryKeyRelatedField(
        required=False, default=None, allow_null=True
    )

    contact_info = _ContactInfo()
    proposal = CreateProposalThroughCandidateSerializer(required=False, allow_null=True)


class CheckLinkedinCandidateExists(serializers.Serializer):
    linkedin_url = serializers.URLField()

    def validate_linkedin_url(self, value):
        if parse_linkedin_slug(value) is None:
            raise ValidationError(_('LinkedIn URL is not correct'))

        return value

    def parse_slug(self):
        return parse_linkedin_slug(self.validated_data['linkedin_url'])


class ProposalMoveBodySerializer(serializers.ModelSerializer):
    """Serializer for moving proposal to other job.."""

    job = serializer_fields.JobPrimaryKeyRelatedField()

    class Meta:  # noqa
        model = m.Proposal
        fields = (
            'id',
            'job',
        )

    def validate(self, data):
        if data['job'] == self.instance.job:
            raise ValidationError({'job': _('Already proposed to this job.')})

        if self.instance.job.organization != data['job'].organization:
            raise ValidationError(
                {'job': _('Can\'t move proposal to other organization\'s job.')}
            )

        proposal_exists = m.Proposal.objects.filter(
            job=data['job'], candidate=self.instance.candidate
        ).exists()

        if proposal_exists:
            raise ValidationError(
                {'job': _('The candidate is already proposed to this job.')}
            )

        return super().validate(data)


class JobDetailQuerySerializer(serializers.Serializer):
    show_pipeline = serializers.BooleanField(required=False)


class JobQuerySerializer(serializers.Serializer):
    """Serializer for parameter of JobSerializer.get_candidate_proposed."""

    check_candidate_proposed = serializer_fields.CandidatePrimaryKeyRelatedField(
        required=False, help_text='ID of Candidate to check proposed to Job'
    )

    check_user_has_access = serializers.PrimaryKeyRelatedField(
        queryset=m.User.objects.all(),
        required=False,
        help_text='ID of User to check access to Job',
    )

    show_pipeline = serializers.BooleanField(required=False)
    show_live_proposal_count = serializers.BooleanField(required=False)


class ZohoGetSerializer(serializers.Serializer):
    url = serializers.URLField(required=True)

    def validate_url(self, value):
        try:
            get_candidate_id_from_zoho_url(value)
        except ValueError as e:
            raise ValidationError(_('Invalid Zoho Candidate URL.'))

        return value

    def get_candidate_zoho_id(self):
        return get_candidate_id_from_zoho_url(self.validated_data['url'])


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Feedback
        fields = ('text', 'page_url', 'page_html', 'redux_state')
        extra_kwargs = {
            'text': {'required': True, 'allow_blank': False},
            'page_url': {'required': True, 'allow_blank': False},
        }


class AgencyCategorySerializer(serializers.ModelSerializer):
    group = serializers.CharField(source='get_group_display')

    class Meta:  # noqa
        model = m.AgencyCategory
        fields = ('id', 'group', 'title')
        read_only_fields = fields


class FunctionSerializer(serializers.ModelSerializer):
    class Meta:  # noqa
        model = m.Function
        fields = ('id', 'title')
        read_only_fields = fields


class DateSerializer(serializers.Serializer):
    date = serializers.DateField()


class DateRangeSerializer(serializers.Serializer):
    date_start = serializers.DateField()
    date_end = serializers.DateField()

    def validate(self, data):
        if data['date_start'] > data['date_end']:
            raise ValidationError('date_start should be less than date_end')

        return super().validate(data)


class StatsFilterSerializer(serializers.Serializer):
    filter_type = serializers.ChoiceField(['team', 'function', 'owner',])
    filter_value = serializers.CharField(required=False, allow_blank=True)


class GranularitySerializer(serializers.Serializer):
    granularity = serializers.ChoiceField(['day', 'week', 'month',])


class StatsJobSerializer(serializers.Serializer):
    job = serializer_fields.JobPrimaryKeyRelatedField()


class StatsQuerySerializer(DateRangeSerializer, StatsFilterSerializer):
    pass


class StatsChartQuerySerializer(StatsQuerySerializer, GranularitySerializer):
    pass


class AnalyticsSourcesQuerySerializer(StatsQuerySerializer):
    hired = serializers.BooleanField(required=True)


class JobAnalyticsQuerySerializer(
    GranularitySerializer, StatsJobSerializer, DateRangeSerializer
):
    pass


class ProposalsSnapshotQuerySerializer(
    DateSerializer, StatsJobSerializer, DateRangeSerializer, GranularitySerializer
):
    pass


class ProposalsSnapshotSerializer(serializers.ModelSerializer):
    # TODO: Due to future C/A contracting requirements
    # TODO: there might be specific serializers for available candidates
    candidate = serializers.SerializerMethodField()
    proposal = serializers.IntegerField(source='proposal.id')

    status = ProposalStatusSerializer()
    changed_at = serializers.SerializerMethodField()

    def get_candidate(self, history):
        candidate = history.proposal.candidate
        return {
            "name": candidate.name,
            "current_company": candidate.current_company,
            "current_position": candidate.current_position,
        }

    def get_changed_at(self, history):
        return history.changed_at.date().isoformat()

    class Meta:
        model = m.ProposalStatusHistory
        fields = ('candidate', 'status', 'changed_at', 'proposal')


class InvitedSetsFromDict:
    def __init__(self, invited=None, emails=None, users=None):
        self.users = users or set()
        self.emails = emails or set()

        if invited is None:
            return

        for item in invited:
            user = self.get_field(item, 'user')
            if user:
                self.users.add(user)

            email = self.get_field(item, 'email')
            if email:
                self.emails.add(email)

    def __sub__(self, other):
        return self.__class__(
            users=self.users - other.users, emails=self.emails - other.emails
        )

    def contained(self, invited):
        for item in invited:
            if (
                self.get_field(item, 'email') in self.emails
                or self.get_field(item, 'user') in self.users
            ):
                yield item

    @staticmethod
    def get_field(item, key):
        return item.get(key)


class InvitedSetsFromInstance(InvitedSetsFromDict):
    @staticmethod
    def get_field(item, key):
        return getattr(item, key, None)


class PlacementSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    proposal = serializer_fields.ProposalPrimaryKeyRelatedField()

    class Meta:
        model = m.Placement
        fields = (
            'id',
            'proposal',
            'current_salary',
            'offered_salary',
            'signed_at',
            'starts_work_at',
            'candidate_source',
            'candidate_source_details',
        )


class FeeSerializer(serializers.ModelSerializer):
    placement = PlacementSerializer(required=False, allow_null=True)
    job_contract = serializer_fields.JobAgencyContractRelatedField(
        required=False, allow_null=True
    )
    proposal_id = AvailableProposalIdField(allow_null=True, required=False)
    proposal = ProposalSerializer(read_only=True)

    split_allocation_id = serializers.IntegerField(
        read_only=True, source='split_allocation.id'
    )
    is_editable = serializers.BooleanField(read_only=True)
    submitted_by = OrgMemberSerializer(read_only=True)
    notes_to_approver = serializer_fields.RichTextField(required=False)
    nbv_date = serializers.DateField(required=False, allow_null=True)
    nfi_date = serializers.DateField(required=False, allow_null=True)
    contract_type = serializers.CharField(read_only=True)
    client_id = serializers.IntegerField(
        read_only=True, source='job_contract.job.client_id'
    )

    def validate(self, attrs):
        data = super().validate(attrs)
        if 'consumption_tax' not in attrs and 'invoice_value' in data:
            data['consumption_tax'] = Decimal(data['invoice_value']) * Decimal('0.1')
        return data

    @staticmethod
    def create_or_update_placement(placement_data):
        if placement_data is not None:
            pk = placement_data.pop('id', None)
            placement, created = m.Placement.objects.update_or_create(
                id=pk, defaults=placement_data
            )
            return placement

        return None

    @require_request
    def assign_placement(self, validated_data, placement):
        if placement:
            validated_data['placement'] = placement
            proposal_id = placement.proposal_id

            validated_data['proposal_id'] = proposal_id

            job = m.Job.objects.get(proposals__id=proposal_id)

            validated_data['job_contract'] = m.JobAgencyContract.objects.get(
                job=job, agency=self.context['request'].user.profile.org
            )

            validated_data['nbv_date'] = placement.signed_at
            validated_data['nfi_date'] = placement.starts_work_at

    @require_request
    def create(self, validated_data):

        self.assign_placement(
            validated_data,
            self.create_or_update_placement(validated_data.pop('placement', None)),
        )

        nbv_date = validated_data.get('nbv_date', None)
        job_contract = validated_data.get('job_contract', None)

        user = self.context['request'].user
        agency = user.profile.org

        if nbv_date is None:
            if job_contract is None:
                raise serializers.ValidationError(
                    {'job_contract': [self.job_contract.error_messages['required']]}
                )

            contract = job_contract.job.client.contracts.filter(agency=agency).first()

            if contract is None:
                raise serializers.ValidationError(
                    _('Contract with this client doesn\'t exist')
                )

            validated_data['nbv_date'] = contract.start_at or contract.created_at

        validated_data.update(
            agency=agency, created_by=user,
        )

        if 'status' in validated_data:
            validated_data.update(
                **get_fee_status_update_and_notify(
                    status=validated_data['status'],
                    user=self.context['request'].user,
                    update=validated_data,
                )
            )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        self.assign_placement(
            validated_data,
            self.create_or_update_placement(validated_data.pop('placement', None)),
        )

        if 'status' in validated_data:
            validated_data.update(
                **get_fee_status_update_and_notify(
                    status=validated_data['status'],
                    user=self.context['request'].user,
                    update=validated_data,
                    fee=instance,
                )
            )

        return super().update(instance, validated_data)

    class Meta:
        model = m.Fee
        fields = (
            'placement',
            'proposal_id',
            'id',
            'job_contract',
            'split_allocation_id',
            'status',
            'submitted_by',
            'billing_address',
            'should_send_invoice_email',
            'invoice_email',
            'contract_type',
            'bill_description',
            'consulting_fee_type',
            'consulting_fee',
            'consulting_fee_percentile',
            'invoice_value',
            'nbv_date',
            'nfi_date',
            'invoice_issuance_date',
            'notes_to_approver',
            'consumption_tax',
            'proposal',
            'invoice_due_date',
            'invoice_status',
            'invoice_paid_at',
            'client_id',
            # annotation
            'is_editable',
        )
        validators = [
            RequireOneOfValidator(
                fields=['placement', 'job_contract'],
                messages={
                    'required': _(
                        'Either Placement or Job Contract ID should be provided'
                    )
                },
            ),
            RequireOneOfValidator(
                fields=['placement', 'nfi_date'],
                messages={
                    'required': _(
                        'Retainer fee date must be set if not a placement fee'
                    )
                },
            ),
            RequireIfValidator(field='title', flag_field='is_admin_fee',),
            ModeRequirementValidator(
                mode_field='consulting_fee_type',
                field_cases={
                    'consulting_fee': m.ConsultingFeeType.FIXED.key,
                    'consulting_fee_percentile': m.ConsultingFeeType.PERCENTILE.key,
                },
            ),
        ]


class FeeSplitAllocationSerializer(serializers.ModelSerializer):
    fee_status = serializers.ChoiceField(
        choices=m.FeeStatus.get_choices(), required=False,
    )
    submitted_by = OrgMemberSerializer(read_only=True, source='placement.submitted_by')
    fee = serializer_fields.FeePrimaryKeyRelatedField()

    is_editable = serializers.SerializerMethodField()

    def get_is_editable(self, value):
        if not self.context['request']:
            return False

        profile = getattr(self.context['request'].user, 'profile', None)
        if profile is None:
            return False

        fee_id = None
        if self.instance:
            fee_id = self.instance.fee_id

        if fee_id is None:
            return False

        return m.Fee.objects.filter(profile.editable_fee_filter, id=fee_id).exists()

    @require_request
    def set_placement_status(self, validated_data):
        fee = validated_data.get('fee')
        is_status_field_exist = 'fee_status' in validated_data
        status = validated_data.pop('fee_status', None)

        if fee and is_status_field_exist:
            fee_update = get_fee_status_update_and_notify(
                status=status, fee=fee, user=self.context['request'].user
            )
            for key, value in fee_update.items():
                setattr(fee, key, value)
            fee.save()

    def create(self, validated_data):
        self.set_placement_status(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self.set_placement_status(validated_data)
        return super().update(instance, validated_data)

    class Meta:
        model = m.FeeSplitAllocation
        read_only_fields = ['file']
        split_fields = [
            'candidate_owner_split',
            'lead_candidate_consultant_split',
            'support_consultant_split',
            'client_originator_split',
            'lead_bd_consultant_split',
            'activator_split',
        ]
        fields = (
            'id',
            'submitted_by',
            'fee',
            'fee_status',
            'candidate_owner',
            'lead_candidate_consultant',
            'support_consultant',
            'client_originator',
            'lead_bd_consultant',
            'activator',
            'file',
            'is_editable',
            *read_only_fields,
            *split_fields,
        )
        validators = [
            FieldsSumValidator(
                total=1, fields=split_fields, message=_('Splits must add up to 100%')
            ),
            SplitHasUserValidator(
                user='candidate_owner', split='candidate_owner_split'
            ),
            SplitHasUserValidator(
                user='lead_candidate_consultant',
                split='lead_candidate_consultant_split',
            ),
            SplitHasUserValidator(
                user='support_consultant', split='support_consultant_split'
            ),
            SplitHasUserValidator(
                user='client_originator', split='client_originator_split'
            ),
            SplitHasUserValidator(
                user='lead_bd_consultant', split='lead_bd_consultant_split'
            ),
            SplitHasUserValidator(user='activator', split='activator_split'),
        ]


class ValidateCandidateSplitAllocationSerializer(serializers.ModelSerializer):
    placement_status = serializers.ChoiceField(
        choices=m.FeeStatus.get_choices(), required=False,
    )

    class Meta:
        model = m.FeeSplitAllocation
        split_fields = [
            'candidate_owner_split',
            'lead_candidate_consultant_split',
            'support_consultant_split',
            'client_originator_split',
            'lead_bd_consultant_split',
            'activator_split',
        ]
        fields = (
            'placement_status',
            'candidate_owner',
            'lead_candidate_consultant',
            'support_consultant',
            'client_originator',
            'lead_bd_consultant',
            'activator',
            'file',
            *split_fields,
        )
        validators = [
            FieldsSumValidator(
                total=1, fields=split_fields, message=_('Splits must add up to 100%')
            )
        ]


class CandidateSplitAllocationFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.FeeSplitAllocation
        fields = ('id', 'file')


class AgencyClientInfoQuerySerializer(serializers.Serializer):
    client = serializer_fields.ClientPrimaryKeyRelatedField()

    class Meta:
        fields = ('client',)


class AgencyClientInfoSerializer(serializers.ModelSerializer):
    originator = serializer_fields.OrgMemberPrimaryKeyRelatedField(
        required=False, allow_null=True
    )
    account_manager = serializer_fields.OrgMemberPrimaryKeyRelatedField(
        required=False, allow_null=True
    )
    updated_by = OrgMemberSerializer(read_only=True)

    # rich fields
    info = serializer_fields.RichTextField(required=False)
    notes = serializer_fields.RichTextField(required=False)

    class Meta:
        model = m.AgencyClientInfo
        fields = (
            'industry',
            'type',
            'originator',
            'info',
            'notes',
            'account_manager',
            'updated_at',
            'updated_by',
            'billing_address',
            'portal_url',
            'portal_login',
            'portal_password',
            'primary_contact_number',
            'website',
        )
        read_only_fields = ('updated_at',)

    @require_request
    def save(self, **kwargs):
        user = self.context['request'].user
        agency = user.profile.org
        client = self.context['view'].kwargs['client']

        self.validated_data['updated_by'] = user

        instance, created = self.Meta.model.objects.update_or_create(
            agency=agency, client=client, defaults=self.validated_data
        )

        return instance


class ProposalRetrieveQuerySerializer(serializers.Serializer):
    extra_fields = serializers.CharField(required=False)


class DealPipelineRoundsSerializer(serializers.Serializer):
    first_round = serializers.IntegerField(read_only=True)
    intermediate_round = serializers.IntegerField(read_only=True)
    final_round = serializers.IntegerField(read_only=True)
    offer_round = serializers.IntegerField(read_only=True)
    total = serializers.IntegerField(read_only=True)

    class Meta:
        fields = (
            'first_round',
            'intermediate_round',
            'final_round',
            'offer_round',
            'total',
        )


class DealPipelineMetricsSerializer(serializers.Serializer):
    total = DealPipelineRoundsSerializer(read_only=True)
    realistic = DealPipelineRoundsSerializer(read_only=True)

    class Meta:
        fields = ('total', 'realistic')


class DealPipelineProposalSerializer(ProposalSerializer):
    deal_stage = serializers.CharField(source='status.deal_stage')
    total_value = serializers.SerializerMethodField()
    realistic_value = serializers.SerializerMethodField()

    @require_request
    def get_total_value(self, instance):
        request = self.context['request']
        coefficients = request.user.profile.org.deal_pipeline_coefficients
        multiplier = coefficients['hiring_fee']

        return int(instance.converted_current_salary * multiplier)

    @require_request
    def get_realistic_value(self, instance):
        request = self.context['request']
        coefficients = request.user.profile.org.deal_pipeline_coefficients
        multiplier = (
            coefficients['hiring_fee'] * coefficients[instance.status.deal_stage]
        )

        return int(instance.converted_current_salary * multiplier)

    class Meta:
        model = m.Proposal
        fields = (
            'id',
            'candidate',
            'job',
            'client_name',
            'deal_stage',
            'total_value',
            'realistic_value',
        )


class ApprovalSerializer(serializers.Serializer):
    job_contract_id = serializers.IntegerField(read_only=True)
    fee_id = serializers.IntegerField(read_only=True)
    proposal_id = serializers.IntegerField(read_only=True)
    candidate_name = serializers.CharField(read_only=True)
    job_title = serializers.CharField(read_only=True)
    client_name = serializers.CharField(read_only=True)
    fee_status = serializers.CharField(read_only=True)
    contract_type = serializers.CharField(read_only=True)
    bill_description = serializers.CharField(read_only=True)
    submitted_by_name = serializers.CharField(read_only=True)
    submitted_at = serializers.DateTimeField(format="%Y-%m-%d", read_only=True)


class ApprovalQuerySerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=m.FeeApprovalType.get_choices())


class JobAgencyContractSerializer(serializers.ModelSerializer):
    contract_type = serializers.ChoiceField(
        choices=m.JobContractTypes.get_choices(),
        required=True,
        allow_null=False,
        allow_blank=False,
    )
    industry = serializers.ChoiceField(
        choices=m.Industry.get_choices(),
        required=True,
        allow_blank=False,
        allow_null=False,
    )

    client_id = serializers.CharField(read_only=True, source='job.client_id')

    contact_person_name = serializers.CharField(
        max_length=100, required=True, allow_null=False, allow_blank=False,
    )

    signed_at = serializers.DateField(required=True, allow_null=False)

    def update(self, instance, validated_data):
        validated_data['is_filled_in'] = True
        return super().update(instance, validated_data)

    class Meta:
        model = m.JobAgencyContract
        fields = (
            'id',
            'contract_type',
            'contact_person_name',
            'industry',
            'signed_at',
            'client_id',
        )


class CandidateVersionSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()

    class Meta:
        model = Version
        fields = (
            'object_id',
            'revision',
            'content_type',
            'actor',
            'data',
        )

    def format_education_detail(self, detail):
        return "{degree} {department} at {institute}, {date_start} - {date_end_or_now}".format(
            date_end_or_now='now'
            if detail['currently_pursuing']
            else detail['date_end'],
            **detail,
        )

    def format_experience_detail(self, detail):
        return "{occupation} at {company}, {date_start} - {date_end_or_now}. {summary}".format(
            date_end_or_now='now'
            if detail['currently_pursuing']
            else detail['date_end'],
            **detail,
        )

    def get_actor(self, obj):
        if obj.revision.user is not None:
            return obj.revision.user.full_name
        else:
            return _("Anonymous User")

    def get_data(self, obj):
        user_org = self.context['request'].user.profile.org
        content_type = ContentType.objects.get_for_model(user_org)
        data = json.loads(obj.serialized_data)[0]['fields']
        candidate_notes_qs = obj.revision.version_set.filter(
            Q(content_type=ContentType.objects.get_for_model(m.CandidateNote))
            & Q(serialized_data__contains=f'"content_type": {content_type.id}')
            & Q(serialized_data__contains=f'"object_id": {user_org.id}')
        )
        if candidate_notes_qs:
            data['note'] = json.loads(candidate_notes_qs.first().serialized_data)[0][
                'fields'
            ]['text']
        education_details_qs = obj.revision.version_set.filter(
            content_type=ContentType.objects.get_for_model(m.EducationDetail)
        )
        data['education_details'] = [
            self.format_education_detail(
                json.loads(detail.serialized_data)[0]['fields']
            )
            for detail in education_details_qs
        ]

        experience_details_qs = obj.revision.version_set.filter(
            content_type=ContentType.objects.get_for_model(m.ExperienceDetail)
        )
        data['experience_details'] = [
            self.format_experience_detail(
                json.loads(detail.serialized_data)[0]['fields']
            )
            for detail in experience_details_qs
        ]

        candidate_files_qs = obj.revision.version_set.filter(
            content_type=ContentType.objects.get_for_model(m.CandidateFile)
        )
        data['files'] = [
            json.loads(detail.serialized_data)[0]['fields']['file']
            for detail in candidate_files_qs
        ]

        return data


class VerboseProposalCommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    proposal = CandidateProposalSerializer()

    class Meta:  # noqa
        model = m.ProposalComment
        fields = ('id', 'proposal', 'author', 'text', 'created_at', 'system')
        read_only_fields = ('id', 'author', 'created_at', 'system')

    @require_request
    def get_author(self, comment):
        user = self.context['request'].user
        if comment.author is not None:
            if comment.author.profile is None:
                return ''

            if user.profile.org == comment.author.profile.org or (
                comment.public and not comment.system
            ):
                return PublicUserSerializer(comment.author).data

            return comment.author.profile.org.name
        else:
            return _('Anonymous')


class CandidateCommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:  # noqa
        model = m.CandidateComment
        fields = ('id', 'candidate', 'author', 'text', 'created_at', 'system')
        read_only_fields = ('id', 'author', 'created_at', 'system')

    @require_request
    def get_author(self, comment):
        user = self.context['request'].user

        if comment.author is None or comment.author.profile is None:
            return ''

        if user.profile.org == comment.author.profile.org or (
            comment.public and not comment.system
        ):
            return PublicUserSerializer(comment.author).data


class CreateCandidateCommentSerializer(serializers.ModelSerializer):
    class Meta:  # noqa
        model = m.CandidateComment
        fields = ('id', 'candidate', 'text', 'public')
        read_only_fields = ('id',)

    @require_request
    def create(self, validated_data):
        """Add user for the context to the created object."""
        return m.CandidateComment.objects.create(
            **validated_data, author=self.context['request'].user,
        )


class InterviewTemplateSerializer(serializers.ModelSerializer):
    class Meta:  # noqa
        model = m.InterviewTemplate
        fields = ('interview_type', 'default_order')


class QuickActionRequestSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=QuickActionVerb.get_choices())
    to_status = serializer_fields.ProposalStatusLookupField(
        required=False, allow_null=True
    )

    @require_request
    def validate(self, data):
        if self.context['proposal'].job.status != m.JobStatus.OPEN.key:
            raise serializers.ValidationError(_('Job has to be open'))
        if data['action'] == QuickActionVerb.CHANGE_STATUS and not data.get(
            'to_status'
        ):
            raise serializers.ValidationError(_('Missing `to_status` for quick action'))

        return super().validate(data)


class LegalAgreementSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display')

    class Meta:  # noqa
        model = m.LegalAgreement
        fields = ('id', 'document_type', 'document_type_display', 'version', 'file')
        read_only_fields = fields


class ClientSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Client
        fields = [
            'name',
            'name_ja',
            'website',
            'country',
            'function_focus',
            'logo',
            'career_site_slug',
            'is_career_site_enabled',
        ]
        extra_kwargs = {'name_ja': {'required': True, 'allow_blank': False}}


class ZendeskJWTSerializer(serializers.Serializer):
    token = serializers.CharField(read_only=True)


class PrivateJobPostingQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.PrivateJobPostingQuestion
        fields = ('id', 'text')


class CareerSiteJobPostingQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.CareerSiteJobPostingQuestion
        fields = ('id', 'text')


class JobPostingMixin(metaclass=serializers.SerializerMetaclass):
    skills = TagSerializer(many=True)
    required_languages = LanguageSerializer(many=True)
    questions = PrivateJobPostingQuestionSerializer(many=True)
    job_id = serializers.IntegerField()

    class Meta:
        fields = ['job_id', 'skills', 'required_languages', 'questions'] + [
            field.name for field in m.BaseJob._meta.fields
        ]

    def get_field_model_maybe(self, field):
        declared_field = self._declared_fields.get(field)
        if declared_field:
            declared_field = getattr(declared_field, 'child', declared_field)
            return declared_field.Meta.model
        else:
            raise Exception(f"Can't find model for {field}")

    def validate_job_id(self, value):
        if not self.instance and self.Meta.model.objects.filter(job_id=value).exists():
            raise ValidationError(
                '{} with job_id={} already exists.'.format(self.Meta.model, value)
            )
        return value

    @require_request
    def create(self, validated_data):
        question_model = self.get_field_model_maybe('questions')
        skills = validated_data.pop('skills', [])
        languages = validated_data.pop('required_languages', [])
        questions = validated_data.pop('questions', [])

        user = self.context['request'].user
        org = user.profile.org

        job = self.Meta.model(**validated_data)
        job.save()

        for language in languages:
            job.required_languages.add(
                m.Language.objects.get(
                    language=language['language'], level=language['level']
                )
            )

        for question_data in questions:
            question_model.objects.create(job=job, **question_data)

        for skill in skills:
            tag, _ = m.Tag.objects.get_or_create(
                name=skill['name'].lower(),
                type='skill',
                org_id=org.id,
                org_content_type=ContentType.objects.get_for_model(org),
                defaults={'organization': org, 'created_by': user},
            )
            try:
                with transaction.atomic():
                    job.skills.add(tag, through_defaults={'attached_by': user})
            except IntegrityError:
                # skip already attached tag
                pass

        return job

    @require_request
    def update(self, instance, validated_data):
        question_model = self.get_field_model_maybe('questions')
        skills = validated_data.pop('skills', None)
        languages = validated_data.pop('required_languages', None)
        questions = validated_data.pop('questions', None)

        user = self.context['request'].user
        org = user.profile.org

        update_instance_fields(instance, validated_data)
        instance.save()

        if languages is not None:
            instance.required_languages.clear()
            for language in languages:
                instance.required_languages.add(
                    m.Language.objects.get(
                        language=language['language'], level=language['level']
                    )
                )

        # replace all
        if questions is not None:
            instance.questions.all().delete()
            for question_data in questions:
                question_model.objects.create(job=instance, **question_data)

        if skills is not None:
            instance.skills.clear()
            for skill in skills:
                tag, _ = m.Tag.objects.get_or_create(
                    name=skill['name'].lower(),
                    type='skill',
                    org_id=org.id,
                    org_content_type=ContentType.objects.get_for_model(org),
                    defaults={'organization': org, 'created_by': user},
                )
                try:
                    with transaction.atomic():
                        instance.skills.add(tag, through_defaults={'attached_by': user})
                except IntegrityError:
                    # skip already attached tag
                    pass

        return instance


class PublicJobPostingMixin(metaclass=serializers.SerializerMetaclass):
    questions = PrivateJobPostingQuestionSerializer(many=True)
    required_languages = LanguageSerializer(many=True)
    skills = TagSerializer(many=True, required=False)
    function = JobFunctionSerializer()

    class Meta:  # noqa
        model = m.PrivateJobPosting
        fields = (
            # Details
            'id',
            'job_id',
            'title',
            'function',
            'employment_type',
            'mission',
            'responsibilities',
            # Requirements
            'requirements',
            'skills',
            'required_languages',
            # Job Conditions
            'salary_from',
            'salary_to',
            'salary_per',
            'salary_currency',
            'bonus_system',
            'probation_period_months',
            'work_location',
            'working_hours',
            'break_time_mins',
            'flexitime_eligibility',
            'telework_eligibility',
            'overtime_conditions',
            'paid_leaves',
            'additional_leaves',
            'social_insurances',
            'commutation_allowance',
            'other_benefits',
            # Others
            'questions',
        )


class BaseJobSerializer(JobPostingMixin, serializers.ModelSerializer):
    questions = JobQuestionSerializer(many=True)
    job_id = serializers.IntegerField(source='id')

    class Meta:
        model = m.Job
        fields = JobPostingMixin.Meta.fields


class PrivateJobPostingSerializer(JobPostingMixin, serializers.ModelSerializer):
    questions = PrivateJobPostingQuestionSerializer(many=True)
    is_enabled = serializers.BooleanField()

    class Meta:
        model = m.PrivateJobPosting
        fields = JobPostingMixin.Meta.fields + ['public_uuid', 'is_enabled']
        read_only_fields = ['public_uuid']

    @require_request
    def create(self, validated_data):
        is_enabled = validated_data.pop('is_enabled', False)
        validated_data['public_uuid'] = uuid.uuid4() if is_enabled else None
        return super().create(validated_data)

    @require_request
    def update(self, instance, validated_data):
        was_enabled = instance.is_enabled
        is_enabled = validated_data.pop('is_enabled', False)
        if was_enabled != is_enabled:
            validated_data['public_uuid'] = uuid.uuid4() if is_enabled else None
        return super().update(instance, validated_data)


class PrivateJobPostingPublicSerializer(
    PublicJobPostingMixin, serializers.ModelSerializer
):
    """Serializer for the PrivateJobPosting public objects."""

    organization = JobOrganizationSerializer(source='job.organization')
    questions = PrivateJobPostingQuestionSerializer(many=True)
    public_uuid = serializers.CharField(read_only=True)

    class Meta:  # noqa
        model = m.PrivateJobPosting
        fields = (
            'organization',
            'questions',
            'public_uuid',
        ) + PublicJobPostingMixin.Meta.fields


class CareerSiteOrganizationSerializer(serializers.ModelSerializer):
    """Serializer for organization data displayed on career page"""

    class Meta:
        model = m.Client
        fields = ('id', 'type', 'name', 'name_ja', 'logo')


class CareerSiteJobPostingSerializer(JobPostingMixin, serializers.ModelSerializer):
    """Serializer for CareerSiteJobPosting objects"""

    questions = CareerSiteJobPostingQuestionSerializer(many=True)
    slug = serializers.CharField(read_only=True)

    class Meta:
        model = m.CareerSiteJobPosting
        fields = JobPostingMixin.Meta.fields + ['is_enabled', 'slug']


class CareerSiteJobPostingPublicSerializer(
    PublicJobPostingMixin, serializers.ModelSerializer
):
    questions = CareerSiteJobPostingQuestionSerializer(many=True)
    slug = serializers.CharField(read_only=True)

    class Meta:
        model = m.CareerSiteJobPosting
        fields = ('questions', 'slug') + PublicJobPostingMixin.Meta.fields


class NoteActivitySerializer(serializers.ModelSerializer):
    proposal = serializer_fields.ProposalPrimaryKeyRelatedField(
        required=False,
        error_messages={
            'not_org_job': _(
                'Job proposal is assigned to belongs to other organisation'
            )
        },
    )
    job = serializer_fields.JobPrimaryKeyRelatedField(required=False)
    candidate = serializer_fields.CandidatePrimaryKeyRelatedField(required=False)

    class Meta:
        model = m.NoteActivity
        fields = (
            'id',
            'content',
            'proposal',
            'candidate',
            'job',
            'author',
            'created_at',
            'updated_at',
        )
        read_only_fields = [
            'id',
            'author',
            'created_at',
            'updated_at',
        ]
        validators = [
            RequireOneOfValidator(
                fields=['candidate', 'proposal', 'job'], exclusive=True
            )
        ]

    @require_request
    def create(self, validated_data):
        """Add user for the context to the created object."""
        validated_data.update(author=self.context['request'].user)
        return super().create(validated_data)


class NoteActivityQuerySerializer(serializers.Serializer):
    proposal = serializers.IntegerField(required=False)
    candidate = serializers.IntegerField(required=False)
    job = serializers.IntegerField(required=False)

    class Meta:
        validators = [
            RequireOneOfValidator(
                fields=['candidate', 'proposal', 'job'], exclusive=True
            )
        ]
