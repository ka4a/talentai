from core.constants import NotificationLinkText, QuickActionVerb
import os
import secrets
import re
import time
import pytz
import ics
from abc import abstractmethod
from enum import Enum
from ics.parse import ContentLine
from uuid import uuid4

import reversion
from django.apps import apps
from django.conf import settings
from django.contrib.admin.models import ACTION_FLAG_CHOICES, LogEntry as AdminLogEntry
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.db.utils import IntegrityError
from django.db.models import Q, Case, When
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from gfklookupwidget.fields import GfkLookupField
from phonenumber_field.modelfields import PhoneNumberField
from djmoney.models.fields import MoneyField as DjangoMoneyField
from ordered_model.models import OrderedModel


from core.constants import (
    ProposalStatusGroup,
    StatusEnum,
    ProposalStatusStage,
)
from core.tasks import send_email
from core.utils import (
    camelize_str,
    datetime_str,
    parse_linkedin_slug,
    get_trans,
    get_unique_emails_filter,
    org_filter,
    get_country_list,
    get_country_name,
)


class MoneyField(DjangoMoneyField):
    def __init__(self, **kwargs):
        kwargs.update(max_digits=19, decimal_places=0)
        super().__init__(**kwargs)


def get_max_choice_length(choices):
    return max(*(len(choice[0]) for choice in choices))


SALARY_PER_CHOICES = (
    ('year', _('Year')),
    ('month', _('Month')),
    ('week', _('Week')),
    ('day', _('Day')),
    ('hour', _('Hour')),
)


PROPOSAL_STATUS_GROUP_CHOICES = (
    # shortlist groups
    ('new', _('New')),
    ('proceeding', _('Proceeding')),
    ('approved', _('CV approved')),
    ('rejected', _('CV rejected')),
    ('interviewing', _('Interviewing')),
    ('offer', _('Offer')),
    ('offer_accepted', _('Offer Accepted')),
    ('offer_declined', _('Offer Declined')),
    ('candidate_quit', _('Candidate Quits Process')),
    ('closed', _('Closed')),
    # longlist groups
    ('not_contacted', _('Not Contacted')),
    ('not_interested', _('Contacted - Not Interested')),
    ('pending_interview', _('Contacted - Pending Interview')),
    ('interested', _('Interviewed - Interested')),
    ('not_interested_after_interview', _('Interviewed - Not Interested')),
    ('pending_feedback', _('Interviewed - Pending feedback')),
    ('not_suitable', _('Interviewed - Not Suitable')),
)

SHORTLIST_PROPOSAL_STATUS_GROUPS = [
    'new',
    'proceeding',
    'approved',
    'rejected',
    'interviewing',
    'offer',
    'offer_accepted',
    'offer_declined',
    'candidate_quit',
    'closed',
]

LONGLIST_PROPOSAL_STATUS_GROUPS = [
    'not_contacted',
    'interested',
    'not_interested',
    'not_interested_after_interview',
    'pending_feedback',
    'pending_interview',
    'not_suitable',
]


class ProposalCommentTypes(object):
    STATUS_CHANGED = _('Proposal status changed to "{status}"')
    SHORTLISTED = _('Shortlisted')
    LONGLISTED = _('Longlisted')
    INTERVIEW_CONFIRMED = _(
        'An interview on {start_at:%a, %b %d - %H:%M} - {end_at:%H:%M} has been arranged.'
    )
    INTERVIEW_CREATED = _('The candidate has been invited to an interview')
    INTERVIEW_CANCELED = _('A scheduled interview has been canceled')
    INTERVIEW_REJECTED = _(
        '{candidate} has rejected all proposed time slots for the interview.'
    )
    PLACED = _('The candidate has been placed')
    REJECTED = _('Rejected')


def get_proposal_comment(comment, *args, **kwargs):
    return {
        'text_en': get_trans('en', comment).format(*args, **kwargs),
        'text_ja': get_trans('ja', comment).format(*args, **kwargs),
    }


class StatusModel(models.Model):
    name = models.CharField(max_length=256, unique=True)

    @classmethod
    def get_dropdown_options(cls):
        return tuple({'value': s.id, 'label': s.name} for s in cls.objects.all())

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class ProposalStatusSubStage(StatusEnum):
    FIRST_INTERVIEW = _('First Interview')
    IN_PROCESS = _('In Process')
    FINAL_INTERVIEW = _('Final Interview')


class ContractStatus(StatusEnum):
    AGENCY_INVITED = _('Agency Invited')
    PENDING = _('Pending')
    INITIATED = _('Initiated')
    REJECTED = _('Rejected')
    EXPIRED = _('Expired')


class JobStatus(StatusEnum):
    OPEN = _('Open')
    ON_HOLD = _('On Hold')
    FILLED = _('Filled')
    CLOSED = _('Closed')


class ProposalDealStages(StatusEnum):
    FIRST_ROUND = _('First round')
    INTERMEDIATE_ROUND = _('Intermediate round')
    FINAL_ROUND = _('Final round')
    OFFER = _('Offer')
    OUT_OF = _('Out of deal pipeline')

    @classmethod
    def get_dropdown_options(cls):
        return tuple(
            {'value': item.key, 'label': item.value}
            for item in cls
            if item is not cls.OUT_OF
        )


DEFAULT_CONTRACT_STATUS = ContractStatus.AGENCY_INVITED.key
CONTRACT_DEFAULT_INVITATION_DURATION = 14  # days
CONTRACT_STATUS_CHOICES = ContractStatus.get_choices()
CONTRACT_STATUSES_ALLOW_JOBS = (
    ContractStatus.INITIATED.key,
    ContractStatus.PENDING.key,
)
CONTRACT_STATUSES_AGENCY_ALLOWED_TO_SET = (
    ContractStatus.PENDING.key,
    ContractStatus.REJECTED.key,
)
CONTRACT_STATUSES_CAN_EXPIRE = (
    ContractStatus.AGENCY_INVITED.key,
    ContractStatus.PENDING.key,
)

DEFAULT_JOB_STATUS = JobStatus.OPEN.key
JOB_STATUS_CHOICES = JobStatus.get_choices()

JOB_STATUSES_CLOSED = (
    JobStatus.FILLED.key,
    JobStatus.CLOSED.key,
)

COUNTRY_CHOICES = [(c['code'], c['name']) for c in get_country_list('en')]


class ClientType(StatusEnum):
    KEY_ACCOUNT = _('Key account')
    AUXILIARY_ACCOUNT = _('Auxiliary account')
    NEW_ACCOUNT = _('New account')


class Industry(StatusEnum):
    ARCHITECTURE_AND_CONSTRUCTION = _('Architecture & Construction')
    AUTOMOBILE_OR_AVIATION_AND_AEROSPACE = _('Automobile / Aviation & Aerospace')
    BANKING_AND_FINANCIAL_SERVICES = _('Banking & Financial Services')
    CONSULTING = _('Consulting')
    EDUCATION_OR_TRAINING_OR_COACHING = _('Education / Training / Coaching')
    ELECTRONIC_GOODS = _('Electronic Goods')
    ENERGY_AND_NATURAL_RESOURCES = _('Energy & Natural Resources')
    FINTECH = _('Fintech')
    FOOD_AND_BEVERAGE_OR_FMCG = _('Food & Beverage / FMCG')
    HARDWARE = _('Hardware')
    HEALTHCARE_OR_PHARMACEUTICAL_OR_LIFE_SCIENCES = _(
        'Healthcare / Pharmaceutical / Life Sciences'
    )
    IT_OR_TECHNOLOGY_OR__DIGITAL_AND_TELECOM = _('IT / Technology/ Digital & Telecom')
    INSURANCE = _('Insurance')
    LEGAL_AND_COMPLIANCE = _('Legal & Compliance')
    LEISURE_OR_HOSPITALITY_OR_RESTAURANTS_OR_TRAVEL_AND_TOURISM = _(
        'Leisure / Hospitality / Restaurants / Travel & Tourism'
    )
    MANUFACTURING_OR_INDUSTRIAL = _('Manufacturing / Industrial')
    MEDIA_OR_ART_AND_ENTERTAIMENT_OR_COMMUNICATION_OR_AGENCY = _(
        'Media / Art & Entertaiment / Communication / Agency'
    )
    PUBLIC_SECTOR = _('Public Sector')
    REAL_ESTATE_OR_PROPERTY_AND_CONSTRUCTION = _(
        'Real Estate / Property & Construction'
    )
    RECRUITMENT = _('Recruitment')
    RETAIL_OR_FASHION_OR_LUXURY_OR_CONSUMER_GOODS = _(
        'Retail / Fashion / Luxury / Consumer Goods'
    )
    SERVICES = _('Services')
    SOFTWARE = _('Software')
    TRANSPORTATION_OR_SHIPPING_OR_LOGISTICS = _('Transportation / Shipping / Logistics')


class JobContractTypes(StatusEnum):
    MTS = _('MTS')
    RETAINER = _('Retainer')
    CONTINGENT = _('Contingent')


class ContractType(StatusEnum):
    @property
    def dropdown_option(self):
        return {
            'value': self.key,
            'label': self.value,
            'for_placement': self.key in PLACEMENT_CONTRACT_TYPE_SET,
            'for_no_placement': self.key in NO_PLACEMENT_CONTRACT_TYPE_SET,
        }

    RETAINER = _('Retainer')
    MTS = _('MTS')
    CONTINGENT = _('Contingent')


PLACEMENT_CONTRACT_TYPE_SET = {
    ContractType.RETAINER.key,
    ContractType.MTS.key,
    ContractType.CONTINGENT.key,
}

NO_PLACEMENT_CONTRACT_TYPE_SET = {
    ContractType.MTS.key,
    ContractType.CONTINGENT.key,
}


class BillDescription(StatusEnum):
    AF = _('AF')
    SLF = _('SLF')
    FF = _('FF')
    MONTHLY = _('Monthly')
    INTERNAL = _('Internal')
    EXTERNAL = _('External')
    PLACEMENT_FEE = _('Placement Fee')

    @property
    def dropdown_option(self):
        return {
            'value': self.key,
            'label': self.value,
            'for_placement': self.key in BILL_DESCRIPTIONS_FOR_PLACEMENT,
        }

    @classmethod
    def get_available_for_contract(cls, contract_type):
        if contract_type == ContractType.RETAINER.key:
            yield cls.AF
            yield cls.SLF
            yield cls.FF
            return
        if contract_type == ContractType.MTS.key:
            yield cls.MONTHLY
            yield cls.INTERNAL
            yield cls.EXTERNAL
            return
        if contract_type == ContractType.CONTINGENT.key:
            yield cls.PLACEMENT_FEE
            return

    @classmethod
    def get_choices(cls, contract_type=None):
        if contract_type is None:
            return super().get_choices()

        return tuple(
            item.choice for item in cls.get_available_for_contract(contract_type)
        )


BILL_DESCRIPTIONS_FOR_PLACEMENT = [
    BillDescription.FF.key,
    BillDescription.INTERNAL.key,
    BillDescription.EXTERNAL.key,
    BillDescription.PLACEMENT_FEE.key,
]


class SkillDomain(StatusModel):
    pass


class JobWorkExperience(StatusEnum):
    NONE = _('None')
    ZERO_ONE_YEAR = _('0-1 year')
    ONE_TWO_YEARS = _('1-2 years')
    TWO_FIVE_YEARS = _('2-5 years')
    FIVE_TEN_YEARS = _('5-10 years')
    TEN_PLUS_YEARS = _('10+ years')


class JobReasonForOpening(StatusEnum):
    REPLACEMENT = _('Replacement')
    NEW = _('New')


class JobEducationalLevel(StatusEnum):
    NONE = _('None')
    HIGHSCHOOL = _('High School Diploma')
    BACHELORS = _('Bachelor\'s Degree')
    MASTERS = _('Master\'s Degree')
    PHD = _('PhD')


class JobFlexitimeEligibility(StatusEnum):
    ELIGIBLE = _('Eligible')
    NOT_ELIGIBLE = _('Not Eligible')


class JobSocialInsurances(StatusEnum):
    HEALTH = _('Health Insurance')
    EMPLOYMENT = _('Employment Insurance')
    WELFARE_PENSION = _('Welfare Pension Insurance')
    ACCIDENT_COMPENSATION = _('Workers Accident Compensation Insurance')


class JobOtherBenefits(StatusEnum):
    VISA = _('Visa Sponsorship')
    RELOCATION = _('Relocation Assistance')
    WELLNESS = _('Gym / Wellness Membership')
    COFFEE = _('Free Coffee')


class JobEmploymentType(StatusEnum):
    PERMANENT = _('Permanent Employee')
    PARTTIME = _('Part Time Employee')
    FIXEDTERM = _('Fixed Term Contract Employee')
    DISPATCH = _('Dispatch')
    FREELANCE = _('Freelance')


class JobTeleworkEligibility(StatusEnum):
    ONSITE = _('On Site Only')
    POSSIBLE = _('Remote Possible')
    REMOTE = _('Remote Only')


class NotificationType:
    """
    email_text - is the plaintext form of the email. For customized emails,
        use templates at `core/templates/notifications/`.
    """

    def __init__(
        self,
        group,
        setting_label,
        text,
        email_text=None,
        email_subject=_('Notification'),
    ):
        self.group = group
        self.setting_label = setting_label
        self.text = text
        self.email_text = email_text if email_text else text
        self.email_subject = email_subject


class NotificationTypeFactory:
    @staticmethod
    def contract_initiated(specific_text, actor_type):
        return NotificationType(
            'n/a',
            _('Your contract with the {0} has been initiated.').format(actor_type),
            _(
                'You have successfully initiated a contract with {{actor.name}}.\n'
                '{0}'
            ).format(specific_text),
        )

    @staticmethod
    def job_access_revoked(specific_text):
        return NotificationType(
            'n/a',
            _('Job access has been removed'),
            _(
                '{{actor.name}} has no longer access to the jobs you shared.\n' '{0}'
            ).format(specific_text),
        )


