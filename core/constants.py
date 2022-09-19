import enum

from django.utils.translation import gettext_lazy as _


class NotSet:
    def __repr__(self):
        return "NOT_SET"


NOT_SET = NotSet()

VALIDATE_ACTIONS = [
    'validate_create',
    'validate_partial_create',
    'validate_update',
    'validate_partial_update',
]
CREATE_ACTIONS = ['create']
DELETE_ACTIONS = ['destroy']
UPDATE_ACTIONS = ['update', 'partial_update']
CREATE_DELETE_ACTIONS = CREATE_ACTIONS + DELETE_ACTIONS
CREATE_UPDATE_ACTIONS = CREATE_ACTIONS + UPDATE_ACTIONS
CREATE_UPDATE_VALIDATE_ACTIONS = CREATE_UPDATE_ACTIONS + VALIDATE_ACTIONS

CANDIDATE_FILE_TYPES = ['resume', 'photo', 'resume_ja', 'cv_ja']


class StatusEnum(enum.Enum):
    @property
    def key(self):
        return self.name.lower()

    @property
    def choice(self):
        return (self.key, self.value)

    @property
    def dropdown_option(self):
        return {'value': self.key, 'label': self.value}

    @classmethod
    def get_keys(cls):
        return [item.key for item in cls]

    @classmethod
    def get_choices(cls):
        return tuple(item.choice for item in cls)

    @classmethod
    def get_dropdown_options(cls):
        return tuple(item.dropdown_option for item in cls)

    @classmethod
    def get_db_field_length(cls):
        return max(*(len(item.key) for item in cls))

    @classmethod
    def get_key_by_value(cls, value):
        for item in cls:
            if item.value == value:
                return item.key

        return ''


class ClientRole(str, enum.Enum):
    ADMINISTRATOR = 'profile_type:clientadministrator'
    INTERNAL_RECRUITER = 'profile_type:clientinternalrecruiter'
    STANDARD_USER = 'profile_type:clientstandarduser'

    @classmethod
    def all(cls):
        return list(cls)

    @classmethod
    def non_admin_roles(cls):
        return [cls.INTERNAL_RECRUITER, cls.STANDARD_USER]


class AgencyRole(str, enum.Enum):
    ADMINISTRATOR = 'profile_type:agencyadministrator'
    MANAGER = 'profile_type:agencymanager'
    RECRUITER = 'profile_type:recruiter'

    @classmethod
    def all(cls):
        return list(cls)


class NotificationLinkText(enum.Enum):
    PROPOSAL_DETAIL = _('View Application')
    JOB_DETAIL = _('View Job')
    ACTIVITY_DETAIL = _('View Activity')


class ProposalStatusStage(StatusEnum):
    ASSOCIATED = _('Associated')
    PRE_SCREENING = _('Pre-Screening')
    SCREENING = _('Screening')
    SUBMISSIONS = _('Submissions')
    INTERVIEWING = _('Interviewing')
    OFFERING = _('Offering')
    HIRED = _('Hired')

    @classmethod
    def get_longlist_groups(cls):
        return [
            cls.ASSOCIATED,
            cls.PRE_SCREENING,
        ]

    @classmethod
    def get_longlist_keys(cls):
        return [item.key for item in cls.get_longlist_groups()]

    @classmethod
    def get_shortlist_groups(cls):
        return [
            cls.SUBMISSIONS,
            cls.SCREENING,
            cls.INTERVIEWING,
            cls.OFFERING,
            cls.HIRED,
        ]

    @classmethod
    def get_shortlist_keys(cls):
        return [item.key for item in cls.get_shortlist_groups()]


