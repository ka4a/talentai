import functools
from typing import List

from django.contrib.auth import get_user_model
from django.db.models.query_utils import Q
from django.http import Http404
from rest_access_policy import AccessPolicy
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from core import models as m
from core.constants import AgencyRole, ClientRole
from core.utils import has_profile, org_filter

User = get_user_model()


class BaseAccessPolicy(AccessPolicy):
    group_prefix = 'profile_type:'
    statements = [
        {
            'action': ['*'],
            'principal': ['*'],
            'effect': 'allow',
            'condition': 'is_organization_user',
        }
    ]

    def has_action_permission(self, request, view, action):
        statements = self.get_policy_statements(request, view)

        if len(statements) == 0:
            return False

        return self._evaluate_statements(statements, request, view, action)

    def get_user_group_values(self, user) -> List[str]:
        """
        Returns lowercase profile class name:
        e.g., ClientAdministrator -> clientadministrator
        """
        return list([getattr(user, 'profile_type', '') or ''])

    def user_must_be(self, request, view, action, field: str) -> bool:
        obj = view.get_object()
        return getattr(obj, field) == request.user

    def check_job_hiring_manager(self, job, user):
        return job._managers.filter(id=user.id).exists()

    def check_job_interviewer(self, job, user):
        return (
            job.interview_templates.filter(interviewer=user).exists()
            or job.proposals.filter(interviews__interviewer=user).exists()
        )

    def is_organization_user(self, request, view, action):
        return hasattr(request.user, 'profile') and request.user.profile is not None