class NotificationTypeEnum(Enum):
    """key - group, label on the settings page, text, email text, email subject"""

    PLACEMENT_FEE_PENDING = NotificationType(
        'n/a',
        _('Candidate placement is submitted for approval'),
        _(
            '{action_object.client.name} - {action_object.candidate.name}\'s'
            ' placement form'
            ' has been submitted for your approval'
        ),
    )

    PLACEMENT_FEE_PENDING_REMINDER = NotificationType(
        'n/a',
        _('Candidate placement is sent to revision'),
        _(
            '{action_object.client.name} - {action_object.candidate.name}\'s'
            ' placement form'
            ' is waiting for your approval'
        ),
    )

    PLACEMENT_FEE_DRAFT = NotificationType(
        'n/a',
        _('Candidate placement is set as draft'),
        _(
            '{action_object.client.name} - {action_object.candidate.name}\'s'
            ' placement form'
            ' has been saved as draft'
        ),
    )

    PLACEMENT_FEE_NEEDS_REVISION = NotificationType(
        'n/a',
        _('Candidate placement is sent to revision'),
        _(
            '{action_object.client.name} - {action_object.candidate.name}\'s'
            ' placement form'
            ' has been submitted for revision'
        ),
    )

    PLACEMENT_FEE_APPROVED = NotificationType(
        'n/a',
        _('Candidate placement is approved'),
        _(
            '{action_object.client.name} - {action_object.candidate.name}\'s'
            ' placement form'
            ' has been approved'
        ),
    )

    FEE_PENDING = NotificationType(
        'n/a',
        _('Fee is submitted for approval'),
        _(
            '{action_object.contract_type_title} - {action_object.bill_description_title}'
            ' fee'
            ' has been submitted for your approval'
        ),
    )

    FEE_PENDING_REMINDER = NotificationType(
        'n/a',
        _('Fee is waiting approval'),
        _(
            '{action_object.contract_type_title} - {action_object.bill_description_title}'
            ' fee'
            ' is waiting for your approval'
        ),
    )

    FEE_DRAFT = NotificationType(
        'n/a',
        _('Fee is set as draft'),
        _(
            '{action_object.contract_type_title} - {action_object.bill_description_title}'
            ' fee'
            ' has been saved as draft'
        ),
    )

    FEE_NEEDS_REVISION = NotificationType(
        'n/a',
        _('Fee is sent to revision'),
        _(
            '{action_object.contract_type_title} - {action_object.bill_description_title}'
            ' fee'
            ' has been submitted for revision'
        ),
    )

    FEE_APPROVED = NotificationType(
        'n/a',
        _('Fee is approved'),
        _(
            '{action_object.contract_type_title} - {action_object.bill_description_title}'
            ' fee'
            ' has been approved'
        ),
    )

    # <org | actor> submitted <candidate | action_object> for <job | target>
    CANDIDATE_SHORTLISTED_FOR_JOB = NotificationType(
        'n/a',
        _('Candidate shortlisted for a job'),
        _('{actor.name} shortlisted {action_object.name} for "{target.title}"'),
    )

    # <org | actor> longlisted <candidate | action_object> for <job | target>
    CANDIDATE_LONGLISTED_FOR_JOB = NotificationType(
        'n/a',
        _('Candidate longlisted for a job'),
        _('{actor.name} longlisted {action_object.name} for "{target.title}"'),
    )

    # <talent | actor> assigned you for <job | target>
    TALENT_ASSIGNED_MANAGER_FOR_JOB = NotificationType(
        'n/a',
        _('Talent Associate assigns you to a job'),
        _('{actor.full_name} assigned you to "{target.title}"'),
    )

    # <client | actor> created contract with your agency
    CLIENT_CREATED_CONTRACT = NotificationType(
        'n/a',
        _('Client creates a contract with your agency'),
        _('{actor.name} has invited you to view their open positions'),
        _(
            '{actor.name} has invited you to view their open positions on '
            'the ZooKeep platform.'
        ),
    )

    CONTRACT_INVITATION_DECLINED = NotificationType(
        'n/a',
        _('Agency declined invitation'),
        _('{actor.name} has declined your invitation to see your jobs.'),
    )

    CONTRACT_INVITATION_ACCEPTED = NotificationType(
        'n/a',
        _('Agency accepted invitation'),
        _('{actor.name} has accepted your invitation to see your jobs.'),
    )

    CONTRACT_SIGNED_BY_ONE_PARTY = NotificationType(
        'n/a',
        _('Contract is signed by one of the parties'),
        _(
            '{actor.name} have confirmed the contract is signed.\n'
            'Please open invitation page and confirm.'
        ),
    )

    CONTRACT_INITIATED_AGENCY = NotificationTypeFactory.contract_initiated(
        _('You will be able to submit candidates once they assign you ' 'to a job.'),
        'client',
    )

    CONTRACT_INITIATED_CLIENT = NotificationTypeFactory.contract_initiated(
        _('Assign {actor.name} to your openings.'), 'agency'
    )

    CONTRACT_JOB_ACCESS_REVOKED_INVITE_IGNORED = NotificationTypeFactory.job_access_revoked(
        _('The invitation has expired')
    )

    CONTRACT_JOB_ACCESS_REVOKED_NO_AGREEMENT = NotificationTypeFactory.job_access_revoked(
        _('You did not find an agreement')
    )

    # <client | actor> assigned your agency to <job | target>
    CLIENT_ASSIGNED_AGENCY_FOR_JOB = NotificationType(
        'n/a',
        _('Client assigns your agency to a job'),
        _('{actor.name} assigned your agency to "{target.title}"'),
    )

    # <agency | actor> assigned you to <job | target>
    AGENCY_ASSIGNED_MEMBER_FOR_JOB = NotificationType(
        'n/a',
        _('Your agency assigns you to a job'),
        _('{actor.full_name} assigned you to "{target.title}"'),
    )

    # <client | actor> updated <job | target>
    CLIENT_UPDATED_JOB = NotificationType(
        'n/a', _('Client updates a job'), _('{actor.name} updated "{target.title}"'),
    )
    PROPOSAL_MOVED = NotificationType(
        'n/a',
        _('Candidate is reallocated to a different job'),
        _(
            '{actor.name} reallocated {action_object.name} from '
            '{from_job} to {target.title}'
        ),
    )
    USER_MENTIONED_IN_COMMENT = NotificationType(
        'n/a',
        _('User is mentioned'),
        _('{actor.full_name} mentioned you on {target.candidate}'),
        _(
            '{actor.full_name} mentioned you on {target.candidate}: "{target.formatted_text}"'
        ),
        _('Notification: New comment on {target.candidate}'),
    )

    USER_MENTIONED_IN_COMMENT_DELETED = NotificationType(
        'n/a',
        _('Comment mentioning user is deleted'),
        _(
            '{actor.full_name} deleted a comment mentioning you on {target.candidate}: "{target.formatted_text}"'
        ),
        email_subject=_('Notification: Comment deleted on {target.candidate}'),
    )

    # new notifs
    NEW_PROPOSAL_CANDIDATE_SOURCED_BY = NotificationType(
        group='candidate_is_added_to_job',
        setting_label=_('Candidate is Added to Job'),
        text=_('{actor_name} added {action_object.name} to {target.job.title}'),
        email_text=_(
            'A Candidate you sourced was added to a Job.\n\n'
            'Candidate: {action_object.name}\n'
            'Job: {target.job.title}\n'
            'Candidate was added to job by {actor_name} on {datetime}'
        ),
        email_subject=_('{action_object.name} was added to {target.job.title}'),
    )

    NEW_PROPOSAL_CANDIDATE_RECRUITER = NotificationType(
        group='candidate_is_added_to_job_excl_direct_application',
        setting_label=_('Candidate is Added to Job (excl. Direct Application)'),
        text=_('{actor_name} added {action_object.name} to {target.job.title}'),
        email_text=_(
            'A new Candidate was added to a Job you manage.\n\n'
            'Candidate: {action_object.name}\n'
            'Job: {target.job.title}\n'
            'Candidate was added to job by {actor_name} on {datetime}'
        ),
        email_subject=_('{action_object.name} Was Added to {target.job.title}'),
    )

    NEW_PROPOSAL_CANDIDATE_DIRECT_APPLICATION = NotificationType(
        group='candidate_is_added_to_job_direct_application',
        setting_label=_('Candidate is Added to Job - Direct Application'),
        text=_('{actor.name} applied to {target.job.title}'),
        email_text=_(
            'A new Candidate applied to a Job you manage.\n\n'
            'Candidate: {actor.name}\n'
            'Job: {target.job.title}\n'
            'Candidate applied on {datetime}'
        ),
        email_subject=_('{actor.name} Applied to {target.job.title}'),
    )

    PROPOSAL_SUBMITTED_TO_HIRING_MANAGER = NotificationType(
        group='n/a',
        setting_label=_('N/A'),
        text=_('Please review {action_object.name} submitted to {target.job.title}'),
        email_text=_(
            'Please review {action_object.name} submitted to {target.job.title}\n\n'
            'You can Click on "Approve" or "Reject" Candidate directly from the Application.'
        ),
        email_subject=_('Application Submission Pending Review for {target.job.title}'),
    )

    PROPOSAL_APPROVED_REJECTED_BY_HIRING_MANAGER = NotificationType(
        group='n/a',
        setting_label=_('N/A'),
        text=_('You {decision} {action_object.name} submitted to {target.job.title}'),
    )

    PROPOSAL_PENDING_HIRING_DECISION = NotificationType(
        group='n/a',
        setting_label=_('N/A'),
        text=_(
            '{action_object.name} is Pending Hiring Decision for {target.job.title}'
        ),
        email_text=_(
            'A Candidate Application is Pending Hiring Decision!\n\n'
            'Candidate: {action_object.name}\n'
            'Job: {target.job.title}'
        ),
        email_subject=_('Pending Hiring Decision for {action_object.name}'),
    )

    PROPOSAL_PENDING_START = NotificationType(
        group='n/a',
        setting_label=_('N/A'),
        text=_('{action_object.name} Has Been Hired for {target.job.title}'),
        email_text=_(
            'A Candidate Has Been Hired!\n\n'
            'Candidate: {action_object.name}\n'
            'Job: {target.job.title}'
        ),
        email_subject=_('{action_object.name} Has been Hired'),
    )

    CLIENT_CHANGED_PROPOSAL_STATUS = NotificationType(
        group='client_changed_proposal_status',
        setting_label=_('Application Status is Updated'),
        text=_(
            '{actor_name} changed the Status of {action_object.name} for {target.job.title} to {status}'
        ),
        email_text=_(
            'An Application Status was updated.\n\n'
            'Candidate: {action_object.name}\n'
            'Job: {target.job.title}\n'
            'Status: {old_status} → {status}\n'
            'By {actor_name} on {datetime}'
        ),
        email_subject=_('{action_object.name} Moved to {status}'),
    )

    JOB_IS_FILLED = NotificationType(
        group='job_is_filled',
        setting_label=_('Job is Filled up'),
        text=_('{target.title} has been filled 🎉'),
        email_text=_(
            '{target.title} has been filled.\n\n'
            'Hired Candidate(s):\n'
            '{hired_candidates}'
        ),
        email_subject=_('{target.title} is Filled 🎉'),
    )

    PROPOSAL_IS_REJECTED = NotificationType(
        group='proposal_is_rejected',
        setting_label=_('Application is Rejected'),
        text=_('{actor.name} rejected {action_object.name} for {target.job.title}'),
        email_text=_(
            'A Candidate Application was rejected!\n\n'
            'Candidate: {action_object.name}\n'
            'Job: {target.job.title}\n'
            'Candidate was Rejected by {actor.name} on {datetime}'
        ),
        email_subject=_(
            '{action_object.name} Application to {target.job.title} was Rejected!'
        ),
    )

    INTERVIEW_PROPOSAL_IS_SENT = NotificationType(
        group='interview_proposal_is_sent',
        setting_label=_('Interview Proposal is Sent to Candidate'),
        text=_(
            'Interview Proposal was sent to {action_object.candidate.name} for {target.job.title}'
        ),
    )

    INTERVIEW_PROPOSAL_CONFIRMED_PROPOSER = NotificationType(
        group='interview_proposal_is_confirmed',
        setting_label=_('Interview Proposal is Confirmed by Candidate'),
        text=_(
            '{actor.name} confirmed the interview {action_object.order} for {target.job.title} with {action_object.interviewer.name}'
        ),
        email_text=_(
            'The interview {action_object.order} with {actor.name} has been confirmed:\n\n'
            'Job: {target.job.title}\n\n'
            'When: {timeframe}\n\n'
            'Candidate: {actor.name}\n'
            'Interviewer: {action_object.interviewer.name}\n\n'
            '{action_object.notes}'
        ),
        email_subject=_(
            '{target.job.title} - Interview {action_object.order} with {actor.name} confirmed'
        ),
    )

    INTERVIEW_PROPOSAL_CONFIRMED_INTERVIEWER = NotificationType(
        group='n/a',
        setting_label=_('Proposal interview confirmed'),
        text=_('{actor.name} confirmed the interview for {target.job.title}'),
        email_text=_(
            'Dear {action_object.interviewer.name}, your interview with {actor.name} has been confirmed:\n\n'
            'Job: {target.job.title}\n\n'
            'When: {timeframe}\n\n'
            'Candidate: {actor.name}\n'
            'Interviewer: {action_object.interviewer.name}\n\n'
            '{action_object.notes}'
        ),
        email_subject=_('{target.job.title} - Interview with {actor.name} confirmed'),
    )

    INTERVIEW_PROPOSAL_REJECTED_RECRUITER = NotificationType(
        group='n/a',
        setting_label=_('Proposal interview rejected'),
        text=_(
            'Interview Proposal was declined by {actor.name} for {target.job.title}'
        ),
        email_text=_(
            'The interview proposal for interview {action_object.order} with {actor.name} has been declined:\n'
            'Please try to schedule the interview again.\n\n'
            'Job: {target.job.title}\n\n'
            'Candidate: {actor.name}\n'
            'Interviewer: {action_object.interviewer.name}\n'
        ),
        email_subject=_(
            '{target.job.title} - Interview Proposal with {actor.name} was Declined'
        ),
    )

    INTERVIEW_PROPOSAL_REJECTED_INTERVIEWER = NotificationType(
        group='n/a',
        setting_label=_('Proposal interview rejected'),
        text=_(
            'Interview Proposal was declined by {actor.name} for {target.job.title}'
        ),
        email_text=_(
            'Dear {action_object.interviewer.name}, your interview proposal with {actor.name} has been declined.\n'
            'The Recruiter will contact you to schedule the interview again.\n\n'
            'Job: {target.job.title}\n\n'
            'Candidate: {actor.name}\n'
            'Interviewer: {action_object.interviewer.name}\n'
        ),
        email_subject=_(
            '{target.job.title} - Interview Proposal with {actor.name} was Declined'
        ),
    )

    INTERVIEW_PROPOSAL_CANCELED = NotificationType(
        group='n/a',
        setting_label=_('Proposal interview canceled'),
        text=_(
            'Interview {action_object.order} with {target.candidate.name} for {target.job.title} has been cancelled by {actor.name}'
        ),
        email_text=_(
            'Dear {action_object.interviewer.name}, your interview with {target.candidate.name} has been cancelled:\n\n'
            'Job: {target.job.title}\n\n'
            'When: {timeframe}\n\n'
            'Candidate: {target.candidate.name}\n'
            'Interviewer: {action_object.interviewer.name}\n\n'
        ),
        email_subject=_(
            '{target.job.title} - Interview with {target.candidate.name} cancelled'
        ),
    )

    INTERVIEW_ASSESSMENT_ADDED_RECRUITER = NotificationType(
        group='interview_assessment_is_added',
        setting_label=_('Interview assessment is added'),
        text=_(
            'New Assessment Added to Interview {action_object.order} for {target.candidate.name} applying to {target.job.title}'
        ),
        email_text=_(
            'A Interview Assessment was added:\n\n'
            'Job: {target.job.title}\n\n'
            'Interview {action_object.order} on {timeframe}\n\n'
            'Candidate: {target.candidate.name}\n'
            'Interviewer: {action_object.interviewer.name}'
        ),
        email_subject=_(
            '{target.job.title} - New Assessment for {target.candidate.name}'
        ),
    )

    INTERVIEW_ASSESSMENT_ADDED_INTERVIEWER = NotificationType(
        group='n/a',
        setting_label=_('Interview assessment is added'),
        text=_(
            'New Assessment Added to Interview {action_object.order} for {target.candidate.name} applying to {target.job.title}'
        ),
        email_text=_(
            'Dear {action_object.interviewer.name}, a New Assessment was added to your interview:\n\n'
            'Job: {target.job.title}\n\n'
            'Interview {action_object.order} on {timeframe}\n\n'
            'Candidate: {target.candidate.name}\n'
            'Interviewer: {action_object.interviewer.name}'
        ),
        email_subject=_(
            '{target.job.title} - New Assessment for {target.candidate.name}'
        ),
    )

    NOTE_ACTIVITY_ADDED_TO_PROPOSAL = NotificationType(
        group='note_activity_added_to_proposal',
        setting_label=_('A new note is added to an application'),
        text=_(
            '{actor.name} added a note to {action_object.candidate.name}\'s Application to {action_object.job.title}'
        ),
        email_text=_(
            '{actor.name} added a Note:\n\n'
            'Job: {action_object.job.title}\n'
            'Candidate: {action_object.candidate.name}\n'
            'Note: {target.content}\n'
        ),
        email_subject=_(
            '{action_object.job.title} - New Note added for {action_object.candidate.name}'
        ),
    )

    @classmethod
    def get_choices(cls):
        choices = [(item.name.lower(), item.value.setting_label) for item in cls]
        choices.sort(key=lambda x: x[0])
        return choices

    @classmethod
    def get_group_choices(cls):
        choices = []
        keys = []
        for item in cls:
            key = item.value.group.lower()
            if key not in keys and key != 'n/a':
                choices.append((key, item.value.setting_label))
                keys.append(key)
        choices.sort(key=lambda x: x[0])
        return choices


class FrontendSettingsSchema(object):
    PAGINATION_SCHEMA = [10, 25, 50, 100]

    PAGINATION_FIELDS = [
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
        'career_site_job_postings_show_per',
    ]

    @classmethod
    def get_default_pagination(cls):
        default_value = cls.PAGINATION_SCHEMA[2]
        return {field: default_value for field in cls.PAGINATION_FIELDS}

    @classmethod
    def get_default_frontend_settings(cls):
        return {**cls.get_default_pagination()}

    @property
    def fields(self):
        fields = []
        fields += self.PAGINATION_FIELDS

        return fields


class UserManager(BaseUserManager):
    """A model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""

        if not email:
            raise ValueError('The given email must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""

        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a superuser with the given email and password."""

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


def get_user_photo_upload_to(user, filename):
    return f'avatars/{user.id}_{filename}'


