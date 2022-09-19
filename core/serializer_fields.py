import bleach
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from core import models as m
from core.utils import require_request
from core.validators import unique_entries


class AgencyMemberForCandidatePrimaryKeyRelatedField(
    serializers.PrimaryKeyRelatedField
):
    @require_request
    def get_queryset(self):
        request = self.context.get('request', None)
        return request.user.profile.org.members.all()


class CandidatePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """Serializer field to get only available Candidates."""

    @require_request
    def get_queryset(self):
        """Filter available Candidates."""
        return self.context['request'].user.profile.apply_candidates_filter(
            m.Candidate.objects
        )


class ClientPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """Serializer field to get only available clients."""

    @require_request
    def get_queryset(self):
        profile = self.context['request'].user.profile

        if hasattr(profile, 'client') or hasattr(profile, 'agency'):
            return profile.org.apply_available_clients_filter(m.Client.objects)

        return m.Client.objects.none()


class FeePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """Serializer field to get only own Placements."""

    def get_queryset(self):
        """Filter out Proposals User doesn't have access to."""
        profile = self.context['request'].user.profile

        if isinstance(profile.org, m.Agency):
            return m.Fee.objects.filter(profile.editable_fee_filter)

        return m.Fee.objects.none()


class JobClientRelatedField(serializers.PrimaryKeyRelatedField):
    """Serializer that only allowing to assign current user's client or curent user's agency's puppet clients"""

    @require_request
    def get_queryset(self):
        org = self.context['request'].user.profile.org
        if isinstance(org, m.Client):
            return m.Client.objects.filter(id=org.id)
        if isinstance(org, m.Agency):
            return m.Client.objects.filter(owner_agency=org)
        return m.Client.objects.none()


class JobAgencyContractRelatedField(serializers.PrimaryKeyRelatedField):
    @require_request
    def get_queryset(self):
        profile = self.context['request'].user.profile

        if isinstance(profile.org, m.Agency):
            return m.JobAgencyContract.objects.filter(agency=profile.org)

        return m.JobAgencyContract.objects.none()


class JobPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """Serializer field to get only available Jobs."""

    @require_request
    def get_queryset(self):
        """Filter available Jobs."""
        return self.context['request'].user.profile.apply_jobs_filter(m.Job.objects)


class JobUuidRelatedField(serializers.UUIDField):
    """Field for Job's public UUID."""

    def to_internal_value(self, data):
        uuid = super().to_internal_value(data)
        return m.Job.objects.filter(private_posting__public_uuid=uuid).first()


class ProposalStatusLookupField(serializers.DictField):
    """Field for ProposalStatus lookup. Accepts key-value dict of field_name-field_value."""

    def to_internal_value(self, data):
        if data:
            return m.ProposalStatus.objects.filter(**data).first()
        return None


class ManagersPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """Serializer field to get only Hiring Managers."""

    def get_queryset(self):
        """Filter Users to Hiring Managers."""
        return self.context['request'].user.profile.client.members.all()


class OrgMemberPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    @require_request
    def get_queryset(self):
        request = self.context.get('request', None)
        return request.user.profile.org.members.all()


class OrganizationRelatedField(serializers.RelatedField):
    """Serializer field to get own User's Orgaization."""

    def get_queryset(self):
        """Filter objects by organization type."""
        Organization = self.context['request'].user.profile.org.__class__
        return Organization.objects.all()

    def to_representation(self, data):
        """Return organization pk."""
        return data.pk


class ProposalPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """Serializer field to get only own Proposals."""

    def get_queryset(self):
        """Filter out Proposals User doesn't have access to."""
        return self.context['request'].user.profile.apply_proposals_filter(
            m.Proposal.objects.all()
        )


class TeamsPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """Serializer field to get only current org Teams."""

    @require_request
    def get_queryset(self):
        return self.context['request'].user.profile.org.teams


class RichTextField(serializers.Field):
    """Field for rich text editor HTML cleaning"""

    default_error_messages = {
        'blank': _('This field may not be blank.'),
    }

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        only_text = bleach.clean(data, tags=[], strip=True).strip()

        if not only_text:  # to remove empty <p></p>
            return ''

        return bleach.clean(
            data, tags=['p', 'ul', 'li', 'ol', 'strong', 'em', 'u'], attributes={},
        )

    def run_validation(self, data=serializers.empty):
        """Validates HTML contains text, not just empty tags."""

        if self.required and data is not serializers.empty:
            only_text = bleach.clean(data, tags=[], strip=True).strip()

            if not only_text:
                self.fail('blank')

        return super().run_validation(data)


class UniqueChoiceListField(serializers.ListField):
    def __init__(self, choices, *args, **kwargs):
        self.child = serializers.ChoiceField(choices=choices)
        self.allow_empty = True
        self.validators = [unique_entries]
        super().__init__(*args, **kwargs)