def add_permissions(perms):
    """Add Permissions for separate ViewSet methods."""

    def decorator_func(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if args:
                view, request = args
            else:
                view = kwargs.get('view')
                request = kwargs.get('request')

            for perm in perms:
                if not perm.has_permission(request, view):
                    raise PermissionDenied(detail=getattr(perm, 'message', None))

            return func(*args, **kwargs)

        return wrapper

    return decorator_func


class IsOrganizationUser(permissions.BasePermission):
    """Only Users of the Organization: Agency or Client."""

    def has_permission(self, request, view):
        return hasattr(request.user, 'profile') and request.user.profile is not None


class IsAgencyUser(permissions.BasePermission):
    """Only Users from the Agency."""

    def has_permission(self, request, view):
        return hasattr(request.user, 'profile') and hasattr(
            request.user.profile, 'agency'
        )


class StaffAccessPolicy(BaseAccessPolicy):
    statements = [
        {
            'action': ['list', 'retrieve', 'photo'],
            'principal': ClientRole.all() + AgencyRole.all(),
            'effect': 'allow',
        },
        {
            'action': ['update', 'partial_update', 'upload_photo', 'delete_photo'],
            'principal': [ClientRole.ADMINISTRATOR, AgencyRole.ADMINISTRATOR,],
            'effect': 'allow',
        },
    ]


class IsOwnOrganization(permissions.BasePermission):
    """Create, update, patch and delete for own Organization only."""

    def has_object_permission(self, request, view, obj):
        """Permit only read actions for not own Organization."""
        if request.method != 'GET':
            return request.user.profile.org == obj

        return True


class RoleClientPermissions(permissions.BasePermission):
    """Class to manage Client permissions"""

    def has_permission(self, request, view):
        user = request.user
        if view.action in ['retrieve', 'list']:
            return True

        if view.action == 'create':
            return has_profile(user, 'agency')

        if view.action in ['update', 'partial_update']:
            return (
                has_profile(user, 'agency')
                or type(getattr(user, 'profile')) is m.TalentAssociate
            )

        return False


class HasRoleAbc(permissions.BasePermission):
    profile_type = None

    def has_permission(self, request, view):
        return (
            hasattr(request.user, 'profile')
            and type(request.user.profile) is self.profile_type
        )


class IsTalentAssociate(HasRoleAbc):
    profile_type = m.TalentAssociate


class IsAgencyAdministrator(HasRoleAbc):
    profile_type = m.AgencyAdministrator


class IsAgencyManager(HasRoleAbc):
    profile_type = m.AgencyManager


class IsHiringManager(HasRoleAbc):
    profile_type = m.HiringManager


class IsClientAdministrator(HasRoleAbc):
    profile_type = m.ClientAdministrator


class IsClientInternalRecruiter(HasRoleAbc):
    profile_type = m.ClientInternalRecruiter


class IsClientStandardUser(HasRoleAbc):
    profile_type = m.ClientStandardUser


class IsClientUser(permissions.BasePermission):
    """Only Users from the Client."""

    def has_permission(self, request, view):
        return hasattr(request.user, 'profile') and hasattr(
            request.user.profile, 'client'
        )


def get_permission_profiles_have_access(*args):
    class IsProfile(permissions.BasePermission):
        def has_permission(self, request, view):
            profile = getattr(request.user, 'profile', None)
            return profile and type(profile) in args

    return IsProfile


def get_permission_actions_available_to(actions, allowed_profiles):
    class ProfilesCanDoActions(permissions.BasePermission):
        def has_permission(self, request, view):
            if view.action in actions:
                profile = getattr(request.user, 'profile', None)
                return profile and type(profile) in allowed_profiles
            return True

    return ProfilesCanDoActions


LOCKING_FEE_STATUS_SET = {
    m.FeeStatus.APPROVED.key,
    m.FeeStatus.PENDING.key,
}


class FeePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        return (
            view.action in ['retrieve', 'get_file', 'upload_file']
            or obj.status not in LOCKING_FEE_STATUS_SET
            or isinstance(user.profile, (m.AgencyAdministrator, m.AgencyManager))
        )


class FeeSplitAllocationPermission(FeePermission):
    def has_object_permission(self, request, view, obj):
        # TODO: refactor when upload flow is fixed.
        # if isinstance(
        #     request.user.profile, (m.AgencyAdministrator, m.AgencyManager)
        # ) and view.action in ['upload_file', 'delete_file']:
        #     return obj.fee.status != m.FeeStatus.APPROVED.key
        # else:
        return super().has_object_permission(request, view, obj.fee)


class ClientBaseAccessPolicy(BaseAccessPolicy):
    """Base Access Policy for Client-specific viewsets"""

    statements = [
        {
            'action': ['*'],
            'principal': ['*'],
            'effect': 'allow',
            'condition': 'is_client_user',
        }
    ]

    def is_client_user(self, request, view, action):
        return hasattr(request.user, 'profile') and hasattr(
            request.user.profile, 'client'
        )


class AgencyBaseAccessPolicy(BaseAccessPolicy):
    """Base Access Policy for Agency-specific viewsets"""

    statements = [
        {
            'action': ['*'],
            'principal': ['*'],
            'effect': 'allow',
            'condition': 'is_agency_user',
        }
    ]

    def is_agency_user(self, request, view, action):
        return hasattr(request.user, 'profile') and hasattr(
            request.user.profile, 'agency'
        )


class ProposalsAccessPolicy(BaseAccessPolicy):
    """
    Admin
    - CRU any
    Internal Recruiter
    - CRU any
    Standard User
    - R if HM or interviewer in job
    """

    statements = [
        {
            'action': ['public_application', 'validate_public_application'],
            'principal': ['*'],
            'effect': 'allow',
        },
        {
            'action': [
                'create',
                'list',
                'retrieve',
                'update',
                'partial_update',
                'batch_create',
                'move_to_job',
                'quick_actions',
            ],
            'principal': [ClientRole.ADMINISTRATOR, ClientRole.INTERNAL_RECRUITER,],
            'effect': 'allow',
        },
        {
            'action': ['retrieve'],
            'principal': [ClientRole.STANDARD_USER],
            'effect': 'allow',
            'condition': 'is_proposal_job_assigned_to_user',
        },
        {
            'action': ['quick_actions'],
            'principal': [ClientRole.STANDARD_USER],
            'effect': 'allow',
            'condition': 'is_proposal_job_hiring_manager',
        },
        {
            'action': ['list'],
            'principal': [ClientRole.STANDARD_USER],
            'effect': 'allow',
        },
        {'action': ['*'], 'principal': AgencyRole.all(), 'effect': 'allow',},
    ]

    def is_proposal_job_hiring_manager(self, request, view, action):
        proposal = view.get_object()
        return self.check_job_hiring_manager(proposal.job, request.user)

    def is_proposal_job_assigned_to_user(self, request, view, action):
        proposal = view.get_object()
        return self.check_job_hiring_manager(
            proposal.job, request.user
        ) or self.check_job_interviewer(proposal.job, request.user)

    @classmethod
    def scope_queryset(cls, request, qs):
        qs = super().scope_queryset(request, qs)


class ProposalInterviewsAccessPolicy(BaseAccessPolicy):
    statements = [
        {
            'action': ['list', 'retrieve'],
            'principal': ['*'],
            'effect': 'allow',
            'condition': 'is_organization_user',
        },
        {
            'action': ['create'],
            'principal': [ClientRole.ADMINISTRATOR, ClientRole.INTERNAL_RECRUITER,],
            'effect': 'allow',
            'condition': 'is_organization_user',
        },
        {
            'action': ['update', 'partial_update', 'assessment'],
            'principal': [ClientRole.ADMINISTRATOR, ClientRole.INTERNAL_RECRUITER,],
            'effect': 'allow',
            'condition': 'is_same_organization_as_proposal',
        },
        {
            'action': ['assessment'],
            'principal': ['*'],
            'effect': 'allow',
            'condition': [
                'user_must_be:interviewer',
                'is_same_organization_as_proposal',
            ],
        },
        {
            'action': ['destroy'],
            'principal': [ClientRole.ADMINISTRATOR, ClientRole.INTERNAL_RECRUITER,],
            'effect': 'allow',
            'condition': [
                'is_same_organization_as_proposal',
                'is_not_current_interview',
            ],
        },
        {'action': ['*'], 'principal': AgencyRole.all(), 'effect': 'allow',},
    ]

    def is_not_current_interview(self, request, view, action):
        interview = view.get_object()
        return not interview.proposal.current_interview == interview

    def is_same_organization_as_proposal(self, request, view, action):
        proposal_interview = view.get_object()
        return request.user.org == proposal_interview.proposal.job.organization


class JobsAccessPolicy(BaseAccessPolicy):
    """
    Admin
    - CRU any
    Internal Recruiter
    - CR any
    - U if creator or assigned
    Standard User
    - R if HM or interviewer
    """

    statements = [
        {
            'action': [
                'create',
                'list',
                'retrieve',
                'update',
                'partial_update',
                'assign_member',
                'withdraw_member',
                'import_longlist',
            ],
            'principal': [ClientRole.ADMINISTRATOR],
            'effect': 'allow',
        },
        {
            'action': ['create', 'list', 'retrieve', 'import_longlist',],
            'principal': [ClientRole.INTERNAL_RECRUITER],
            'effect': 'allow',
        },
        {
            'action': ['update', 'partial_update', 'assign_member', 'withdraw_member',],
            'principal': [ClientRole.INTERNAL_RECRUITER],
            'effect': 'allow',
            'condition': ['is_assigned_to_job_or_creator'],
        },
        {
            'action': ['list'],
            'principal': [ClientRole.STANDARD_USER],
            'effect': 'allow',
        },
        {
            'action': [
                'retrieve',
                'get_private_job_posting',
                'get_career_site_job_posting',
            ],
            'principal': [ClientRole.STANDARD_USER],
            'effect': 'allow',
            'condition_expression': ['(is_job_hiring_manager or is_job_interviewer)'],
        },
        {'action': ['*'], 'principal': AgencyRole.all(), 'effect': 'allow',},
    ]

    def is_assigned_to_job_or_creator(self, request, view, action):
        job = view.get_object()
        return job.created_by == request.user or request.user in job.recruiters.all()

    def is_job_hiring_manager(self, request, view, action):
        job = view.get_object()
        return self.check_job_hiring_manager(job, request.user)

    def is_job_interviewer(self, request, view, action):
        job = view.get_object()
        return self.check_job_interviewer(job, request.user)


class JobPostingAccessPolicy(BaseAccessPolicy):
    """
    Admin
    - CRU any
    Internal Recruiter
    - CR any
    - U if creator or assigned
    Standard User
    - R if HM or interviewer
    """

    statements = [
        {
            'action': ['create', 'list', 'retrieve', 'update', 'partial_update',],
            'principal': [ClientRole.ADMINISTRATOR, ClientRole.INTERNAL_RECRUITER,],
            'effect': 'allow',
        },
        {
            'action': ['list', 'retrieve'],
            'principal': [ClientRole.STANDARD_USER],
            'effect': 'allow',
        },
    ]


class JobFilesAccessPolicy(BaseAccessPolicy):
    statements = [
        {
            'action': ['create'],
            'principal': ['*'],
            'effect': 'allow',
            'condition': ['is_organization_user', 'is_creating_for_own_organization'],
        },
        {
            'action': ['retrieve', 'list', 'destroy', 'update', 'partial_update'],
            'principal': ['*'],
            'effect': 'allow',
            'condition': ['is_organization_user', 'is_same_organization_as_job'],
        },
    ]

    def is_same_organization_as_job(self, request, view, action):
        job_file = view.get_object()
        return request.user.org == job_file.job.organization

    def is_creating_for_own_organization(self, request, view, action):
        job = request.data.get('job')
        if not job:
            raise Http404
        return m.Job.objects.filter(
            Q(pk=job) & Q(org_filter(request.user.org))
        ).exists()


class CandidatesAccessPolicy(BaseAccessPolicy):
    """
    Admin
    - CRU any
    Internal Recruiter
    - CRU any
    - except archive_candidate action (should be owner or creator)
    Standard User
    - R if can view job
    """

    statements = [
        {
            'action': [
                'create',
                'validate_create',
                'validate_partial_create',
                'list',
                'retrieve',
                'update',
                'validate_update',
                'partial_update',
                'validate_partial_update',
                'check_duplication',
                'linkedin_data_check_duplication',
                'linkedin_url_check_proposed',
                'archive_candidate',
                'restore_candidate',
            ],
            'principal': [ClientRole.ADMINISTRATOR],
            'effect': 'allow',
        },
        {
            'action': [
                'create',
                'validate_create',
                'validate_partial_create',
                'list',
                'retrieve',
                'update',
                'validate_update',
                'partial_update',
                'validate_partial_update',
                'check_duplication',
                'linkedin_data_check_duplication',
                'linkedin_url_check_proposed',
                'restore_candidate',
            ],
            'principal': [ClientRole.INTERNAL_RECRUITER],
            'effect': 'allow',
        },
        {
            'action': ['archive_candidate'],
            'principal': [ClientRole.INTERNAL_RECRUITER],
            'effect': 'allow',
            'condition': ['is_candidate_owner_or_creator'],
        },
        {
            'action': ['retrieve'],
            'principal': [ClientRole.STANDARD_USER],
            'effect': 'allow',
            'condition': ['is_candidate_applied_to_assigned_job'],
        },
        {
            'action': ['list'],
            'principal': [ClientRole.STANDARD_USER],
            'effect': 'allow',
        },
        {'action': ['*'], 'principal': AgencyRole.all(), 'effect': 'allow',},
    ]

    def is_candidate_applied_to_assigned_job(self, request, view, action):
        """
        Candidate applied to job I can view
        """
        candidate = view.get_object()
        return request.user.profile.apply_own_candidates_filter(
            m.Candidate.objects.filter(id=candidate.id)
        ).exists()

    def is_candidate_owner_or_creator(self, request, view, action):
        candidate = view.get_object()
        return candidate.owner == request.user or candidate.created_by == request.user


class CandidateFilesAccessPolicy(BaseAccessPolicy):
    statements = [
        {'action': ['public_upload'], 'principal': ['*'], 'effect': 'allow',},
        {
            'action': ['*'],
            'principal': ['*'],
            'effect': 'allow',
            'condition': 'is_organization_user',
        },
    ]


class CandidateCommentsAccessPolicy(BaseAccessPolicy):
    statements = [
        {
            'action': ['delete'],
            'principal': ['*'],
            'effect': 'allow',
            'condition': 'user_must_be:author',
        },
        {
            'action': ['create', 'list', 'retrieve'],
            'principal': ['*'],
            'effect': 'allow',
            'condition': 'is_organization_user',
        },
    ]


class ManagersAccessPolicy(BaseAccessPolicy):
    statements = [
        {
            'action': ['list', 'invite'],
            'principal': [ClientRole.ADMINISTRATOR, ClientRole.INTERNAL_RECRUITER,],
            'effect': 'allow',
        },
        {
            'action': ['assign', 'remove_from_job'],
            'principal': [ClientRole.ADMINISTRATOR, ClientRole.INTERNAL_RECRUITER,],
            'effect': 'allow',
            'condition': ['is_user_same_organization', 'is_job_same_organization'],
        },
        {'action': ['*'], 'principal': AgencyRole.all(), 'effect': 'allow',},
    ]

    def is_user_same_organization(self, request, view, action):
        user = request.data.get('user')
        if user:
            return request.user.profile.client.members.filter(pk=user).exists()
        return False

    def is_job_same_organization(self, request, view, action):
        job = request.data.get('job')
        if job:
            return (
                request.user.profile.org
                == m.Job.objects.filter(pk=job).first().organization
            )
        return False


class ProposalQuestionAccessPolicy(BaseAccessPolicy):
    statements = [
        {
            'action': ['list', 'retrieve'],
            'principal': ClientRole.all(),
            'effect': 'allow',
        },
        {
            'action': ['update', 'partial_update'],
            'principal': [ClientRole.ADMINISTRATOR, ClientRole.INTERNAL_RECRUITER,],
            'effect': 'allow',
        },
    ]


class NoteActivityAccessPolicy(BaseAccessPolicy):
    statements = [
        {
            'action': ['list', 'create', 'update', 'partial_update', 'delete'],
            'principal': [ClientRole.ADMINISTRATOR,],
            'effect': 'allow',
        },
        {
            'action': ['list', 'create'],
            'principal': ClientRole.non_admin_roles(),
            'effect': 'allow',
        },
        {
            'action': ['update', 'partial_update', 'delete'],
            'principal': ClientRole.non_admin_roles(),
            'effect': 'allow',
            'condition': ['is_note_author'],
        },
    ]

    def is_note_author(self, request, view, action):
        note = view.get_object()
        return note.author == request.user