@reversion.register(exclude=('password', 'last_login'), ignore_duplicates=True)
class User(AbstractUser):
    """Represents a User."""

    username = None
    email = models.EmailField(_('email address'), unique=True)

    first_name = models.CharField(_('first name'), max_length=30)
    last_name = models.CharField(_('last name'), max_length=150)

    is_activated = models.BooleanField(default=True, editable=False)
    #  is_waiting_invite field defines if user should get registration link
    #  then agency is invited
    #  and user is the primary contact of that agency
    #  This is for cases where agency created with dummy users to fill primary contact
    is_waiting_invite = models.BooleanField(default=False)
    on_activation_action = models.CharField(
        max_length=128, null=True, blank=True, editable=False
    )
    on_activation_params = models.JSONField(null=True, blank=True, editable=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    photo = models.ImageField(
        upload_to=get_user_photo_upload_to, blank=True, null=True,
    )

    locale = models.CharField(
        max_length=8, choices=settings.LANGUAGES, default=settings.DEFAULT_USER_LANGUAGE
    )

    frontend_settings = models.JSONField(
        default=FrontendSettingsSchema.get_default_frontend_settings
    )

    country = models.CharField(max_length=128, blank=True, choices=COUNTRY_CHOICES)

    zoho_id = models.CharField(max_length=32, blank=True)
    zoho_data = models.JSONField(null=True, blank=True)

    is_legal_agreed = models.BooleanField(default=True)
    legal_agreement_hash = models.CharField(max_length=32, blank=True)

    @property
    def full_name(self):
        return self.get_full_name()

    @property
    def name(self):
        return self.full_name

    @property
    def unread_notifications_count(self):
        return self.notifications.filter(unread=True).count()

    def get_profile_attribute_pair_iterator(self):
        profile_attributes = (
            'agencyadministrator',
            'agencymanager',
            'recruiter',
            'clientadministrator',
            'clientinternalrecruiter',
            'clientstandarduser',
        )
        for attr in profile_attributes:
            if hasattr(self, attr):
                profile = getattr(self, attr)
                yield attr, profile

    def get_profile_iterator(self):
        for pair in self.get_profile_attribute_pair_iterator():
            yield pair[1]

    def assign_profile_group(self, role):
        if role.group_name:
            group = Group.objects.get(name=role.group_name)
            self.groups.add(group)

    def delete_profile(self, related_field):
        profile = getattr(self, related_field, None)
        if profile:
            profile.delete()
            setattr(self, related_field, None)

    @property
    def first_profile(self):
        for profile in self.get_profile_iterator():
            return profile

    @property
    def profile(self):
        """Return the related UserProfile, depending on User type."""
        # TODO: add polymorphism?
        profiles = [*self.get_profile_iterator()]

        if len(profiles) == 0:
            return

        if len(profiles) == 1:
            return profiles[0]

        raise AttributeError('User have more than 1 profile.')

    @property
    def profile_type(self):
        profile = getattr(self, 'profile', None)
        if profile is None:
            return None
        return profile.model_name

    @property
    def org(self):
        profile = getattr(self, 'profile', None)
        if profile is None:
            return None
        return profile.org

    def __str__(self):
        """Return the email of the User."""
        return self.email

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        error_dict = {}

        if hasattr(self.profile, 'agency'):
            # country is required for all Agency users
            if not self.country:
                error_dict['country'] = _('Country is required for Agency Users')

        if error_dict:
            raise ValidationError(error_dict)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ProfileMixin(models.Model):
    """Mixin for User Profiles, e.g.: Hiring Manager, Recruiter etc."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    group_name = None
    has_full_candidate_field_access = False

    class Meta:  # noqa
        abstract = True

    @property
    def name(self):
        return self.user.name

    def apply_own_candidates_filter(self, queryset):
        """Org's own candidates"""
        return self.org.apply_own_candidates_filter(queryset)

    def apply_candidates_filter(self, queryset):
        """Abstract fn, applies filter to Candidates queryset."""
        return self.apply_own_candidates_filter(queryset).distinct()

    def apply_jobs_filter(self, queryset):
        """Method, applies Jobs query filter."""
        return self.org.apply_own_jobs_filter(queryset)

    def apply_job_files_filter(self, queryset):
        """Apply queryset filter to get Job files for allowed Jobs."""
        return queryset.filter(job__in=self.apply_jobs_filter(Job.objects.all()))

    def apply_proposals_filter(self, queryset):
        """Apply queryset filter to get available proposals"""
        org_content_type = ContentType.objects.get_for_model(self.org)
        return queryset.filter(
            Q(
                job__org_content_type=org_content_type,
                job__org_id=self.org.id,
                status__stage__in=ProposalStatusStage.get_shortlist_keys(),
            )
            | Q(
                candidate__org_id=self.org.id,
                candidate__org_content_type=org_content_type,
            )
        ).distinct()

    def apply_tags_filter(self, queryset):
        """Apply queryset filter to get available tags"""
        org_content_type = ContentType.objects.get_for_model(self.org)
        return queryset.filter(org_content_type=org_content_type, org_id=self.org.id)

    def apply_candidate_tags_filter(self, queryset):
        """Apply queryset filter to get available candidate tags"""
        org_content_type = ContentType.objects.get_for_model(self.org)
        return queryset.filter(
            tag__org_content_type=org_content_type, tag__org_id=self.org.id
        )

    @property
    def contracts_filter(self):
        """Abstract property, returns Contracts query filter."""
        raise NotImplementedError

    @property
    def org(self):
        """Abstract property, returns User Organization."""
        raise NotImplementedError

    def represent_notification_types(self):
        """Get list of Notification Types ready for serialization."""
        return [
            {
                'name': n.value.group.lower(),
                'description': n.value.setting_label,
                'user_field': camelize_str(n.value.field),
                'user_field_enabled': getattr(self.user, n.value.field, None),
            }
            for n in self.notification_types
        ]

    @property
    def notification_types(self):
        """Abstract property, returns Notification types for User."""
        raise NotImplementedError

    def can_create_proposal(self, job, candidate):
        """Check if User can create a Proposal for given Job and Candidate."""
        return self.org == candidate.organization and self.org == job.organization

    def can_create_job_file(self, job):
        """Check if User can create a Job File for a given Job."""
        return self.org == job.organization

    @property
    def model_name(self):
        return self._meta.model_name


@reversion.register()
class AgencyRegistrationRequest(models.Model):
    """Agency Registration Request."""

    ip = models.GenericIPAddressField()
    headers = models.JSONField()

    name = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.BooleanField(default=False)

    # organization country
    country = models.CharField(max_length=128, blank=True, choices=COUNTRY_CHOICES,)

    via_job = models.ForeignKey('Job', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return 'Agency Registration Request #{} "{}"'.format(self.id, self.name)

    def approve(self):
        with transaction.atomic():
            agency = Agency.objects.create(
                name=self.name,
                contact_email=self.user.email,
                primary_contact=self.user,
                country=self.country,
            )
            agency.assign_agency_administrator(self.user)

            if self.via_job:
                # TODO: Should the contract be initiated?
                Contract.objects.create(agency=agency, client=self.via_job.organization)
                self.via_job.assign_agency(agency)

            self.created = True
            self.save()

            return agency


@reversion.register()
class ClientRegistrationRequest(models.Model):
    """Client Registration Request."""

    ip = models.GenericIPAddressField()
    headers = models.JSONField()

    name = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.BooleanField(default=False)

    # organization country
    country = models.CharField(max_length=128, blank=True, choices=COUNTRY_CHOICES,)

    def __str__(self):
        return 'Client Registration Request #{} "{}"'.format(self.id, self.name)


def generate_invite_token():
    return secrets.token_urlsafe(16)


class AgencyInvite(models.Model):
    """Agency Invite."""

    email = models.EmailField()
    private_note = models.CharField(max_length=1024)

    token = models.CharField(
        max_length=128, unique=True, default=generate_invite_token, editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    used_by = models.ForeignKey(
        'Agency', on_delete=models.CASCADE, null=True, editable=False
    )

    def __str__(self):
        return 'Agency Invite #{}'.format(self.id)

    def get_absolute_url(self):
        return reverse('agency_sign_up_token', kwargs={'token': self.token})


class OrganizationMixin(models.Model):
    """Mixin for organizations: clients, agencies."""

    @property
    def type(self):
        raise NotImplementedError

    name = models.CharField(max_length=128)
    name_ja = models.CharField(max_length=128, blank=True)

    zoho_auth_token = models.CharField(
        max_length=32,
        help_text=(
            'Can be generated on this page:\n'
            'https://accounts.zoho.com/apiauthtoken/create?SCOPE=ZohoRecruit/'
            'recruitapi'
        ),
        blank=True,
    )

    jobs = GenericRelation('Job', 'org_id', 'org_content_type')
    proposal_statuses = GenericRelation(
        'OrganizationProposalStatus', 'org_id', 'org_content_type'
    )
    teams = GenericRelation('Team', 'org_id', 'org_content_type')
    candidate_notes = GenericRelation('CandidateNote')
    candidate_files = GenericRelation('CandidateFile', 'org_id', 'org_content_type')

    country = models.CharField(max_length=128, blank=True, choices=COUNTRY_CHOICES)

    function_focus = models.ManyToManyField('Function')
    website = models.URLField(blank=True)
    quick_action_mapping = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:  # noqa
        abstract = True

    def __str__(self):
        """Return the string representation of the Agency object."""
        return '{} - {}'.format(self.pk, self.name)

    @property
    @abstractmethod
    def members(self):
        raise NotImplementedError

    @property
    def get_user_filter(self):
        raise NotImplementedError

    @property
    def get_user_filter(self):
        raise NotImplementedError

    @property
    def has_zoho_integration(self):
        return bool(self.zoho_auth_token)

    @property
    def career_site_url(self):
        raise NotImplementedError

    def assign_role(self, role, user):
        raise NotImplementedError

    def apply_own_candidates_filter(self, queryset):
        return queryset.filter(org_filter(self))

    def apply_proposed_candidates_filter(self, queryset):
        return queryset.filter(
            proposals__job__org_id=self.id,
            proposals__job__org_content_type=ContentType.objects.get_for_model(self),
        )

    def apply_own_jobs_filter(self, queryset):
        """Apply queryset filter to get Jobs Organization owns"""
        return queryset.filter(org_filter(self)).distinct()

    def apply_guest_jobs_filter(self, queryset):
        """Apply queryset filter to get published Jobs Organization was invited to"""
        raise NotImplementedError

    def apply_available_clients_filter(self, queryset):
        raise NotImplementedError

    def has_contract_with(self, org):
        return False


def is_contract_initiated(client, agency):
    return Contract.objects.filter(
        status=ContractStatus.INITIATED.key, agency=agency, client=client,
    ).exists()


class InvoiceOn(StatusEnum):
    IOA = _('IOA')
    IOS = _('IOS')


class AgencyClientInfo(models.Model):
    agency = models.ForeignKey(
        'Agency', related_name='attached_client_info', on_delete=models.CASCADE
    )
    client = models.ForeignKey(
        'Client', related_name='attached_info', on_delete=models.CASCADE
    )

    industry = models.CharField(
        max_length=128, choices=Industry.get_choices(), blank=True
    )
    type = models.CharField(max_length=64, choices=ClientType.get_choices(), blank=True)

    originator = models.ForeignKey(
        'User',
        related_name='discovered_clients',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    account_manager = models.ForeignKey(
        'User',
        related_name='managed_clients',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    info = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    website = models.URLField(blank=True, default='')

    primary_contact_number = PhoneNumberField(blank=True)
    billing_address = models.CharField(max_length=256, blank=True)

    portal_url = models.URLField(blank=True)
    portal_login = models.CharField(max_length=128, blank=True)
    portal_password = models.CharField(max_length=128, blank=True)

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        related_name='last_updated_client_info',
        blank=True,
        null=True,
    )
    ios_ioa = models.CharField(
        max_length=InvoiceOn.get_db_field_length(),
        choices=InvoiceOn.get_choices(),
        default=InvoiceOn.IOA.key,
    )

    class Meta:
        unique_together = ('agency', 'client')


def get_client_logo_file_path(instance, filename):
    return f'client/{instance.id}/logo/{uuid4()}/{filename}'


@reversion.register()
class Client(OrganizationMixin):
    """Represents a party which is looking for employees."""

    type = 'client'

    jobs = GenericRelation(
        'Job', 'org_id', 'org_content_type', related_query_name='owner_client'
    )
    proposal_statuses = GenericRelation(
        'OrganizationProposalStatus',
        'org_id',
        'org_content_type',
        related_query_name='client',
    )

    candidates = GenericRelation(
        'Candidate',
        related_query_name='client',
        object_id_field='org_id',
        content_type_field='org_content_type',
    )
    teams = GenericRelation(
        'Team', 'org_id', 'org_content_type', related_query_name='client'
    )
    candidate_files = GenericRelation(
        'CandidateFile', 'org_id', 'org_content_type', related_query_name='client'
    )
    candidate_notes = GenericRelation('CandidateNote', related_query_name='client')
    tags = GenericRelation(
        'Tag', 'org_id', 'org_content_type', related_query_name='client'
    )
    primary_contact = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True
    )

    owner_agency = models.ForeignKey(
        'Agency',
        related_name='owned_clients',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    zoho_id = models.CharField(max_length=32, blank=True, default='')
    zoho_data = models.JSONField(null=True, blank=True)

    logo = models.ImageField(blank=True, null=True, upload_to=get_client_logo_file_path)
    career_site_slug = models.SlugField(blank=True, null=True, unique=True)
    is_career_site_enabled = models.BooleanField(default=False)

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        error_dict = {}

        if not self.primary_contact and not self.owner_agency:
            error_dict.update({'primary_contact': _('This field is required.')})

        if error_dict:
            raise ValidationError(error_dict)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def members(self):
        return User.objects.filter(
            Q(clientadministrator__client=self)
            | Q(clientinternalrecruiter__client=self)
            | Q(clientstandarduser__client=self)
        )

    @property
    def career_site_url(self):
        if self.is_career_site_enabled:
            return settings.BASE_URL + reverse(
                'career_site_page', kwargs={'slug': self.career_site_slug}
            )

    def assign_role(self, role, user):
        role.objects.create(user=user, client=self)
        user.assign_profile_group(role)

    # TODO remove
    def assign_talent_associate(self, user):
        """Assign a User to be a Talent Associate for this Client."""
        self.assign_role(TalentAssociate, user)

    # TODO remove
    def assign_hiring_manager(self, user):
        """Assign a User to be a Hiring Manager for this Client."""
        self.assign_role(HiringManager, user)

    def assign_standard_user(self, user):
        self.assign_role(ClientStandardUser, user)

    def assign_administrator(self, user):
        self.assign_role(ClientAdministrator, user)

    def assign_internal_recruiter(self, user):
        self.assign_role(ClientInternalRecruiter, user)

    def apply_available_clients_filter(self, queryset):
        return queryset.filter(pk=self.pk)

    def has_contract_with(self, org):
        return isinstance(org, Agency) and is_contract_initiated(self, org)


class TalentAssociate(ProfileMixin):
    """Represents a User which manages Proposals and creates Jobs."""

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    teams = models.ManyToManyField('Team', blank=True)
    group_name = 'Talent Associates'
    has_full_candidate_field_access = True

    def __str__(self):
        return 'Talent Associate of "{}"'.format(self.client.name)

    def apply_candidates_filter(self, queryset):
        """Apply queryset filter to select Candidates linked via Proposals."""
        return (
            self.apply_own_candidates_filter(queryset)
            | self.org.apply_proposed_candidates_filter(queryset)
        ).distinct()

    @property
    def contracts_filter(self):
        """Queryset filter to select Contracts linked to a Client."""
        return Q(client=self.client)

    @property
    def org(self):
        """Return User Organization: the Client."""
        return self.client

    @property
    def notification_types(self):
        """Return Talent Associate related Notification types."""
        return [
            NotificationTypeEnum.CANDIDATE_SHORTLISTED_FOR_JOB,
            NotificationTypeEnum.CANDIDATE_LONGLISTED_FOR_JOB,
        ]


class HiringManager(ProfileMixin):
    """Represents a User which manages assigned Jobs."""

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    teams = models.ManyToManyField('Team', blank=True)
    group_name = 'Hiring Managers'
    has_full_candidate_field_access = True

    def __str__(self):
        return 'Hiring Manager of "{}"'.format(self.client.name)

    def apply_candidates_filter(self, queryset):
        """Apply queryset filter to select Candidates linked via Proposals."""

        return (
            self.apply_own_candidates_filter(queryset)
            | self.org.apply_proposed_candidates_filter(queryset).filter(
                proposals__job___managers=self.user
            )
        ).distinct()

    def apply_jobs_filter(self, queryset):
        """Apply queryset filter to select assigned Jobs of own Client."""
        return super().apply_jobs_filter(queryset.filter(_managers=self.user))

    def apply_proposals_filter(self, queryset):
        """Apply queryset filter to select available Proposals."""
        return super().apply_proposals_filter(queryset).filter(job___managers=self.user)

    def can_create_proposal(self, job, candidate):
        """Check if User can create a Proposal for given Job and Candidate."""

        return (
            super().can_create_proposal(job, candidate)
            and self.user in job.managers.all()
        )

    @property
    def contracts_filter(self):
        """Queryset filter to select Contracts linked to a Client."""
        return Q(client=self.client)

    @property
    def org(self):
        """Return User Organization: the Client."""
        return self.client

    def can_create_job_file(self, job):
        """Check if User can create a Job File for a given Job."""
        return super().can_create_job_file(job) and (
            self.user in job.managers or self.user == job.owner
        )

    @property
    def notification_types(self):
        """Return Hiring Manager related Notification types."""
        return [
            NotificationTypeEnum.CANDIDATE_SHORTLISTED_FOR_JOB,
            NotificationTypeEnum.CANDIDATE_LONGLISTED_FOR_JOB,
            NotificationTypeEnum.TALENT_ASSIGNED_MANAGER_FOR_JOB,
            NotificationTypeEnum.PROPOSAL_MOVED,
        ]


class ClientAdministrator(ProfileMixin):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    teams = models.ManyToManyField('Team', blank=True)
    group_name = 'Client Administrators'
    has_full_candidate_field_access = True

    def __str__(self):
        return 'Client Administrator of "{}"'.format(self.client.name)

    @property
    def contracts_filter(self):
        """Queryset filter to select Contracts linked to a Client."""
        return Q(client=self.client)

    def apply_candidates_filter(self, queryset):
        """Apply queryset filter to select Candidates linked via Proposals."""
        return (
            self.apply_own_candidates_filter(queryset)
            | self.org.apply_proposed_candidates_filter(queryset)
        ).distinct()

    @property
    def org(self):
        """Return User Organization: the Client."""
        return self.client

    @property
    def notification_types(self):
        """Return Client Administrator related Notification types."""
        return []


class ClientInternalRecruiter(ProfileMixin):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    teams = models.ManyToManyField('Team', blank=True)
    group_name = 'Client Internal Recruiters'
    has_full_candidate_field_access = True

    def __str__(self):
        return 'Client Internal Recruiter of "{}"'.format(self.client.name)

    @property
    def contracts_filter(self):
        """Queryset filter to select Contracts linked to a Client."""
        return Q(client=self.client)

    def apply_candidates_filter(self, queryset):
        """Apply queryset filter to select Candidates linked via Proposals."""
        return (
            self.apply_own_candidates_filter(queryset)
            | self.org.apply_proposed_candidates_filter(queryset)
        ).distinct()

    @property
    def org(self):
        """Return User Organization: the Client."""
        return self.client

    @property
    def notification_types(self):
        """Return Client Internal Recruiter related Notification types."""
        return []


class ClientStandardUser(ProfileMixin):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    teams = models.ManyToManyField('Team', blank=True)
    group_name = 'Client Standard Users'

    def __str__(self):
        return 'Client Standard User of "{}"'.format(self.client.name)

    @property
    def contracts_filter(self):
        """Queryset filter to select Contracts linked to a Client."""
        return Q(client=self.client)

    def apply_jobs_filter(self, queryset):
        """Apply queryset filter to select assigned Jobs of own Client."""
        return super().apply_jobs_filter(
            queryset.filter(
                Q(_managers=self.user)
                | Q(interview_templates__interviewer=self.user)
                | Q(proposals__interviews__interviewer=self.user)
            )
        )

    def apply_proposals_filter(self, queryset):
        """Apply queryset filter to select available Proposals."""
        return (
            super()
            .apply_proposals_filter(queryset)
            .filter(
                Q(job___managers=self.user)
                | Q(job__interview_templates__interviewer=self.user)
                | Q(job__proposals__interviews__interviewer=self.user)
            )
        )

    def apply_candidates_filter(self, queryset):
        """Apply queryset filter to select Candidates linked via Proposals."""
        return (
            self.apply_own_candidates_filter(queryset)
            | self.org.apply_proposed_candidates_filter(queryset)
        ).distinct()

    def apply_own_candidates_filter(self, queryset):
        return self.org.apply_own_candidates_filter(queryset).filter(
            Q(proposals__job___managers=self.user)
            | Q(proposals__job__interview_templates__interviewer=self.user)
            | Q(proposals__interviews__interviewer=self.user)
        )

    def can_create_job_file(self, job):
        """Check if User can create a Job File for a given Job."""
        return super().can_create_job_file(job) and (
            self.user in job.managers or self.user == job.owner
        )

    @property
    def org(self):
        """Return User Organization: the Client."""
        return self.client

    @property
    def notification_types(self):
        """Return Client Standard User related Notification types."""
        return []


class NotificationSetting(models.Model):
    """
    Represents user setting for a particular notification type
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notification_settings'
    )
    notification_type_group = models.CharField(
        max_length=255, choices=NotificationTypeEnum.get_group_choices()
    )
    base = models.BooleanField(default=True)
    email = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'notification_type_group'],
                name='unique user notification_type',
            )
        ]

    def __str__(self):
        return f'{self.get_notification_type_group_display()}: Email {"enabled" if self.email else "disabled"}'


class LatestLegalAgreementManager(models.Manager):
    def get_queryset(self):
        """Latest version for each document type"""
        return (
            super()
            .get_queryset()
            .filter(is_draft=False)
            .order_by('document_type', '-version')
            .distinct('document_type')
        )

    def get_hash(self):
        """Identifier of the latest agreements as a whole"""
        return ','.join([str(item.version) for item in self.get_queryset()])


def get_legalagreement_upload_to(instance, filename):
    return f'legal_agreements/{instance.document_type}/{instance.version}/{uuid4()}/{filename}'


class LegalAgreement(models.Model):
    DOCUMENT_TYPE_CHOICES = (
        ('tandc', _('Terms and Conditions')),
        ('pp', _('Privacy Policy')),
    )
    document_type = models.CharField(max_length=8, choices=DOCUMENT_TYPE_CHOICES)
    version = models.PositiveIntegerField()
    is_draft = models.BooleanField(default=False)
    file = models.FileField(upload_to=get_legalagreement_upload_to, max_length=256)

    objects = models.Manager()
    latest_objects = LatestLegalAgreementManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['document_type', 'version'],
                name='unique legal agreement type per version',
            )
        ]

    def __str__(self):
        return f'{self.get_document_type_display()} v{self.version}'


class Function(models.Model):
    """Job/Agency Function"""

    title = models.CharField(max_length=64)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('title_en',)


AGENCY_CATEGORY_GROUPS = [
    ('Placement type', _('Placement type')),
    ('Industry focus', _('Industry focus')),
]


@reversion.register()
class AgencyCategory(models.Model):
    group = models.CharField(max_length=64, choices=AGENCY_CATEGORY_GROUPS)
    title = models.CharField(max_length=64)

    def __str__(self):
        return '{} - {}'.format(self.get_group_display(), self.title)

    class Meta:
        verbose_name_plural = 'agency categories'
        ordering = ('group', 'title_en')


def get_agency_logo_upload_to(agency, filename):
    ext = os.path.splitext(filename)[1]
    return f'agency-logo/{agency.id}_{int(time.time())}{ext}'


def validate_file_image(file):
    ext = os.path.splitext(file.name)[1]

    if ext not in ['.png', '.svg', '.jpg', '.jpeg']:
        raise ValidationError('Invalid image file')


AGENCY_USER_PROFILE_FIELDS = (
    'agencyadministrator',
    'agencymanager',
    'recruiter',
)


@reversion.register()
class Agency(OrganizationMixin):
    """Represents a party which propose candidates for Clients."""

    type = 'agency'

    jobs = GenericRelation(
        'Job', 'org_id', 'org_content_type', related_query_name='owner_agency'
    )
    proposal_statuses = GenericRelation(
        'OrganizationProposalStatus',
        'org_id',
        'org_content_type',
        related_query_name='agency',
    )
    tags = GenericRelation(
        'Tag', 'org_id', 'org_content_type', related_query_name='agency'
    )
    logo = models.FileField(
        blank=True,
        null=True,
        upload_to=get_agency_logo_upload_to,
        help_text='png, svg',
        validators=[validate_file_image],
    )
    description = models.TextField(max_length=1024, blank=True)
    contact_email = models.EmailField(null=True)
    primary_contact = models.ForeignKey(User, on_delete=models.PROTECT, null=True)

    email_domain = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text=(
            'Adding agency\'s email domain will allow recruiters to register '
            'without additional actions'
        ),
        unique=True,
    )

    candidate_notes = GenericRelation('CandidateNote')
    candidates = GenericRelation(
        'Candidate',
        related_query_name='agency',
        object_id_field='org_id',
        content_type_field='org_content_type',
    )
    candidate_files = GenericRelation(
        'CandidateFile', 'org_id', 'org_content_type', related_query_name='agency'
    )

    categories = models.ManyToManyField(AgencyCategory)
    teams = GenericRelation(
        'Team', 'org_id', 'org_content_type', related_query_name='agency'
    )

    enable_researcher_field_feature = models.BooleanField(default=False)

    # Deal pipeline metrics
    deal_hiring_fee_coefficient = models.FloatField(default=0.3)
    deal_first_round_sc = models.FloatField(default=0.1)
    deal_intermediate_round_sc = models.FloatField(default=0.3)
    deal_final_round_sc = models.FloatField(default=0.5)
    deal_offer_sc = models.FloatField(default=0.8)

    class Meta:  # noqa
        verbose_name_plural = 'agencies'

    @property
    def members(self):
        return User.objects.filter(
            Q(agencyadministrator__agency=self)
            | Q(agencymanager__agency=self)
            | Q(recruiter__agency=self)
        )

    @property
    def deal_pipeline_coefficients(self):
        return {
            'hiring_fee': self.deal_hiring_fee_coefficient,
            'first_round': self.deal_first_round_sc,
            'intermediate_round': self.deal_intermediate_round_sc,
            'final_round': self.deal_final_round_sc,
            'offer': self.deal_offer_sc,
        }

    def assign_role(self, role, user):
        role.objects.create(user=user, agency=self)
        user.assign_profile_group(role)

    def assign_agency_administrator(self, user):
        """Assign a User to be an Agency Administrator for this Agency."""
        self.assign_role(AgencyAdministrator, user)

    def assign_agency_manager(self, user):
        """Assign a User to be an Agency Manager for this Agency."""
        self.assign_role(AgencyManager, user)

    def assign_recruiter(self, user):
        """Assign a User to be a Recruiter for this Agency."""
        self.assign_role(Recruiter, user)

    def apply_available_clients_filter(self, queryset):
        return queryset.filter(
            Q(contracts__agency=self, contracts__status=ContractStatus.INITIATED.key,)
            | Q(owner_agency=self)
        ).distinct()

    def apply_own_jobs_filter(self, queryset):
        """Apply queryset filter to get published Jobs Agency owns"""
        return (
            super()
            .apply_own_jobs_filter(queryset)
            .filter(agency_contracts__agency=self)
        )

    def apply_guest_jobs_filter(self, queryset):
        """Apply queryset filter to get published Jobs Agency is assigned to."""
        return queryset.filter(
            agency_contracts__agency=self,
            agency_contracts__is_active=True,
            published=True,
            client__contracts__agency=self,
            client__contracts__status=ContractStatus.INITIATED.key,
        ).distinct()

    @classmethod
    def get_by_email_domain(cls, email):
        email_domain = email.split('@')[1]
        return cls.objects.filter(email_domain=email_domain).first()

    def has_contract_with(self, org):
        return isinstance(org, Client) and is_contract_initiated(org, self)


class Team(models.Model):
    """Teams for Client/Agency members."""

    name = models.CharField(max_length=128)
    notify_if_fee_approved = models.BooleanField(
        default=False, verbose_name='Notify members if candidate placement is approved'
    )
    org_content_type = models.ForeignKey(
        ContentType,
        limit_choices_to=(
            Q(app_label='core', model='agency') | Q(app_label='core', model='client')
        ),
        null=True,
        on_delete=models.CASCADE,
    )
    org_id = GfkLookupField('org_content_type')
    organization = GenericForeignKey('org_content_type', 'org_id')

    class Meta:  # noqa
        unique_together = ('name', 'org_content_type', 'org_id')

    def __str__(self):
        return self.name


@reversion.register()
class Contract(models.Model):
    """Represents a Contract between an Agency and a Client."""

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='contracts'
    )
    agency = models.ForeignKey(
        Agency, on_delete=models.CASCADE, related_name='contracts'
    )

    invite_duration_days = models.IntegerField(
        default=CONTRACT_DEFAULT_INVITATION_DURATION
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_at = models.DateField(blank=True, null=True)
    end_at = models.DateField(blank=True, null=True)
    duration = models.CharField(max_length=64, blank=True, null=True)
    is_client_signed = models.BooleanField(default=False)
    is_agency_signed = models.BooleanField(default=False)

    status = models.CharField(
        max_length=16, choices=CONTRACT_STATUS_CHOICES, default=DEFAULT_CONTRACT_STATUS
    )

    initial_fee = MoneyField(null=True, blank=True, currency_field_name='fee_currency')
    fee_rate = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        null=True,
        blank=True,
        help_text='Float number of percent in format: 00.00',
    )

    @property
    def days_until_invitation_expire(self):
        return max(0, self.invite_duration_days - (now() - self.created_at).days)

    @property
    def is_signed(self):
        return self.is_agency_signed and self.is_client_signed

    class Meta:  # noqa
        unique_together = ('client', 'agency')

    def __str__(self):
        """Return the string representation of the Contract object."""
        return '{} with {}'.format(self.agency, self.client)


class Language(models.Model):
    """Language for Job requirements / Candidate."""

    LANGUAGE_CHOICES = (
        ('cmn', _('Mandarin Chinese')),
        ('es', _('Spanish')),
        ('en', _('English')),
        ('hi', _('Hindi')),
        ('ar', _('Arabic')),
        ('pt', _('Poruguese')),
        ('bn', _('Bengali')),
        ('ru', _('Russian')),
        ('ja', _('Japanese')),
        ('lah', _('Lahnda')),
        ('de', _('German')),
        ('jv', _('Javanese')),
        ('wu', _('Shanghainese')),
        ('zlm', _('Malay')),
        ('te', _('Telugu')),
        ('vi', _('Vietnamese')),
        ('ko', _('Korean')),
        ('fr', _('French')),
        ('mr', _('Marathi')),
        ('ta', _('Tamil')),
        ('ur', _('Urdu')),
        ('tr', _('Turkish')),
        ('it', _('Italian')),
        ('yue', _('Yue Chinese')),
        ('th', _('Thai')),
    )
    language = models.CharField(max_length=16, choices=LANGUAGE_CHOICES)

    LEVEL_CHOICES = (
        (0, _('Survival')),
        (1, _('Daily Conversation')),
        (2, _('Advanced')),
        (3, _('Fluent')),
        (4, _('Native')),
    )
    level = models.IntegerField(choices=LEVEL_CHOICES)

    def __str__(self):
        """Return the string representation of Language object."""
        return '{} {}'.format(self.get_level_display(), self.get_language_display())

    class Meta:  # noqa
        unique_together = ('language', 'level')


@reversion.register
class HiringCriterion(models.Model):
    job = models.ForeignKey(
        'Job', on_delete=models.CASCADE, related_name='hiring_criteria'
    )
    name = models.CharField(max_length=128)


class BaseJobSkill(models.Model):
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)
    attached_by = models.ForeignKey(
        'User', on_delete=models.SET_NULL, null=True, blank=True,
    )

    def __str__(self):
        return f'{self.tag.name} - {self.job.title}'

    class Meta:
        unique_together = ('job', 'tag')
        abstract = True


class JobSkill(BaseJobSkill):
    job = models.ForeignKey('Job', on_delete=models.CASCADE)


class PrivateJobPostingSkill(BaseJobSkill):
    job = models.ForeignKey('PrivateJobPosting', on_delete=models.CASCADE)


class CareerSiteJobPostingSkill(BaseJobSkill):
    job = models.ForeignKey('CareerSiteJobPosting', on_delete=models.CASCADE)


class BaseJob(models.Model):
    """Abstract Base Job Class"""

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Details
    title = models.CharField(max_length=128)
    function = models.ForeignKey(
        Function, on_delete=models.SET_NULL, null=True, blank=True
    )
    employment_type = models.CharField(
        max_length=9, blank=True, choices=JobEmploymentType.get_choices()
    )
    mission = models.TextField(blank=True)
    responsibilities = models.TextField()

    # Requirements
    requirements = models.TextField()
    skills = models.ManyToManyField('Tag', blank=True, through='JobSkill')
    required_languages = models.ManyToManyField(Language, blank=True)

    # Job Conditions
    salary_from = MoneyField(
        null=True, blank=True, currency_field_name='salary_currency'
    )
    salary_to = MoneyField(null=True, blank=True, currency_field_name='salary_currency')
    salary_per = models.CharField(
        max_length=16, choices=SALARY_PER_CHOICES, default='year'
    )
    bonus_system = models.TextField(blank=True)
    probation_period_months = models.PositiveIntegerField(blank=True, null=True)
    work_location = models.CharField(max_length=128, blank=True)
    working_hours = models.TextField(blank=True)
    break_time_mins = models.PositiveIntegerField(blank=True, null=True)
    flexitime_eligibility = models.CharField(
        max_length=12, blank=True, choices=JobFlexitimeEligibility.get_choices(),
    )
    telework_eligibility = models.CharField(
        max_length=8,
        default=JobTeleworkEligibility.ONSITE.key,
        choices=JobTeleworkEligibility.get_choices(),
        blank=True,
        null=True,
    )
    overtime_conditions = models.TextField(blank=True)
    paid_leaves = models.PositiveIntegerField(blank=True, null=True)
    additional_leaves = models.TextField(blank=True)
    social_insurances = ArrayField(
        models.CharField(max_length=21, choices=JobSocialInsurances.get_choices()),
        blank=True,
        default=list,
    )
    commutation_allowance = models.TextField(blank=True)
    other_benefits = ArrayField(
        models.CharField(max_length=10, choices=JobOtherBenefits.get_choices()),
        blank=True,
        default=list,
    )

    class Meta:
        abstract = True


class PrivateJobPosting(BaseJob):
    class PublicManager(models.Manager):
        def get_queryset(self):
            """Filter out Jobs without uuid and not published."""
            return super().get_queryset().filter(public_uuid__isnull=False)

    job = models.OneToOneField(
        'Job', on_delete=models.CASCADE, related_name='private_posting'
    )
    public_uuid = models.UUIDField(null=True, blank=True, default=None, unique=True)

    skills = models.ManyToManyField('Tag', blank=True, through='PrivateJobPostingSkill')

    objects = models.Manager()
    public_objects = PublicManager()

    @property
    def is_enabled(self):
        return self.public_uuid is not None


class CareerSiteJobPosting(BaseJob):
    class PublicManager(models.Manager):
        def get_queryset(self):
            """Filter out Jobs without uuid and not published."""
            return super().get_queryset().filter(is_enabled=True)

    job = models.OneToOneField(
        'Job', on_delete=models.CASCADE, related_name='career_site_posting'
    )
    is_enabled = models.BooleanField(default=True)

    skills = models.ManyToManyField(
        'Tag', blank=True, through='CareerSiteJobPostingSkill'
    )

    objects = models.Manager()
    public_objects = PublicManager()

    @property
    def slug(self):
        return slugify(f"{self.title}-{self.job_id}")

    def get_public_url(self):
        return reverse(
            'career_site_job_page',
            kwargs={
                'slug': self.job.organization.career_site_slug,
                'job_slug': self.slug,
            },
        )


@reversion.register()
class Job(BaseJob):
    openings_count = models.IntegerField(default=1)
    owner = models.ForeignKey(User, models.PROTECT, 'owned_jobs')

    agencies = models.ManyToManyField(Agency, blank=True, through='JobAgencyContract')
    _managers = models.ManyToManyField(
        User, blank=True, related_name='manager_for_jobs'
    )

    _assignees = models.ManyToManyField(
        User, blank=True, related_name='assigned_to_jobs', through='JobAssignee'
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='assigned_jobs'
    )

    organization = GenericForeignKey('org_content_type', 'org_id')
    org_content_type = models.ForeignKey(
        ContentType,
        limit_choices_to=(
            Q(app_label='core', model='agency') | Q(app_label='core', model='client')
        ),
        on_delete=models.CASCADE,
    )
    org_id = GfkLookupField('org_content_type')

    country = models.CharField(max_length=128, choices=COUNTRY_CHOICES)
    priority = models.BooleanField(default=False)
    status = models.CharField(
        max_length=16, choices=JOB_STATUS_CHOICES, default=DEFAULT_JOB_STATUS
    )
    published = models.BooleanField(default=False)  # draft/published

    closed_at = models.DateTimeField(blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)

    contract_type = models.CharField(
        max_length=32, blank=True, choices=JobContractTypes.get_choices()
    )

    work_experience = models.CharField(
        max_length=16,
        blank=True,
        choices=JobWorkExperience.get_choices(),
        default=JobWorkExperience.NONE.key,
    )

    target_hiring_date = models.DateField(blank=True, null=True)

    recruiters = models.ManyToManyField(
        'User', related_name='primary_jobs', blank=True,
    )

    tier_one_companies = models.TextField(blank=True)
    tier_two_companies = models.TextField(blank=True)

    zoho_id = models.CharField(max_length=32, blank=True, default='')
    zoho_data = models.JSONField(null=True, blank=True)

    department = models.CharField(max_length=128, blank=True, default='')
    reason_for_opening = models.CharField(
        max_length=12, blank=True, choices=JobReasonForOpening.get_choices(),
    )
    educational_level = models.CharField(
        max_length=12, blank=True, choices=JobEducationalLevel.get_choices(),
    )
    hiring_process = models.TextField(blank=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        """Return the string representation of the Job object."""
        return self.title

    def set_filled_if_no_openings(self, should_save=True):
        if self.get_hired_count() >= self.openings_count:
            self.status = JobStatus.FILLED.key
            self.closed_at = now()

            if should_save:
                self.save()

            return True
        return False

    def get_hired_count(self):  # to avoid conflict with annotation
        return self.proposals.filter(
            status__stage=ProposalStatusStage.HIRED.key,
        ).count()

    def get_hired_candidates(self):  # to avoid conflict with annotation
        return [
            p.candidate
            for p in self.proposals.filter(status__stage=ProposalStatusStage.HIRED.key,)
        ]

    @property
    def created_by(self):
        return self.owner

    @property
    def managers(self):
        """Return a QuerySet of all Job managers."""
        return self._managers.all()

    @property
    def assignees(self):
        return self._assignees.all()

    @property
    def location(self):
        location = '%s, %s' % (get_country_name(self.country), self.work_location)
        return location.strip(', ')

    @property
    def public_uuid(self):
        try:
            return self.private_posting.public_uuid
        except PrivateJobPosting.DoesNotExist:
            return None

    @property
    def is_private_posting_enabled(self):
        try:
            return self.private_posting.is_enabled
        except PrivateJobPosting.DoesNotExist:
            return None

    @property
    def is_career_site_posting_enabled(self):
        try:
            return self.career_site_posting.is_enabled
        except CareerSiteJobPosting.DoesNotExist:
            return None

    @property
    def has_enabled_postings(self):
        return self.is_private_posting_enabled or self.is_career_site_posting_enabled

    def get_absolute_url(self):
        return reverse('job', kwargs={'job_id': self.id})

    def candidates(self):
        """Return all Candidates linked via Proposals to this Job."""
        return [p.candidate for p in self.proposals.all()]

    def assign_manager(self, user):
        """Add a User to the Managers for this Job."""
        self._managers.add(user)

    def set_managers(self, users):
        """Remove old, set provided Users to be Managers for this Job."""
        self._managers.set(users)

    def withdraw_manager(self, user):
        """Remove the User from the Managers of this Job."""
        self._managers.remove(user)

    def assign_agency(self, agency):
        """Add Agency to list of assigned agencies."""
        JobAgencyContract.objects.create(job=self, agency=agency)

    def set_agencies(self, agencies):
        """Set assigned agencies list."""
        for agency in agencies:
            JobAgencyContract.objects.update_or_create(
                job=self, agency=agency, defaults=dict(is_active=True)
            )

        JobAgencyContract.objects.filter(job=self).exclude(agency__in=agencies).update(
            is_active=False
        )

    def withdraw_agency(self, agency):
        """Remove Agency from list of assigned agencies."""
        JobAgencyContract.objects.filter(job=self, agency=agency).delete()

    def assign_member(self, user):
        """Add a User to the Assignees for this Job."""
        if not hasattr(user.profile, 'agency'):
            raise TypeError(
                'User should be one of Recruiter, '
                'Agency Manager or Agency Administrator.'
            )

        JobAssignee.objects.create(job=self, user=user)

    def set_members(self, users):
        """Remove old, set provided Users to be Assignees for this Job."""
        for u in users:
            if not hasattr(u.profile, 'agency'):
                raise TypeError(
                    'User should be one of Recruiter, '
                    'Agency Manager or Agency Administrator.'
                )

            JobAssignee.objects.update_or_create(job=self, user=u)

        JobAssignee.objects.filter(job=self).exclude(user__in=users).delete()

    def withdraw_member(self, user):
        """Remove the User from the Assignees of this Job."""
        JobAssignee.objects.filter(job=self, user=user).delete()

    def set_recruiters(self, users):
        self.recruiters.set(users)

    def import_longlist(self, actor, from_job, candidates):
        proposals = Proposal.longlist.filter(
            Q(job=from_job, candidate__in=candidates)
            & ~Q(
                candidate__in=Proposal.objects.filter(
                    job=self, candidate__in=candidates
                ).values_list('candidate')
            )
        )
        default_status = ProposalStatus.longlist.filter(
            stage=ProposalStatusStage.ASSOCIATED.key
        ).first()

        copied_proposals = []
        for proposal in proposals:
            copy = Proposal(
                job=self,
                candidate=proposal.candidate,
                status=default_status,
                created_by=actor,
                status_last_updated_by=actor,
            )

            copied_proposals.append(copy)
        Proposal.objects.bulk_create(copied_proposals)

    def create_default_interview_templates(self):
        for interview_template in (
            apps.get_model('core', 'InterviewTemplate')
            .objects.filter(default=True)
            .all()
        ):
            apps.get_model('core', 'JobInterviewTemplate').objects.get_or_create(
                job_id=self.id,
                interview_type=interview_template.interview_type,
                order=interview_template.default_order,
            )


class JobAssignee(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:  # noqa
        unique_together = ('job', 'user')


class JobAgencyContract(models.Model):
    job = models.ForeignKey(
        Job, on_delete=models.CASCADE, related_name='agency_contracts'
    )
    agency = models.ForeignKey(
        Agency, on_delete=models.CASCADE, related_name='job_contracts'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    is_filled_in = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    signed_at = models.DateField(null=True)

    contract_type = models.CharField(
        choices=JobContractTypes.get_choices(),
        max_length=JobContractTypes.get_db_field_length(),
        null=True,
    )

    contact_person_name = models.CharField(max_length=100, blank=True,)
    industry = models.CharField(
        choices=Industry.get_choices(),
        max_length=Industry.get_db_field_length(),
        null=True,
    )

    class Meta:  # noqa
        unique_together = ('job', 'agency')


def get_jobfile_thumbnail_upload_to(jobfile, filename):
    if not hasattr(jobfile, 'job') or jobfile.job is None:
        raise IntegrityError
    return f'job_file_thumbnails/{jobfile.job.id}/{uuid4()}/{filename}'


def get_jobfile_upload_to(jobfile, filename):
    if not hasattr(jobfile, 'job') or jobfile.job is None:
        raise IntegrityError
    return f'job_files/{jobfile.job.id}/{uuid4()}/{filename}'


class JobFile(models.Model):
    """Represents files attached to the Job."""

    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    title = models.CharField(max_length=64, blank=True)
    file = models.FileField(upload_to=get_jobfile_upload_to, max_length=256)
    thumbnail = models.FileField(blank=True, upload_to=get_jobfile_thumbnail_upload_to,)


class BaseJobQuestion(models.Model):
    text = models.CharField(max_length=1024)

    class Meta:
        ordering = ('id',)
        abstract = True

    def __str__(self):
        """Return the string representation of the JobQuestion object."""
        return self.text


@reversion.register()
class JobQuestion(BaseJobQuestion):
    """Represents a question for job applicant (candidate)."""

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='questions',
        related_query_name='question',
    )


class PrivateJobPostingQuestion(BaseJobQuestion):
    """Represents a question for job applicant (candidate)."""

    job = models.ForeignKey(
        PrivateJobPosting,
        on_delete=models.CASCADE,
        related_name='questions',
        related_query_name='question',
    )


class CareerSiteJobPostingQuestion(BaseJobQuestion):
    """Represents a question for job applicant (candidate)."""

    job = models.ForeignKey(
        CareerSiteJobPosting,
        on_delete=models.CASCADE,
        related_name='questions',
        related_query_name='question',
    )


@reversion.register()
class ProposalQuestion(models.Model):
    proposal = models.ForeignKey(
        'Proposal',
        on_delete=models.CASCADE,
        related_name='questions',
        related_query_name='question',
    )
    text = models.CharField(max_length=1024)
    answer = models.CharField(max_length=1024, blank=True)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.text


class AgencyProfileMixin(ProfileMixin):
    class Meta:  # noqa
        abstract = True

    def apply_jobs_filter(self, queryset):
        """Apply queryset filter to get published Jobs User assigned to."""
        return (
            self.org.apply_own_jobs_filter(queryset)
            | self.org.apply_guest_jobs_filter(queryset)
        ).distinct()

    def can_create_proposal(self, job, candidate):
        """Check if User can create a Proposal for given Job and Candidate."""
        return candidate.organization == self.org and (
            job.organization == self.org or self.org in job.agencies.all()
        )

    @property
    def fee_filter(self):
        """Can be used to filter candidate placements available to user"""

        return Q(agency=self.org)

    @property
    def editable_fee_filter(self):
        """Can be used to filter editable candidate placements available to user"""
        return self.fee_filter


class AgencyAdministrator(AgencyProfileMixin):
    """Represents an Administrator of an Agency."""

    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    teams = models.ManyToManyField('Team', blank=True)
    group_name = 'Agency Administrators'

    def __str__(self):
        return 'Agency Administrator of "{}"'.format(self.agency.name)

    @property
    def contracts_filter(self):
        """Queryset filter to select Contracts linked to an Agency."""
        return Q(agency=self.agency)

    @property
    def editable_fee_filter(self, placement_field_name=None):
        """Can be used to filter editable Fees available to user"""
        return ~Q(status=FeeStatus.APPROVED.key) & self.fee_filter

    @property
    def org(self):
        """Return User Organization: the Agency."""
        return self.agency

    @property
    def notification_types(self):
        """Return Agency Administrator related Notification types."""
        return [
            NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
            NotificationTypeEnum.CLIENT_ASSIGNED_AGENCY_FOR_JOB,
            NotificationTypeEnum.CLIENT_UPDATED_JOB,
            NotificationTypeEnum.CLIENT_CHANGED_PROPOSAL_STATUS,
        ]


class AgencyManager(AgencyProfileMixin):
    """Represents a Manager of an Agency."""

    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    teams = models.ManyToManyField('Team', blank=True)
    group_name = 'Agency Managers'

    def __str__(self):
        return 'Agency Manager of "{}"'.format(self.agency.name)

    @property
    def contracts_filter(self):
        """Queryset filter to select Contracts linked to an Agency."""
        return Q(agency=self.agency)

    @property
    def editable_fee_filter(self, placement_field_name=None):
        """Can be used to filter editable Fees available to user"""
        return ~Q(status=FeeStatus.APPROVED.key) & self.fee_filter

    @property
    def org(self):
        """Return User Organization: the Agency."""
        return self.agency

    @property
    def notification_types(self):
        """Return Agency Manager related Notification types."""
        return [
            NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
            NotificationTypeEnum.CLIENT_ASSIGNED_AGENCY_FOR_JOB,
            NotificationTypeEnum.CLIENT_UPDATED_JOB,
            NotificationTypeEnum.CLIENT_CHANGED_PROPOSAL_STATUS,
        ]


class Recruiter(AgencyProfileMixin):
    """Represents a User which proposes Candidates to Jobs."""

    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    teams = models.ManyToManyField('Team', blank=True)
    group_name = 'Recruiters'

    def __str__(self):
        return 'Recruiter of "{}"'.format(self.agency.name)

    @property
    def fee_filter(self, placement_field_name=None):
        """Can be used to filter candidate placements available to user"""
        return Q(created_by=self.user) | Q(submitted_by=self.user)

    @property
    def editable_fee_filter(self, placement_field_name=None):
        """Can be used to filter editable candidate placements available to user"""
        return ~Q(status__in=LOCKED_PLACEMENT_STATUSES) & self.fee_filter

    def apply_jobs_filter(self, queryset):
        """Apply queryset filter to get published Jobs User assigned to."""
        return (
            super()
            .apply_jobs_filter(queryset)
            .filter(Q(owner=self.user) | Q(_assignees=self.user))
            .distinct()
        )

    def apply_proposals_filter(self, queryset):
        """Apply queryset filter to get available proposals"""
        return (
            super()
            .apply_proposals_filter(queryset)
            .filter(job__in=self.apply_jobs_filter(Job.objects))
        )

    def can_create_proposal(self, job, candidate):
        """Check if User can create a Proposal for given Job and Candidate."""
        return super().can_create_proposal(job, candidate) and (
            job.owner == self.user or self.user in job.assignees.all()
        )

    def can_create_job_file(self, job):
        return super().can_create_job_file(job) and (
            self.user in job.assignees or self.user == job.owner
        )

    @property
    def contracts_filter(self):
        """Queryset filter to select Contracts linked to an Agency."""
        return Q(agency=self.agency)

    @property
    def org(self):
        """Return User Organization: the Agency."""
        return self.agency

    @property
    def notification_types(self):
        """Return Recruiter related Notification types."""
        return [
            NotificationTypeEnum.CLIENT_CREATED_CONTRACT,
            NotificationTypeEnum.CLIENT_ASSIGNED_AGENCY_FOR_JOB,
            NotificationTypeEnum.AGENCY_ASSIGNED_MEMBER_FOR_JOB,
            NotificationTypeEnum.CLIENT_UPDATED_JOB,
            NotificationTypeEnum.CLIENT_CHANGED_PROPOSAL_STATUS,
            NotificationTypeEnum.PROPOSAL_MOVED,
        ]


def get_resume_thumbnail_upload_to(candidate, filename):
    return f'candidate_resume_thumbnails/{candidate.id}/{uuid4()}/{filename}'


def get_resume_upload_to(candidate, filename):
    return f'candidate_resumes/{candidate.id}/{uuid4()}/{filename}'


def get_resume_ja_thumbnail_upload_to(candidate, filename):
    return f'candidate_resume_ja_thumbnails/{candidate.id}/{uuid4()}/{filename}'


def get_resume_ja_upload_to(candidate, filename):
    return f'candidate_resume_ja_files/{candidate.id}/{uuid4()}/{filename}'


def get_cv_ja_thumbnail_upload_to(candidate, filename):
    return f'candidate_cv_ja_thumbnails/{candidate.id}/{uuid4()}/{filename}'


def get_cv_ja_upload_to(candidate, filename):
    return f'candidate_cv_ja_files/{candidate.id}/{uuid4()}/{filename}'


class Choices:
    def __init__(self, *args):
        self.list = list(args)

    def for_dropdown(self):
        result = []
        for value, label in self.list:
            result.append({'value': value, 'label': label})
        return result


class CandidateSources(models.TextChoices):
    EXTERNAL_AGENCIES = ('External Agencies', _('External Agencies'))
    JOB_BOARDS = ('Job Boards', _('Job Boards'))
    REFERRALS = ('Referrals', _('Referrals'))
    DIRECT_APPLY = ('Direct Apply', _('Direct Apply'))
    CAREER_EVENT = ('Career Event', _('Career Event'))
    BIC = (('BIC', _('BIC')),)


CANDIDATE_SOURCE_DETAILS_CHOICES = Choices(
    ('LinkedIn', _('LinkedIn')),
    ('BizReach', _('BizReach')),
    ('EnJapan', _('EnJapan')),
    ('Doda', _('Doda')),
    (None, _('Other')),
)

CANDIDATE_SOURCE_DETAILS_PROPERTIES = {
    'Job Boards': {
        'label': _('Job Board'),
        'labelNew': _('Other Job Board'),
        'choices': CANDIDATE_SOURCE_DETAILS_CHOICES.for_dropdown(),
    }
}


@reversion.register()
class EducationDetail(models.Model):
    candidate = models.ForeignKey(
        'Candidate', on_delete=models.CASCADE, related_name='education_details'
    )

    institute = models.CharField(max_length=128, blank=True)
    department = models.CharField(max_length=128, blank=True)
    degree = models.CharField(max_length=128, blank=True)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    currently_pursuing = models.BooleanField(default=False)


@reversion.register()
class ExperienceDetail(models.Model):
    candidate = models.ForeignKey(
        'Candidate', on_delete=models.CASCADE, related_name='experience_details'
    )

    occupation = models.CharField(max_length=128, blank=True)
    company = models.CharField(max_length=128, blank=True)
    summary = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    currently_pursuing = models.BooleanField(default=False)


class CandidateManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(archived=False)


class CandidateInternalStatus(StatusEnum):
    NOT_CONTACTED = _('Not contacted')
    CONTACTED = _('Contacted')
    GENERALLY_UNQUALIFIED = _('Generally unqualified')
    ACTIVE = _('Active')


def get_candidate_photo_file_path(instance, filename):
    return f'candidate/{instance.id}/photo/{uuid4()}/{filename}'


@reversion.register()
class CandidateCertification(models.Model):
    CERTIFICATION_CHOICES = (
        ('toeic', _('TOEIC')),
        ('jlpt', _('JLPT')),
        ('toefl', _('TOEFL')),
        ('other', _('Other Cerfication')),
    )
    candidate = models.ForeignKey(
        'Candidate', on_delete=models.CASCADE, related_name='certifications'
    )
    certification = models.CharField(max_length=5, choices=CERTIFICATION_CHOICES)
    certification_other = models.CharField(max_length=32, blank=True)
    score = models.CharField(max_length=16, blank=True)

    @property
    def certification_display(self):
        if self.certification == 'other':
            return self.certification_other
        return self.certification


@reversion.register(
    follow=(
        'education_details',
        'experience_details',
        'notes',
        'files',
        'certifications',
    )
)
class Candidate(models.Model):
    """Represents a future employee which Agency propose to a Client."""

    EMPLOYMENT_CHOICES = (
        ('notemployed', _('Unemployed')),
        ('fulltime', _('Permanent Employee')),
        ('fixedterm', _('Fixed-term Contract Employee')),
        ('temporary', _('Part-time Employee')),
        ('businessowner', _('Business Owner')),
        ('dispatched', _('Dispatched')),
        ('freelance', _('Freelance')),
    )

    GENDER_CHOICES = (
        ('male', _('Male')),
        ('female', _('Female')),
        ('other', _('Other')),
    )

    MANAGEMENT_SCOPE_CHOICES = (
        ('individual', _('Individual Contributor')),
        ('team', _('Team')),
        ('division', _('Division')),
        ('country', _('Country')),
        ('region', _('Region')),
        ('global', _('Global')),
    )

    OTHER_DESIRED_BENEFIT_CHOICES = (
        ('sign_on_bonus', _('One-Time Sign On Bonus')),
        ('relocation', _('Relocation')),
        ('holidays', _('Minimum Number of Holidays Per Year')),
        ('schooling', _('Schooling for Kids')),
        ('company_car', _('Company Car')),
        ('training', _('Company Sponsored Training')),
        ('housing', _('Housing Support')),
        ('equity', _('Equity')),
        ('tax_equalization', _('Tax Equalization')),
        ('special_insurance', _('Special Insurance')),
        ('other', _('Other')),
    )

    NOTICE_PERIOD_CHOICES = (
        ('immediate', _('Immediate')),
        ('two_weeks', _('2 Weeks')),
        ('one_month', _('1 Month')),
        ('two_months', _('2 Months')),
        ('three_months', _('3+ Months')),
    )

    JOB_CHANGE_URGENCY_CHOICES = (
        ('urgent', _('Urgent')),
        ('actively_looking', _('Actively Looking')),
        ('passively_looking', _('Passively Looking')),
        ('not_looking', _('Not Looking')),
    )

    PLATFORM_CHOICES = (
        ('linkedin', _('LinkedIn')),
        ('facebook', _('Facebook')),
        ('biz_reach', _('Biz Reach')),
        ('github', _('Github')),
        ('careercross', _('CareerCross')),
        ('corporate_site', _('Corporate Website')),
        ('other', _('Other')),
    )

    org_content_type = models.ForeignKey(
        ContentType,
        limit_choices_to=(
            Q(app_label='core', model='agency') | Q(app_label='core', model='client')
        ),
        null=True,
        on_delete=models.CASCADE,
    )
    org_id = GfkLookupField('org_content_type')
    organization = GenericForeignKey('org_content_type', 'org_id')

    photo = models.ImageField(
        blank=True, null=True, upload_to=get_candidate_photo_file_path
    )

    first_name = models.CharField(max_length=128, blank=True)
    middle_name = models.CharField(max_length=128, blank=True, default='')
    last_name = models.CharField(max_length=128, blank=True)

    first_name_kanji = models.CharField(max_length=128, blank=True, default='')
    last_name_kanji = models.CharField(max_length=128, blank=True, default='')

    first_name_katakana = models.CharField(max_length=128, blank=True, default='')
    last_name_katakana = models.CharField(max_length=128, blank=True, default='')

    birthdate = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, blank=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    nationality = models.CharField(max_length=128, blank=True)

    source = models.CharField(max_length=128, blank=True)
    source_details = models.CharField(max_length=128, blank=True,)

    email = models.EmailField(default='', blank=True)
    secondary_email = models.EmailField(default='', blank=True)
    phone = PhoneNumberField(blank=True, default='')
    secondary_phone = PhoneNumberField(blank=True)

    current_street = models.CharField(max_length=128, blank=True)
    current_city = models.CharField(max_length=128, blank=True, default='')
    current_postal_code = models.CharField(max_length=128, blank=True)
    current_prefecture = models.CharField(max_length=128, blank=True)
    current_country = models.CharField(
        max_length=128, choices=COUNTRY_CHOICES, blank=True
    )

    current_company = models.CharField(max_length=128, blank=True, default='')
    current_position = models.CharField(max_length=256, blank=True, default='')
    potential_locations = models.CharField(max_length=256, blank=True, default='')

    tax_equalization = models.BooleanField(null=True, blank=True)
    max_num_people_managed = models.PositiveIntegerField(null=True, blank=True)
    other_desired_benefits = ArrayField(
        models.CharField(max_length=17, choices=OTHER_DESIRED_BENEFIT_CHOICES),
        blank=True,
        default=list,
    )
    other_desired_benefits_others_detail = models.CharField(max_length=128, blank=True)
    notice_period = models.CharField(
        max_length=12, choices=NOTICE_PERIOD_CHOICES, blank=True
    )
    job_change_urgency = models.CharField(
        max_length=17, choices=JOB_CHANGE_URGENCY_CHOICES, blank=True
    )
    expectations_details = models.TextField(blank=True)
    employment_status = models.CharField(
        max_length=16, choices=EMPLOYMENT_CHOICES, blank=True
    )

    linkedin_url = models.URLField(blank=True, default='')
    linkedin_slug = models.CharField(max_length=256, null=True, blank=True)

    github_url = models.URLField(blank=True, default='')
    website_url = models.URLField(blank=True, default='')
    twitter_url = models.URLField(blank=True, default='')

    summary = models.TextField(default='', blank=True)

    fulltime = models.BooleanField(default=False)
    parttime = models.BooleanField(default=False)

    local = models.BooleanField(default=False)
    remote = models.BooleanField(default=False)

    # Salary section
    current_salary_breakdown = models.CharField(max_length=256, blank=True, default='')

    current_salary = MoneyField(
        null=True, blank=True, currency_field_name='current_salary_currency'
    )
    current_salary_variable = MoneyField(
        null=True, blank=True, currency_field_name='current_salary_currency'
    )

    salary = MoneyField(null=True, blank=True)

    def _total_annual_salary_iterator(self):
        yield self.current_salary
        yield self.current_salary_variable

    @property
    def total_annual_salary(self):
        result = None
        for salary_part in self._total_annual_salary_iterator():
            if salary_part is None:
                continue
            result = salary_part if result is None else result + salary_part

        return result.amount if result else None

    @property
    def import_source(self):
        if self.zoho_id:
            return 'Zoho'
        if self.linkedin_data_set.exists():
            return 'LinkedIn'
        return None

    reason_for_job_changes = models.CharField(max_length=256, blank=True, default='')

    languages = models.ManyToManyField(Language, blank=True)
    resume = models.FileField(
        help_text='English Resume',
        upload_to=get_resume_upload_to,
        blank=True,
        null=True,
    )
    resume_thumbnail = models.FileField(
        upload_to=get_resume_thumbnail_upload_to, blank=True, null=True,
    )

    resume_ja = models.FileField(
        help_text='Rirekisho', upload_to=get_resume_ja_upload_to, blank=True, null=True
    )
    resume_ja_thumbnail = models.FileField(
        upload_to=get_resume_ja_thumbnail_upload_to, blank=True, null=True,
    )
    cv_ja = models.FileField(
        help_text='Shokumu-keirekisho',
        upload_to=get_cv_ja_upload_to,
        blank=True,
        null=True,
    )
    cv_ja_thumbnail = models.FileField(
        upload_to=get_cv_ja_thumbnail_upload_to, blank=True, null=True,
    )

    zoho_id = models.CharField(max_length=32, blank=True, default='')
    zoho_data = models.JSONField(null=True, blank=True)

    li_data = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_candidates',
    )

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_updated_candidates',
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_candidates',
        null=True,
        blank=True,
    )

    archived = models.BooleanField(default=False)
    original = models.ForeignKey(
        to='core.Candidate', null=True, blank=True, on_delete=models.SET_NULL,
    )

    tags = models.ManyToManyField('Tag', blank=True, through='CandidateTag')

    objects = CandidateManager()
    archived_objects = models.Manager()
    internal_status = models.CharField(
        max_length=30,
        choices=CandidateInternalStatus.get_choices(),
        default=CandidateInternalStatus.NOT_CONTACTED.key,
    )
    is_met = models.BooleanField(default=False)

    is_client_contact = models.BooleanField(default=False)

    # researcher's fields
    name_collect = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='name_collected_candidates',
    )
    mobile_collect = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mobile_collected_candidates',
    )
    # end researcher's fields

    activator = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activated_candidates',
    )
    skill_domain = models.ForeignKey(
        SkillDomain,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidates',
    )
    lead_consultant = models.ForeignKey(
        User,
        related_name='consulted_candidates',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    support_consultant = models.ForeignKey(
        User,
        related_name='supported_candidates',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    referred_by = models.ForeignKey(
        User,
        related_name='referred_candidates',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    industry = models.CharField(
        max_length=Industry.get_db_field_length(),
        blank=True,
        choices=Industry.get_choices(),
    )
    department = models.TextField(blank=True)
    client_expertise = models.TextField(blank=True)
    client_brief = models.TextField(blank=True)
    push_factors = models.TextField(blank=True)
    pull_factors = models.TextField(blank=True)
    companies_already_applied_to = models.TextField(blank=True)
    companies_applied_to = models.TextField(blank=True)
    platform = models.CharField(max_length=16, choices=PLATFORM_CHOICES, blank=True)
    platform_other_details = models.CharField(max_length=128, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('org_content_type', 'org_id', 'zoho_id'),
                condition=Q(archived=False) & ~Q(zoho_id=''),
                name='unique_zoho_id',
            ),
            models.UniqueConstraint(
                fields=('org_content_type', 'org_id', 'linkedin_slug'),
                condition=Q(archived=False) & ~Q(linkedin_slug=''),
                name='unique_linkedin_slug',
            ),
            models.UniqueConstraint(
                fields=('org_content_type', 'org_id', 'email'),
                condition=Q(archived=False) & ~Q(email=''),
                name='unique_email',
            ),
            models.UniqueConstraint(
                fields=('org_content_type', 'org_id', 'secondary_email'),
                condition=Q(archived=False) & ~Q(secondary_email=''),
                name='unique_secondary_email',
            ),
        ]

    def clean_fields(self, exclude=tuple(), check_zoho_and_linkedin=True):
        """Validate constraints"""
        # TODO: may be optimized: remove query and create standalone Email model
        # Partial unique constraints can't be validated automatically
        super().clean_fields(exclude=tuple(exclude) + ('original',))
        error_dict = {}
        candidates = Candidate.objects.filter(~Q(pk=self.pk))
        current_org_candidates = candidates.filter(
            org_content_type=self.org_content_type, org_id=self.org_id
        )

        if check_zoho_and_linkedin:
            # ZohoID
            if current_org_candidates.filter(
                Q(zoho_id=self.zoho_id) & ~Q(zoho_id='')
            ).exists():
                error_dict.update(
                    {'zoho_id': _('Candidate with this Zoho ID already exists.')}
                )

            # LinkedIn
            if current_org_candidates.filter(
                Q(linkedin_slug=self.linkedin_slug)
                & ~Q(linkedin_slug='')
                & ~Q(linkedin_slug=None)
            ).exists():
                error_dict.update(
                    {'linkedin_url': _('Candidate with this LinkedIn already exists.')}
                )

        # Emails
        if current_org_candidates.filter(get_unique_emails_filter(self.email)).exists():
            error_dict.update({'email': _('Email already in use.')})

        if current_org_candidates.filter(
            get_unique_emails_filter(self.secondary_email)
        ).exists():
            error_dict.update({'secondary_email': _('Email already in use.')})

        if self.email == self.secondary_email and self.email != '':
            error_dict.update(
                {
                    'email': _('Emails must be unique.'),
                    'secondary_email': _('Emails must be unique.'),
                }
            )

        if self.original:
            archived_candidates = Candidate.archived_objects.filter(~Q(pk=self.pk))
            original_exists = archived_candidates.filter(
                org_content_type=self.org_content_type,
                org_id=self.org_id,
                pk=self.original.pk,
            ).exists()
            if not original_exists:
                error_dict.update(
                    {
                        'original': _(
                            f'candidate with id {self.original.pk} does not exist.'
                        )
                    }
                )

        if error_dict:
            raise ValidationError(error_dict)

    def save(self, *args, turn_on_clean_fields=True, **kwargs):
        self.linkedin_slug = parse_linkedin_slug(self.linkedin_url)

        if turn_on_clean_fields:
            self.full_clean()

        return super().save(*args, **kwargs)

    def __str__(self):
        """Return the string representation of the Agency object."""
        return self.name

    @property
    def name(self):
        """Return full name of the Candidate."""
        return ' '.join([self.first_name, self.last_name]).strip()

    @property
    def name_ja(self):
        """Return full name of the Candidate."""
        return ' '.join(
            [
                self.first_name_kanji,
                self.last_name_kanji,
                self.first_name_katakana,
                self.last_name_katakana,
            ]
        ).strip()

    @property
    def linkedin_data(self):
        data = self.linkedin_data_set.order_by('-created_at').first()
        return data.data if data else None

    @property
    def resume_file_name(self):
        if self.resume:
            return os.path.basename(self.resume.name)
        else:
            return None

    def get_note(self, org):
        """Return the related CandidateNote for the organization."""
        note = org.candidate_notes.filter(candidate=self).first()
        return note.text if note else ''

    def set_note(self, org, text):
        """Create, update or delete the CandidateNote."""
        CandidateNote.objects.update_or_create(
            candidate=self,
            content_type=ContentType.objects.get_for_model(org),
            object_id=org.pk,
            defaults={'text': text or ''},
        )

    def get_absolute_url(self):
        return reverse('candidate_page', kwargs={'candidate_id': self.id})


class CandidateLinkedinData(models.Model):
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name='linkedin_data_set'
    )

    data = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


@reversion.register()
class CandidateNote(models.Model):
    """Represents a note for the Candidate, unique across the organization."""

    text = models.TextField()
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name='notes'
    )
    content_type = models.ForeignKey(
        ContentType,
        limit_choices_to=(
            Q(app_label='core', model='agency') | Q(app_label='core', model='client')
        ),
        on_delete=models.CASCADE,
    )
    object_id = GfkLookupField('content_type')
    organization = GenericForeignKey('content_type', 'object_id')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:  # noqa
        unique_together = ('candidate', 'content_type', 'object_id')

    def __str__(self):
        """Return the string representation of the CandidateNote object."""
        return 'Note for {} by {}'.format(self.candidate, self.organization)


class ProposalStatusShortlistManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return (
            super()
            .get_queryset(*args, **kwargs)
            .filter(stage__in=ProposalStatusStage.get_shortlist_keys())
        )


class ProposalStatusLonglistManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return (
            super()
            .get_queryset(*args, **kwargs)
            .filter(stage__in=ProposalStatusStage.get_longlist_keys())
        )


class ProposalStatus(models.Model):
    """Proposal Status."""

    stage = models.CharField(max_length=32, choices=ProposalStatusStage.get_choices())
    group = models.CharField(max_length=64, choices=ProposalStatusGroup.get_choices())
    status = models.CharField(max_length=128)

    default = models.BooleanField(
        default=False, help_text='This status will be added for each new client'
    )
    default_order = models.PositiveIntegerField(null=True, blank=True)

    objects = models.Manager()
    shortlist = ProposalStatusShortlistManager()
    longlist = ProposalStatusLonglistManager()

    deal_stage = models.CharField(
        max_length=32,
        choices=ProposalDealStages.get_choices(),
        default=ProposalDealStages.OUT_OF.key,
    )

    class Meta:
        verbose_name_plural = 'Proposal statuses'

    def __str__(self):
        return '{} - {}'.format(self.group, self.status)

    def clean(self):
        if self.default and self.default_order is None:
            raise ValidationError('Default order is required for default statuses.')


class ClientProposalStatusManager(models.Manager):
    def get_queryset(self):
        """Returns only statuses for clients"""
        return (
            super()
            .get_queryset()
            .filter(status__group__in=ProposalStatusGroup.get_client_org_status_keys())
        )


class AgencyProposalStatusManager(models.Manager):
    def get_queryset(self):
        """Returns only statuses for agency"""
        return (
            super()
            .get_queryset()
            .filter(status__group__in=ProposalStatusGroup.get_agency_org_status_keys())
        )


class OrganizationProposalStatus(models.Model):
    """Proposal Status available for a organisation"""

    org_content_type = models.ForeignKey(
        ContentType,
        limit_choices_to=(
            Q(app_label='core', model='agency') | Q(app_label='core', model='client')
        ),
        null=True,
        on_delete=models.CASCADE,
    )
    org_id = GfkLookupField('org_content_type', null=True)
    organization = GenericForeignKey('org_content_type', 'org_id')
    status = models.ForeignKey(ProposalStatus, on_delete=models.PROTECT)

    order = models.PositiveIntegerField()

    objects = models.Manager()
    client_objects = ClientProposalStatusManager()
    agency_objects = AgencyProposalStatusManager()

    class Meta:
        ordering = ('order',)
        verbose_name_plural = 'Company proposal statuses'


class ProposalComment(models.Model):
    """Comments for Proposals left by Users, also Proposal status updates."""

    author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    proposal = models.ForeignKey('Proposal', on_delete=models.CASCADE)
    proposal_status = models.ForeignKey(
        'ProposalStatus', null=True, on_delete=models.PROTECT
    )
    text = models.TextField()
    public = models.BooleanField(default=False)
    system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return the string representation of the Proposal Comment."""
        return 'Comment on {}'.format(self.proposal)

    @classmethod
    def create_activity(
        cls, user, proposal, comment, system=False, public=False, format_kwargs=None,
    ):
        if format_kwargs:
            comment_texts = get_proposal_comment(comment, **format_kwargs)
        else:
            comment_texts = get_proposal_comment(comment)

        cls.objects.create(
            author=user,
            proposal=proposal,
            system=system,
            public=public,
            **comment_texts,
        )


class CandidateComment(models.Model):
    author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    candidate = models.ForeignKey('Candidate', on_delete=models.CASCADE)
    text = models.TextField()
    public = models.BooleanField(default=False)
    system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment on {self.candidate}"

    def _mentioned_users_pattern(self):
        return re.compile(r'@\[(.*?)\]\((\d+)\)')

    @property
    def formatted_text(self):
        if self.text:
            return self._mentioned_users_pattern().sub(r'\1', self.text)
        return self.text

    def get_mentioned_users(self):
        user_ids = [
            id for name, id in self._mentioned_users_pattern().findall(self.text)
        ]
        return User.objects.filter(id__in=user_ids)


class ShortlistProposalsManager(models.Manager):
    def get_queryset(self):
        """Returns only proposals with shortlisted candidates"""
        return (
            super()
            .get_queryset()
            .filter(status__stage__in=ProposalStatusStage.get_shortlist_keys())
        )


class LonglistProposalsManager(models.Manager):
    def get_queryset(self):
        """Returns only proposals with longlisted candidates"""
        return (
            super()
            .get_queryset()
            .filter(status__stage__in=ProposalStatusStage.get_longlist_keys())
        )


@reversion.register()
class Proposal(models.Model):
    """Represent a link between the Candidate and the Job.

    Recruiters should be able to propose a Candidate of their Agency to
    Jobs, created by Clients. Client users: Hiring Manager and Talent Associate
    should be able to approve or deny this Proposal.
    """

    MIN_SUITABILITY = 1
    MAX_SUITABILITY = 5

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='proposals',)
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name='proposals',
    )
    is_direct_application = models.BooleanField(default=False)
    current_interview = models.ForeignKey(
        'ProposalInterview',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )

    status = models.ForeignKey(ProposalStatus, on_delete=models.PROTECT)
    status_last_updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='status_last_updated_proposals',
        null=True,
    )
    is_rejected = models.BooleanField(default=False)

    suitability = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_SUITABILITY),
            MaxValueValidator(MAX_SUITABILITY),
        ],
        null=True,
    )

    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='created_proposals'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    moved_from_job = models.ForeignKey(
        Job, on_delete=models.SET_NULL, related_name='moved_proposals', null=True,
    )
    moved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='moved_proposals', null=True,
    )

    decline_reasons = models.ManyToManyField('ReasonDeclineCandidateOption')

    reason_declined_description = models.CharField(blank=True, max_length=255)

    reasons_not_interested = models.ManyToManyField(
        'ReasonNotInterestedCandidateOption'
    )

    reason_not_interested_description = models.CharField(blank=True, max_length=255)

    objects = models.Manager()
    shortlist = ShortlistProposalsManager()
    longlist = LonglistProposalsManager()

    class Meta:
        unique_together = ('job', 'candidate')

    def save(self, *args, **kwargs):
        if self.id is None:  # if created
            if self.status_last_updated_by is None and hasattr(self, 'created_by'):
                self.status_last_updated_by = self.created_by

        # if no job, should fail on not-null check
        if (
            not hasattr(self, 'status')
            and hasattr(self, 'job')
            and hasattr(self, 'created_by')
        ):
            self.set_status_by_group(
                # TODO: possibly on automation
                ProposalStatusStage.ASSOCIATED.key,
                self.created_by,
            )

        return super().save(*args, **kwargs)

    def __str__(self):
        """Return the string representation of the Proposal object."""
        return '{} - {}'.format(self.job, self.candidate)

    @property
    def sub_stage(self):
        if (
            self.status.stage == ProposalStatusStage.INTERVIEWING.key
            and self.current_interview
        ):
            if self.current_interview == self.interviews.order_by('order').last():
                return ProposalStatusSubStage.FINAL_INTERVIEW.key
            elif self.current_interview == self.interviews.order_by('order').first():
                return ProposalStatusSubStage.FIRST_INTERVIEW.key
            else:
                return ProposalStatusSubStage.IN_PROCESS.key
        return None

    @property
    def source(self):
        """Return the party which created a Proposal."""
        return self.candidate.organization

    def get_absolute_url(self):
        return reverse(
            'proposal_page', kwargs={'job_id': self.job.id, 'proposal_id': self.id}
        )

    def get_interviewers(self):
        return User.objects.filter(
            id__in=self.interviews.values_list('interviewer', flat=True)
        )

    def get_or_set_current_interview_maybe(self):
        if not self.current_interview:
            self.current_interview = self.interviews.filter(
                current_schedule__status=ProposalInterviewSchedule.Status.TO_BE_SCHEDULED.value
            ).first()
            self.save(update_fields=['current_interview'])
        return self.current_interview

    def proceed_to_next_interview_or_none(self):
        if not self.current_interview:
            return None
        interview = self.current_interview
        self.current_interview = interview.next()
        self.save(update_fields=['current_interview'])
        return self.current_interview

    def create_default_interviews(self):
        interview_templates = self.job.interview_templates.all()
        for template in interview_templates:
            ProposalInterview.objects.get_or_create(
                proposal=self,
                interview_type=template.interview_type,
                order=template.order,
                description=template.description,
                interviewer=template.interviewer,
                created_by=self.job.owner,
            )
        self.get_or_set_current_interview_maybe()

    def create_default_questions(self, posting=None):
        question_templates = []
        if posting:
            question_templates = posting.questions.all()
        else:
            question_templates = self.job.questions.all()
        for template in question_templates:
            ProposalQuestion.objects.get_or_create(
                proposal=self, text=template.text,
            )

    def set_status(self, stage, group, changed_by=None):
        org_status = self.job.organization.proposal_statuses.filter(
            status__stage=stage, status__group=group
        ).first()

        if org_status is None:
            raise ProposalStatus.DoesNotExist()

        status = org_status.status
        self.status = status
        self.status_last_updated_by = changed_by
        self.update_status_history(status, changed_by)

        self.save(update_fields=['status', 'status_last_updated_by'])

    def set_status_by_group(
        self, stage, changed_by, to_history=False, group=None, should_save=False
    ):
        """
        Finds status with chosen group and assigns it to current proposal
        if to_history is True - updates history
        """
        if stage in ProposalStatusStage.get_longlist_keys():
            statuses = ProposalStatus.objects.filter(stage=stage).all()
            if group:
                status = statuses.filter(group=group).first()
            else:
                status = statuses.first()
        else:
            org_statuses = self.job.organization.proposal_statuses.filter(
                status__stage=stage
            ).all()
            if group:
                org_status = org_statuses.filter(status__group=group).first()
            else:
                org_status = org_statuses.first()

            status = org_status.status if org_status else None

        if status is None:
            raise ProposalStatus.DoesNotExist()

        old_status = getattr(self, 'status', None)
        self.status = status
        self.status_last_updated_by = changed_by
        if should_save:
            self.save(update_fields=['status', 'status_last_updated_by'])

        if to_history:
            self.update_status_history(status, changed_by)

        if status.stage == ProposalStatusStage.SUBMISSIONS.key:
            from core.notifications import notify_proposal_submitted_to_hiring_manager

            notify_proposal_submitted_to_hiring_manager(changed_by, self)

        elif status.stage == ProposalStatusStage.HIRED.key:
            from core.notifications import notify_job_is_filled

            is_filled = self.job.set_filled_if_no_openings()
            if is_filled:
                notify_job_is_filled(changed_by, self.job)

        if old_status:
            if old_status != status:
                from core.notifications import notify_client_changed_proposal_status

                notify_client_changed_proposal_status(
                    changed_by,
                    self,
                    {'status': {'from': old_status.id, 'to': status.id}},
                )

            if old_status.stage == ProposalStatusStage.SUBMISSIONS.key:
                if status.group == ProposalStatusGroup.INTERVIEWING.key:
                    from core.notifications import (
                        notify_proposal_approved_rejected_by_hiring_manager,
                    )

                    notify_proposal_approved_rejected_by_hiring_manager(
                        changed_by, self, True
                    )

    def update_status_history(self, status, changed_by):
        """Updates Proposal Status History"""
        ProposalStatusHistory.objects.create(
            proposal=self, status=status, changed_by=changed_by
        )

    def update_activity(self, user, updated=None):
        """Updates proposal activity depends on changed fields"""
        if updated == 'status':
            comment = ProposalCommentTypes.STATUS_CHANGED
            # TODO(ZOO-963)
            public = self.status.stage in ProposalStatusStage.get_shortlist_keys()
            ProposalComment.create_activity(
                user,
                self,
                comment,
                system=True,
                public=public,
                format_kwargs={
                    'status': self.status.status_en or self.status.status,
                    'status_ja': self.status.status_ja or self.status.status,
                },
            )
        elif updated == 'rejected':
            comment = ProposalCommentTypes.REJECTED
            ProposalComment.create_activity(
                user, self, comment, system=True, public=True,
            )

    def decline_same_candidate_proposals(self, user):
        proposals = Proposal.objects.filter(
            Q(
                candidate=self.candidate,
                status__stage__in=ProposalStatusStage.get_shortlist_keys(),
            )
            & ~Q(pk=self.pk)
        )

        if not proposals.count():
            return None

        proposals.update(is_rejected=True)

        for proposal in proposals:
            proposal.update_activity(user, 'rejected')

    def create_comment_placed(self, author):
        ProposalComment.objects.create(
            author=author,
            proposal=self,
            public=False,
            **get_proposal_comment(ProposalCommentTypes.PLACED,),
        )

    def do_action(self, action, user, to_status=None):
        if action == QuickActionVerb.REJECT.key:
            self.is_rejected = True
            from core.notifications import (
                notify_proposal_approved_rejected_by_hiring_manager,
                notify_proposal_is_rejected,
            )

            if self.status.stage == ProposalStatusStage.SUBMISSIONS.key:
                notify_proposal_approved_rejected_by_hiring_manager(user, self, False)
            notify_proposal_is_rejected(user, self)
        elif action == QuickActionVerb.CHANGE_STATUS.key:
            self.set_status_by_group(
                to_status.stage, user, True, to_status.group, should_save=True,
            )
        elif action == QuickActionVerb.PROCEED.key:
            if self.current_interview.order == self.interviews.get_max_order():
                self.set_status_by_group(
                    ProposalStatusStage.OFFERING.key,
                    user,
                    True,
                    ProposalStatusGroup.PENDING_HIRING_DECISION.key,
                )
            self.proceed_to_next_interview_or_none()
        elif action == QuickActionVerb.RESEND.key:
            from core.notifications import notify_interview_schedule_sent

            notify_interview_schedule_sent(
                user, self.current_interview, candidate_only=True
            )
        self.save()