class ProposalStatusGroup(StatusEnum):
    # associated
    ASSOCIATED_TO_JOB = _('Associated to Job')
    APPLIED_BY_CANDIDATE = _('Applied by Candidate')
    SUITABLE = _('Suitable')
    # screening
    CONTACTED = _('Contacted')
    QUALIFIED = _('Qualified')
    # submissions
    SUBMITTED_TO_HIRING_MANAGER = _('Submitted to Hiring Manager')
    # interviewing
    INTERVIEWING = _('Interviewing')
    # offering
    PENDING_HIRING_DECISION = _('Pending Hiring Decision')
    OFFER_TO_BE_PREPARED = _('Offer To Be Prepared')
    PENDING_OFFER_ACCEPTANCE = _('Pending Offer Acceptance')
    # hired
    PENDING_START = _('Pending Start')
    STARTED = _('Started')

    @classmethod
    def get_stage_keys(cls, stage):
        if stage not in ProposalStatusStage.get_keys():
            return []
        stage_statuses = getattr(cls, f'{stage}_statuses')()
        return [item.key for item in stage_statuses]

    @classmethod
    def associated_statuses(cls):
        return [
            cls.ASSOCIATED_TO_JOB,
            cls.APPLIED_BY_CANDIDATE,
            cls.SUITABLE,
        ]

    @classmethod
    def pre_screening_statuses(cls):
        return []

    @classmethod
    def submissions_statuses(cls):
        return [
            cls.SUBMITTED_TO_HIRING_MANAGER,
        ]

    @classmethod
    def screening_statuses(cls):
        return [
            cls.CONTACTED,
            cls.QUALIFIED,
        ]

    @classmethod
    def interviewing_statuses(cls):
        return [
            cls.INTERVIEWING,
        ]

    @classmethod
    def offering_statuses(cls):
        return [
            cls.PENDING_HIRING_DECISION,
            cls.OFFER_TO_BE_PREPARED,
            cls.PENDING_OFFER_ACCEPTANCE,
        ]

    @classmethod
    def hired_statuses(cls):
        return [
            cls.PENDING_START,
            cls.STARTED,
        ]

    @classmethod
    def get_client_org_status_keys(cls):
        return [item.key for item in cls]

    @classmethod
    def get_agency_org_status_keys(cls):
        return [item.key for item in cls]


class ProposalInterviewStatus(StatusEnum):
    TO_BE_SCHEDULED = _('To Be Scheduled')
    PENDING = _('Pending Candidate Confirmation')
    SCHEDULED = _('Scheduled')
    REJECTED = _('To Be Rescheduled')
    CANCELED = _('Canceled')
    SKIPPED = _('Skipped')
    COMPLETED = _('Completed')

    @classmethod
    def get_closed_statuses(cls):
        return [cls.REJECTED, cls.CANCELED, cls.COMPLETED]

    @classmethod
    def get_closed_status_keys(cls):
        return [item.key for item in cls.get_closed_statuses()]


class QuickActionVerb(StatusEnum):
    CHANGE_STATUS = 'Change Status'
    REJECT = 'Reject Candidate'
    # Interviewing actions
    SCHEDULE = 'Schedule Interview'
    RESEND = 'Resend Schedule'
    ASSESS = 'Add Assessment'
    PROCEED = 'Proceed'