class ProposalStatusHistory(models.Model):
    """History item of proposal status changes."""

    proposal = models.ForeignKey(
        Proposal, on_delete=models.CASCADE, related_name='status_history'
    )

    status = models.ForeignKey(ProposalStatus, on_delete=models.PROTECT)

    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,)

    class Meta:
        ordering = ('id',)


class Notification(models.Model):
    """User web notification."""

    sender = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name='caused_notifications',
        on_delete=models.CASCADE,
    )

    recipient = models.ForeignKey(
        User, blank=False, related_name='notifications', on_delete=models.CASCADE
    )

    verb = models.CharField(max_length=255, choices=NotificationTypeEnum.get_choices())

    timestamp = models.DateTimeField(default=now)
    unread = models.BooleanField(default=True, blank=False)
    emailed = models.BooleanField(default=False)

    actor_content_type = models.ForeignKey(
        ContentType, related_name='notify_actor', on_delete=models.CASCADE
    )
    actor_object_id = models.CharField(max_length=255)
    actor = GenericForeignKey('actor_content_type', 'actor_object_id')

    action_object_content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        related_name='notify_action_object',
        on_delete=models.CASCADE,
    )
    action_object_object_id = models.CharField(max_length=255, blank=True, null=True)
    action_object = GenericForeignKey(
        'action_object_content_type', 'action_object_object_id'
    )

    target_content_type = models.ForeignKey(
        ContentType,
        related_name='notify_target',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    target_object_id = models.CharField(max_length=255, blank=True, null=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')
    explicit_link = models.CharField(max_length=255, null=True)
    context_data = models.JSONField(default=dict, encoder=DjangoJSONEncoder)

    def format_data(self):
        """
        Data available for all notification texts, email or otherwise.
        """
        data = dict(
            actor=self.actor, action_object=self.action_object, target=self.target
        )
        data.update(self.context_data)
        data['actor_name'] = (
            _('You') if self.actor == self.recipient else self.actor.name
        )
        # formatting
        data['datetime'] = datetime_str(self.timestamp, self.recipient)
        if 'link_text' in data:
            data['link_text'] = NotificationLinkText[data['link_text']].value
        return data

    @property
    def text(self):
        return NotificationTypeEnum[self.verb.upper()].value.text.format(
            **self.format_data()
        )

    @property
    def email_subject(self):
        return NotificationTypeEnum[self.verb.upper()].value.email_subject.format(
            **self.format_data()
        )

    @property
    def email_text(self):
        return NotificationTypeEnum[self.verb.upper()].value.email_text.format(
            **self.format_data()
        )

    def __str__(self):
        return f"{self.sender} -> {self.recipient}: {self.verb}"

    @property
    def link(self):
        if self.explicit_link is not None:
            return self.explicit_link

        if self.target:
            return self.target.get_absolute_url()

    @classmethod
    def send(
        cls,
        recipient,
        verb,
        sender=None,
        actor=None,
        action_object=None,
        target=None,
        context_data=None,
        send_via_email=None,
        reply_to=None,
        link=None,
        email_attachments=None,
    ):

        notification = cls.objects.create(
            sender=sender,
            recipient=recipient,
            verb=verb.name.lower(),
            actor=actor,
            action_object=action_object,
            target=target,
            explicit_link=link,
            context_data=context_data or {},
        )

        if send_via_email is None:
            notification_type = NotificationTypeEnum[verb.name.upper()]
            # if not specified, default to true
            send_via_email = not recipient.notification_settings.filter(
                notification_type_group=notification_type.value.group, email=False
            ).exists()

        if send_via_email:
            html_body_params = {
                'text': notification.email_text,
                'link': notification.link,
                'base_url': settings.BASE_URL,
                **notification.format_data(),
            }
            try:
                html_body = render_to_string(
                    f'notifications/{verb.name.lower()}.html', html_body_params,
                )
            except TemplateDoesNotExist:
                html_body = render_to_string(
                    'email_notification.html', html_body_params,
                )
            send_email.delay(
                subject=notification.email_subject,
                body=notification.email_text,
                html_body=html_body,
                reply_to=[reply_to],
                to=[recipient.email],
                attachments=email_attachments,
            )

        return notification


class Feedback(models.Model):
    """Feedback item leaved by an user"""

    text = models.TextField()
    page_url = models.CharField(max_length=255, null=True, default=None)
    page_html = models.TextField(null=True)
    redux_state = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, related_name='feedbacks', on_delete=models.CASCADE,
    )


class ReasonOptionManager(models.Manager):
    def get_queryset(self):
        """`Other` option always last no matter what"""
        other_last = Case(When(text='Other', then=1), default=0)
        return super().get_queryset().order_by(other_last, 'text')


class ReasonDeclineCandidateOption(models.Model):
    """Option variant for reason to decline candidate"""

    text = models.CharField(max_length=255)
    has_description = models.BooleanField(default=False)

    objects = ReasonOptionManager()

    def __str__(self):
        return self.text


class ReasonNotInterestedCandidateOption(models.Model):
    """Option variant for reason why candidate is not interested"""

    text = models.CharField(max_length=255)
    has_description = models.BooleanField(default=False)

    objects = ReasonOptionManager()

    def __str__(self):
        return self.text


class InterviewType(StatusEnum):
    ASSIGNMENT = _('Assignment')
    TECHNICAL_FIT = _('Technical Fit')
    CULTURAL_FIT = _('Cultural Fit')
    GENERAL = _('General')
    CROSS_TEAM = _('Cross-team')


class InterviewTemplate(models.Model):
    interview_type = models.CharField(
        max_length=15,
        choices=InterviewType.get_choices(),
        default=InterviewType.GENERAL.key,
    )
    default = models.BooleanField(default=False)
    default_order = models.PositiveIntegerField(null=True, blank=True)


class JobInterviewTemplate(models.Model):
    job = models.ForeignKey(
        'Job', related_name='interview_templates', on_delete=models.CASCADE
    )
    interview_type = models.CharField(
        max_length=15,
        choices=InterviewType.get_choices(),
        default=InterviewType.GENERAL.key,
    )
    default = models.BooleanField(default=False)
    order = models.PositiveIntegerField()
    description = models.TextField(max_length=1024, blank=True)
    interviewer = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name='interview_templates',
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ['order', 'pk']


class ProposalInterviewSchedule(models.Model):
    class Status(models.TextChoices):
        TO_BE_SCHEDULED = 'to_be_scheduled', _('To Be Scheduled')
        PENDING_CONFIRMATION = 'pending', _('Pending Candidate Confirmation')
        SCHEDULED = 'scheduled', _('Scheduled')
        REJECTED = 'rejected', _('Rejected')
        CANCELED = 'canceled', _('Canceled')
        SKIPPED = 'skipped', _('Skipped')

    class SchedulingType(models.TextChoices):
        INTERVIEW_PROPOSAL = (
            'interview_proposal',
            _('Interview Proposal (Send interview time slots to Candidate)'),
        )
        SIMPLE_SCHEDULING = (
            'simple_scheduling',
            _('Simple Scheduling (Candidate has been invited outside ZooKeep)'),
        )
        PAST_SCHEDULING = (
            'past_scheduling',
            _('Past Scheduling (Record an interview that already took place)'),
        )

    scheduling_type = models.CharField(
        max_length=20, choices=SchedulingType.choices, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    interview = models.ForeignKey(
        'ProposalInterview', on_delete=models.CASCADE, related_name='schedules'
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.TO_BE_SCHEDULED
    )
    pre_schedule_msg = models.TextField(max_length=1024, blank=True)
    notes = models.TextField(max_length=1024, blank=True)
    creator_timezone = models.TextField(
        blank=True, choices=((tz_name, tz_name) for tz_name in pytz.all_timezones)
    )
    scheduled_timeslot = models.ForeignKey(
        'ProposalInterviewScheduleTimeSlot',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )

    def __str__(self):
        return f"Schedule {self.status} - {self.scheduled_timeslot}"


class ProposalInterview(OrderedModel):

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    public_uuid = models.UUIDField(unique=True, default=uuid4)
    proposal = models.ForeignKey(
        Proposal, related_name='interviews', on_delete=models.CASCADE,
    )
    interviewer = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name='proposal_interviews',
        on_delete=models.CASCADE,
    )
    current_schedule = models.ForeignKey(
        ProposalInterviewSchedule,
        on_delete=models.RESTRICT,
        null=True,
        related_name='default_for_interviews',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    interview_type = models.CharField(
        max_length=15,
        choices=InterviewType.get_choices(),
        default=InterviewType.GENERAL.key,
    )
    order_with_respect_to = 'proposal'

    @property
    def candidate(self):
        return self.proposal.candidate

    @property
    def job(self):
        return self.proposal.job

    @property
    def organization(self):
        return self.proposal.job.organization

    @property
    def is_current_interview(self):
        return self.proposal.current_interview.id == self.id

    @property
    def creator_timezone(self):
        try:
            return self.current_schedule.creator_timezone
        except AttributeError:
            return ''

    @property
    def start_at(self):
        try:
            return self.current_schedule.scheduled_timeslot.start_at
        except AttributeError:
            return None

    @property
    def end_at(self):
        try:
            return self.current_schedule.scheduled_timeslot.end_at
        except AttributeError:
            return None

    @property
    def notes(self):
        return self.current_schedule.notes

    @property
    def scheduling_type(self):
        if self.current_schedule:
            return self.current_schedule.scheduling_type
        return None

    def get_status(self):
        if self.current_schedule:
            return self.current_schedule.status
        return None

    @property
    def ics_uid(self):
        return f'{self.public_uuid}@zookeep.com'

    def _ics_event(self, status=None):
        event = ics.Event(
            uid=self.ics_uid,
            name=_(
                'Interview between {interview.organization.name}'
                ' and {interview.candidate.name} for {interview.job.title} position'
            ).format(interview=self),
            begin=self.start_at,
            end=self.end_at,
            description=self.notes,
            status=status,
        )
        event.organizer = ics.Organizer(
            common_name=self.created_by.full_name, email=self.created_by.email,
        )
        event.add_attendee(
            ics.Attendee(common_name=self.candidate.name, email=self.candidate.email,)
        )
        if self.created_by != self.proposal.created_by:
            event.add_attendee(
                ics.Attendee(
                    common_name=self.proposal.created_by.full_name,
                    email=self.proposal.created_by.email,
                )
            )
        return event

    @property
    def ics_attachment(self):
        event = self._ics_event()
        data = str(ics.Calendar(events={event}))
        filename = self.format('Interview_%Y-%m-%d_{start_at}~{end_at}.ics', '%H-%M')
        return filename, data, 'text/plain'

    @property
    def ics_canceled_attachment(self):
        event = self._ics_event(status='CANCELLED')
        calendar = ics.Calendar(events={event})
        calendar.extra.append(ContentLine(name='METHOD', value='REQUEST'))
        data = str(calendar)
        filename = self.format('Interview_%Y-%m-%d_{start_at}~{end_at}.ics', '%H-%M')
        return filename, data, 'text/plain'

    def format(self, format, time_format, tz_name=None):
        start_at = self.start_at
        end_at = self.end_at

        if not (start_at and end_at):
            return ''

        tz_name = tz_name or 'Asia/Tokyo'
        if tz_name:
            timezone = pytz.timezone(tz_name)
            start_at = timezone.normalize(start_at)
            end_at = timezone.normalize(end_at)

        return start_at.strftime(format).format(
            start_at=start_at.strftime(time_format), end_at=end_at.strftime(time_format)
        )

    def __str__(self):
        return f'Interview for {self.proposal} {self.created_at}'

    def save(self, *args, **kwargs):
        is_created = not self.id

        super().save(*args, **kwargs)

        if is_created and self.current_schedule is None:
            self.current_schedule = ProposalInterviewSchedule.objects.create(
                interview_id=self.id,
                status=ProposalInterviewSchedule.Status.TO_BE_SCHEDULED,
            )
            self.save()


class ProposalInterviewInvite(models.Model):
    interview = models.ForeignKey(
        ProposalInterview, on_delete=models.CASCADE, related_name='invited'
    )
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    email = models.EmailField(null=True, blank=True)

    @property
    def name(self):
        return self.user.full_name if self.user else None


class ProposalInterviewScheduleTimeSlot(models.Model):
    schedule = models.ForeignKey(
        ProposalInterviewSchedule, on_delete=models.CASCADE, related_name='timeslots',
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    def __str__(self):
        return f"Interview Time Slot {self.start_at} to {self.end_at}"


class HiringCriterionAssessment(models.Model):
    MIN_RATING = 1
    MAX_RATING = 5
    assessment = models.ForeignKey(
        'ProposalInterviewAssessment', on_delete=models.CASCADE
    )
    hiring_criterion = models.ForeignKey('HiringCriterion', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_RATING), MaxValueValidator(MAX_RATING),],
        null=True,
    )


class ProposalInterviewAssessment(models.Model):
    DECISION_CHOICES = (
        ('proceed', _('Proceed')),
        ('keep', _('Keep')),
        ('reject', _('Reject')),
    )
    interview = models.OneToOneField(
        ProposalInterview, on_delete=models.CASCADE, related_name='assessment',
    )
    hiring_criteria = models.ManyToManyField(
        HiringCriterion, through=HiringCriterionAssessment, related_name='+'
    )
    decision = models.CharField(max_length=7, choices=DECISION_CHOICES)
    notes = models.TextField(blank=True)


def get_new_file_path(relation_field, path_template, instance, filename):
    relation = getattr(instance, relation_field, None)

    if relation is None:
        raise IntegrityError

    return path_template.format(filename=filename, random=uuid4(), id=relation.id)


def get_candidate_file_path(instance, filename):
    return get_new_file_path(
        'candidate', 'candidate/{id}/{random}/{filename}', instance, filename,
    )


def get_candidate_file_preview_path(instance, filename):
    return get_new_file_path(
        'candidate', 'candidate/{id}/{random}/preview-{filename}', instance, filename,
    )


def get_candidate_file_thumbnail_path(instance, filename):
    return get_new_file_path(
        'candidate', 'candidate/{id}/{random}/thumbnail-{filename}', instance, filename,
    )


@reversion.register()
class CandidateFile(models.Model):
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name='files',
    )
    title = models.CharField(max_length=64, blank=True)
    file = models.FileField(upload_to=get_candidate_file_path)
    preview = models.FileField(upload_to=get_candidate_file_preview_path)
    thumbnail = models.FileField(upload_to=get_candidate_file_thumbnail_path)
    is_shared = models.BooleanField(default=False)

    org_content_type = models.ForeignKey(
        ContentType,
        limit_choices_to=(
            Q(app_label='core', model='agency') | Q(app_label='core', model='client')
        ),
        null=True,
        on_delete=models.CASCADE,
    )
    org_id = GfkLookupField('org_content_type')
    organization = GenericForeignKey('org_content_type', 'org_id')

    @property
    def file_name(self):
        return os.path.basename(self.file.name)