# function is used for scoping intermediate constants
def init_default_client_quick_action_mapping():
    to_suitable = {
        'action': QuickActionVerb.CHANGE_STATUS.key,
        'label_en': 'Suitable',
        'label_ja': '合致',
        'to_status': {'group': ProposalStatusGroup.SUITABLE.key},
    }

    to_contacted = {
        'action': QuickActionVerb.CHANGE_STATUS.key,
        'label_en': 'Contacted',
        'label_ja': '連絡済',
        'to_status': {'group': ProposalStatusGroup.CONTACTED.key},
    }

    to_qualified = {
        'action': QuickActionVerb.CHANGE_STATUS.key,
        'label_en': 'Qualified',
        'label_ja': '募集要件に合致',
        'to_status': {'group': ProposalStatusGroup.QUALIFIED.key},
    }

    submit_to_hiring_manager = {
        'action': QuickActionVerb.CHANGE_STATUS.key,
        'label_en': 'Submit to Hiring Manager',
        'label_ja': 'Hiring Managerに提案',
        'to_status': {'group': ProposalStatusGroup.SUBMITTED_TO_HIRING_MANAGER.key},
    }

    approved_by_hiring_manager_to_interview = {
        'action': QuickActionVerb.CHANGE_STATUS.key,
        'label_en': 'Approved by Hiring Manager',
        'label_ja': 'Hiring Managerによって承認済',
        'to_status': {'group': ProposalStatusGroup.INTERVIEWING.key},
    }

    approved_by_hiring_manager_to_hire = {
        'action': QuickActionVerb.CHANGE_STATUS.key,
        'label_en': 'Approved by Hiring Manager',
        'label_ja': 'Hiring Managerによって承認済',
        'to_status': {'group': ProposalStatusGroup.PENDING_HIRING_DECISION.key},
    }

    schedule_interview = {
        'action': QuickActionVerb.SCHEDULE.key,
        'label_en': 'Schedule Interview',
        'label_ja': '面接の日程を調整する',
    }

    resend_interview_proposal = {
        'action': QuickActionVerb.RESEND.key,
        'label_en': 'Resend Interview Proposal',
        'label_ja': '面接の招待を再送信',
    }

    submit_assessment = {
        'action': QuickActionVerb.ASSESS.key,
        'label_en': 'Submit Assessment',
        'label_ja': '評価を提出',
    }

    proceed = {
        'action': QuickActionVerb.PROCEED.key,
        'label_en': 'Proceed',
        'label_ja': '進行',
    }

    decide_to_offer = {
        'action': QuickActionVerb.CHANGE_STATUS.key,
        'label_en': 'Decided to Offer',
        'label_ja': '内定オファー',
        'to_status': {'group': ProposalStatusGroup.OFFER_TO_BE_PREPARED.key},
    }

    present_the_offer = {
        'action': QuickActionVerb.CHANGE_STATUS.key,
        'label_en': 'Presented the Offer',
        'label_ja': 'オファー送信済',
        'to_status': {'group': ProposalStatusGroup.PENDING_OFFER_ACCEPTANCE.key},
    }

    offer_accepted = {
        'action': QuickActionVerb.CHANGE_STATUS.key,
        'label_en': 'Offer Accepted',
        'label_ja': 'オファー受理',
        'to_status': {'group': ProposalStatusGroup.PENDING_START.key},
    }

    reject_candidate = {
        'action': QuickActionVerb.REJECT.key,
        'label_en': 'Reject Candidate',
        'label_ja': '候補者を見送り',
    }

    # condition based on application. condition is resolved using Q expressions
    # action is dict
    return [
        {
            'condition': {'status__group': ProposalStatusGroup.ASSOCIATED_TO_JOB.key},
            'actions': [to_suitable, reject_candidate],
        },
        {
            'condition': {
                'status__group': ProposalStatusGroup.APPLIED_BY_CANDIDATE.key
            },
            'actions': [to_suitable, reject_candidate],
        },
        {
            'condition': {'status__group': ProposalStatusGroup.SUITABLE.key},
            'actions': [to_contacted, reject_candidate],
        },
        {
            'condition': {'status__group': ProposalStatusGroup.CONTACTED.key},
            'actions': [to_qualified, reject_candidate],
        },
        {
            'condition': {'status__group': ProposalStatusGroup.QUALIFIED.key},
            'actions': [submit_to_hiring_manager, reject_candidate],
        },
        {
            'condition': {
                'status__group': ProposalStatusGroup.SUBMITTED_TO_HIRING_MANAGER.key,
                'current_interview__isnull': False,
            },
            'actions': [approved_by_hiring_manager_to_interview, reject_candidate],
        },
        {
            'condition': {
                'status__group': ProposalStatusGroup.SUBMITTED_TO_HIRING_MANAGER.key,
                'current_interview__isnull': True,
            },
            'actions': [approved_by_hiring_manager_to_hire, reject_candidate],
        },
        {
            'condition': {
                'status__stage': ProposalStatusStage.INTERVIEWING.key,
                'current_interview__current_schedule__status__in': [
                    ProposalInterviewStatus.TO_BE_SCHEDULED.key,
                    # In that case "To be rescheduled" is shown to user
                    ProposalInterviewStatus.CANCELED.key,
                    ProposalInterviewStatus.REJECTED.key,
                ],
            },
            'actions': [schedule_interview, reject_candidate],
        },
        {
            'condition': {
                'status__stage': ProposalStatusStage.INTERVIEWING.key,
                'current_interview__current_schedule__status': ProposalInterviewStatus.PENDING.key,
            },
            'actions': [resend_interview_proposal, reject_candidate],
        },
        {
            'condition': {
                'status__stage': ProposalStatusStage.INTERVIEWING.key,
                'current_interview__current_schedule__status': ProposalInterviewStatus.SCHEDULED.key,
                'current_interview__assessment__isnull': True,
            },
            'actions': [submit_assessment, reject_candidate],
        },
        {
            'condition': {
                'status__stage': ProposalStatusStage.INTERVIEWING.key,
                'current_interview__current_schedule__status': ProposalInterviewStatus.SKIPPED.key,
            },
            'actions': [proceed, reject_candidate],
        },
        {
            'condition': {
                'status__stage': ProposalStatusStage.INTERVIEWING.key,
                'current_interview__current_schedule__status': ProposalInterviewStatus.SCHEDULED.key,
                'current_interview__assessment__isnull': False,
            },
            'actions': [proceed, reject_candidate],
        },
        {
            'condition': {
                'status__group': ProposalStatusGroup.PENDING_HIRING_DECISION.key
            },
            'actions': [decide_to_offer, reject_candidate],
        },
        {
            'condition': {
                'status__group': ProposalStatusGroup.OFFER_TO_BE_PREPARED.key
            },
            'actions': [present_the_offer, reject_candidate],
        },
        {
            'condition': {
                'status__group': ProposalStatusGroup.PENDING_OFFER_ACCEPTANCE.key
            },
            'actions': [offer_accepted, reject_candidate],
        },
    ]


DEFAULT_CLIENT_QUICK_ACTION_MAPPING = init_default_client_quick_action_mapping()

DEFAULT_AGENCY_QUICK_ACTION_MAPPING = []