TAG_TYPE_CHOICES = [
    ('candidate', 'Candidate'),
    ('skill', 'Skill'),
]


class Tag(models.Model):
    name = models.CharField(max_length=64)
    type = models.CharField(
        choices=TAG_TYPE_CHOICES, default='candidate', max_length=16,
    )

    created_by = models.ForeignKey(
        'User', on_delete=models.SET_NULL, related_name='created_tags', null=True
    )

    org_content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        limit_choices_to=(
            Q(app_label='core', model='agency') | Q(app_label='core', model='client')
        ),
    )
    org_id = GfkLookupField('org_content_type', null=True, blank=True)
    organization = GenericForeignKey('org_content_type', 'org_id')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'type', 'org_content_type', 'org_id'],
                name='unique tag by name type org',
            )
        ]

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CandidateTag(models.Model):
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, related_name='candidate_tags'
    )
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    attached_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attached_candidates_tags',
    )

    def __str__(self):
        return f'{self.tag.name} - {self.candidate.name}'

    class Meta:
        unique_together = ('tag', 'candidate')


class FeeStatus(StatusEnum):
    DRAFT = _('Draft')
    PENDING = _('Pending')
    APPROVED = _('Approved')
    NEEDS_REVISION = _('Needs revision')


LOCKED_PLACEMENT_STATUSES = (
    FeeStatus.PENDING.key,
    FeeStatus.APPROVED.key,
)


class ConsultingFeeType(StatusEnum):
    FIXED = _('Fixed')
    PERCENTILE = _('Percentile')


class InvoiceStatus(StatusEnum):
    PAID = _('Paid')
    OVERDUE = _('Overdue')
    SENT = _('Sent')
    NOT_SENT = _('Not Sent')


class Placement(models.Model):
    proposal = models.OneToOneField(
        'core.Proposal', models.CASCADE, related_name='placement',
    )

    # Placement section
    current_salary = MoneyField()

    offered_salary = MoneyField()

    signed_at = models.DateField(auto_created=True)

    starts_work_at = models.DateField()

    candidate_source = models.CharField(max_length=128, blank=True,)

    candidate_source_details = models.CharField(max_length=100, blank=True)


class Fee(models.Model):
    created_by = models.ForeignKey(
        'core.User', models.CASCADE, related_name='created_fees',
    )

    proposal = models.ForeignKey(
        'core.Proposal', models.CASCADE, related_name='fee', null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    agency = models.ForeignKey('core.Agency', models.CASCADE, related_name='fees',)

    job_contract = models.ForeignKey(
        'core.JobAgencyContract', models.CASCADE, related_name='fees'
    )

    submitted_by = models.ForeignKey(
        'core.User',
        models.CASCADE,
        related_name='submitted_candidate_placements',
        null=True,
    )

    submitted_at = models.DateTimeField(null=True, blank=True)

    approved_at = models.DateField(null=True)

    placement = models.OneToOneField(
        'core.Placement', models.CASCADE, related_name='fee', null=True, blank=True
    )
    status = models.CharField(
        max_length=FeeStatus.get_db_field_length(),
        choices=FeeStatus.get_choices(),
        default=FeeStatus.PENDING.key,
    )

    # Usually copy of placement sign date or contract sign date
    nbv_date = models.DateField()

    # Usually copy of placement start work date or defined explicityl as Retainer Fee Date
    nfi_date = models.DateField()

    # Client Section
    billing_address = models.CharField(max_length=384)

    should_send_invoice_email = models.BooleanField(default=False)
    invoice_email = models.EmailField(blank=True)

    # Contract Section
    consulting_fee_type = models.CharField(
        max_length=10, choices=ConsultingFeeType.get_choices(),
    )
    # Used only if consulting fee type is set as "fixed"
    consulting_fee = MoneyField(null=True)
    # salary percentage as consulting fee
    # Used only if consulting fee type is set as "percentile"
    # consulting_fee_percentile = 1 means 100%
    consulting_fee_percentile = models.DecimalField(
        decimal_places=4, max_digits=5, null=True
    )

    @property
    def contract_type(self):
        return self.job_contract.contract_type

    @property
    def contract_type_title(self):
        key = self.contract_type
        if key:
            return ContractType[key.upper()].value
        return ''

    bill_description = models.CharField(max_length=200)

    @property
    def bill_description_title(self):
        key = self.bill_description
        if key:
            try:
                return BillDescription[key.upper()].value
            except KeyError:
                return key
        return ''

    # Invoice section
    invoice_value = MoneyField()
    consumption_tax = MoneyField()

    invoice_issuance_date = models.DateField()

    invoice_number = models.CharField(max_length=15, null=True)
    invoice_due_date = models.DateField(null=True)
    invoice_status = models.CharField(
        default=InvoiceStatus.NOT_SENT.key,
        choices=InvoiceStatus.get_choices(),
        max_length=InvoiceStatus.get_db_field_length(),
    )
    invoice_paid_at = models.DateField(null=True)

    # Additional info section
    notes_to_approver = models.TextField(blank=True)

    @property
    def client(self):
        return self.job_contract.job.client

    @property
    def candidate(self):
        return self.placement.proposal.candidate


def get_split_allocation_file_path(instance, filename):
    return f'split_allocation/{instance.id}/{uuid4()}/{filename}'


class FeeSplitAllocation(models.Model):
    fee = models.OneToOneField(
        to='core.Fee', on_delete=models.CASCADE, related_name='split_allocation',
    )

    # Split allocations

    candidate_owner = models.ForeignKey(
        to='core.User',
        on_delete=models.SET_NULL,
        related_name='owner_split_allocations',
        null=True,
    )

    candidate_owner_split = models.DecimalField(decimal_places=4, max_digits=5,)

    lead_candidate_consultant = models.ForeignKey(
        to='core.User',
        on_delete=models.SET_NULL,
        related_name='lead_candidate_consultant_split_allocations',
        null=True,
    )

    lead_candidate_consultant_split = models.DecimalField(
        decimal_places=4, max_digits=5,
    )

    support_consultant = models.ForeignKey(
        to='core.User',
        on_delete=models.SET_NULL,
        related_name='support_consultant_split_allocations',
        null=True,
    )

    support_consultant_split = models.DecimalField(decimal_places=4, max_digits=5,)

    client_originator = models.ForeignKey(
        to='core.User',
        on_delete=models.SET_NULL,
        related_name='client_originator_split_allocations',
        null=True,
    )

    client_originator_split = models.DecimalField(decimal_places=4, max_digits=5,)

    lead_bd_consultant = models.ForeignKey(
        to='core.User',
        on_delete=models.SET_NULL,
        related_name='lead_bd_consultant_split_allocations',
        null=True,
    )

    lead_bd_consultant_split = models.DecimalField(decimal_places=4, max_digits=5,)

    activator = models.ForeignKey(
        to='core.User',
        on_delete=models.SET_NULL,
        related_name='activator_split_allocations',
        null=True,
    )

    activator_split = models.DecimalField(decimal_places=4, max_digits=5,)

    file = models.FileField(null=True, upload_to=get_split_allocation_file_path)


class FeeApprovalType(StatusEnum):
    FEE = _('Fee')
    PLACEMENT = _('Placement')
    PROPOSAL = _('Proposal')


class LogEntry(AdminLogEntry):
    class ActionFlag(models.IntegerChoices):
        ADDITION = 1
        CHANGE = 2
        DELETION = 3
        VIEW = 4

    class Meta:
        verbose_name = _('log entry')
        verbose_name_plural = _('log entries')
        proxy = True

    def get_action_flag_display(self):
        return self.ActionFlag(self.action_flag).label


class NoteActivity(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    content = models.TextField(blank=True)
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='note_activities',
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='note_activities',
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='note_activities',
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='authored_note_activities'
    )

    class Meta:
        ordering = ('-created_at',)
        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_enforce_relations',
                check=(
                    Q(
                        proposal__isnull=False,
                        candidate__isnull=False,
                        job__isnull=False,
                    )
                    | (
                        Q(proposal__isnull=True)
                        & (
                            Q(candidate__isnull=True, job__isnull=False)
                            | Q(candidate__isnull=False, job__isnull=True)
                        )
                    )
                ),
            )
        ]

    def save(self, *args, **kwargs):
        if self.proposal:
            self.candidate = self.proposal.candidate
            self.job = self.proposal.job
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        if self.proposal:
            return reverse(
                'proposal_activity',
                kwargs={'job_id': self.job_id, 'proposal_id': self.proposal_id},
            )
        if self.job:
            return reverse('job_activity', kwargs={'job_id': self.job_id})
        if self.candidate:
            return reverse(
                'candidate_activity', kwargs={'candidate_id': self.candidate_id}
            )

    def send_notifications(self):
        if self.proposal:
            recipients = self.job.recruiters.exclude(id=self.author_id)
            for recipient in recipients:
                Notification.send(
                    recipient,
                    NotificationTypeEnum.NOTE_ACTIVITY_ADDED_TO_PROPOSAL,
                    sender=self.author,
                    actor=self.author,
                    action_object=self.proposal,
                    target=self,
                    send_via_email=True,
                    context_data={
                        'link_text': NotificationLinkText.ACTIVITY_DETAIL.name
                    },
                )
