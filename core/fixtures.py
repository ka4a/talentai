"""Fixtures for creating different objects and other utilities."""
from core.factories import (
    ClientAdministratorFactory,
    ClientInternalRecruiterFactory,
    ClientStandardUserFactory,
    UserFactory,
)
import uuid
import random
import string
from io import BytesIO

import pytz
from PIL import Image

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.timezone import datetime, timedelta
from unittest.mock import patch

from core.models import (
    CandidateFile,
    CandidateLinkedinData,
    CandidateNote,
    CandidateInternalStatus,
    Notification,
    PrivateJobPosting,
    Team,
    Client,
    Job,
    Agency,
    Candidate,
    Proposal,
    Contract,
    ProposalStatusHistory,
    ProposalStatus,
    ProposalComment,
    User,
    ProposalInterview,
    ProposalInterviewSchedule,
    ProposalInterviewScheduleTimeSlot,
    ProposalInterviewInvite,
    PROPOSAL_STATUS_GROUP_CHOICES,
    ProposalStatusStage,
    ContractStatus,
    EducationDetail,
    ExperienceDetail,
    FeeStatus,
    Industry,
    ConsultingFeeType,
    ContractType,
    BillDescription,
    InvoiceOn,
    Fee,
    Placement,
    AgencyClientInfo,
    FeeSplitAllocation,
    JobAgencyContract,
)

ISOFORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def to_iso_datetime(date):
    return date.strftime(ISOFORMAT)


def generate_email(length=10):
    """Generates a random email for candidates, users, etc."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length)) + '@test.com'


NOT_EXISTING_PK = 123456789
NOT_AUTHENTICATED = {'detail': 'Authentication credentials were not provided.'}
NOT_FOUND = {'detail': 'Not found.'}
NO_PERMISSION = {'detail': 'You do not have permission to perform this action.'}

DEFAULT_CLIENT = {'name': 'Test Client'}

DEFAULT_JOB = {
    'title': 'Test Title',
    'work_location': 'Test Location',
    'responsibilities': 'Test Responsibilities',
    'requirements': 'Test Requirements',
    'published': True,
    'public': False,
}

DEFAULT_AGENCY = {'name': 'Test Agency', 'contact_email': 'info@test.co'}

DEFAULT_TEAM = {'name': 'Test team{}'}

DEFAULT_CANDIDATE = {
    'first_name': 'Test',
    'last_name': 'Candidate',
    'email': '',
    'summary': 'Test Summary',
    'internal_status': CandidateInternalStatus.NOT_CONTACTED.key,
    'li_data': None,
}

DEFAULT_CANDIDATE_NOTE = {'text': 'Test note'}

DEFAULT_CANDIDATE_EDUCATION = {
    "institute": "MIT",
    "department": "Informatics",
    "degree": "Bachelor",
    "date_start": "2019-1-1",
    "date_end": None,
    "currently_pursuing": True,
}

DEFAULT_CANDIDATE_EXPERIENCE = {
    "occupation": "Developer",
    "company": "Google",
    "summary": "Once upon a time...",
    "date_end": None,
    "date_start": "2019-1-1",
    "currently_pursuing": True,
    "location": "",
}

DEFAULT_USER = {
    'email': 'test{}@test.com',
    'password': 'password',
    'first_name': 'Name',
    'last_name': 'Family Name',
    'country': 'jp',  # required for all Agency users
}

DEFAULT_PROPOSAL_COMMENT = {'text': 'Test comment', 'public': False, 'system': False}

DEFAULT_FEEDBACK = {
    'text': 'Something went wrong',
    'page_url': '/c/dashboard',
    'page_html': '<html>404</html>',
    'redux_state': {'user': {}},
}

LINKEDIN_EXPERIENCE = [
    {
        "title": "Engeneer",
        "org": "RosPower",
        "location": "Taganrog",
        "desc": "Better",
        "date_start": "2017-05-01",
        "currently_pursuing": True,
    },
    {
        "title": "Electritian",
        "org": "Profstroydom",
        "location": "Taganrog",
        "desc": "Low pay",
        "date_start": "2015-03-01",
        "date_end": "2016-10-01",
    },
    {
        "title": "Dumbledor",
        "org": "",
        "location": "",
        "desc": "",
        "date_start": "2019-01-01",
    },
    {"title": "baloney", "date_start": "2019-01-01",},
]

LINKEDIN_EDUCATION = [
    {
        "school": "Eastern Federal University",
        "fos": "Electrical Engeneering",
        "degree": "Master",
        "desc": "blank",
        "date_start": "2018-09-01",
        "currently_pursuing": True,
    },
    {
        "school": "Eastern Federal University",
        "fos": "Electrical Engeneering",
        "degree": "Batchelor",
        "date_start": "2014-09-01",
        "date_end": "2018-01-01",
    },
    {"school": "MBOUSOSH", "date_start": "2004-09-01", "date_end": "2014-05-01"},
    {
        "school": "Blank",
        "degree": "",
        "fos": "",
        "desc": "",
        "date_start": "2019-01-01",
    },
    {"school": "baloney", "date_start": "2019-01-01",},
]

ZOHO_CANDIDATE_DATA = {
    "email": "test@localhost",
    "zoho_id": "123456789101112",
    "first_name": "Test",
    "last_name": "Candidate",
    "zoho_data": [
        {"val": "CANDIDATEID", "content": "123456789101112"},
        {"val": "Email", "content": "test@localhost"},
        {"val": "First Name", "content": "Test"},
        {"val": "Last Name", "content": "Candidate"},
    ],
}

ZOHO_TABULAR_DATA = {
    "education_details": [
        {
            "institute": "Eastern Federal University",
            "department": "Electrical Engeneering",
            "degree": "Master",
            "date_start": "09-2018",
            "currently_pursuing": True,
        },
        {
            "institute": "Eastern Federal University",
            "department": "Electrical Engeneering",
            "degree": "Batchelor",
            "date_start": "09-2014",
            "date_end": "01-2018",
            "currently_pursuing": False,
        },
    ],
    "experience_details": [
        {
            "occupation": "Engeneer",
            "company": "RosPower",
            "summary": "Better",
            "date_start": "05-2017",
            "currently_pursuing": True,
        },
        {
            "occupation": "Electritian",
            "company": "Profstroydom",
            "summary": "Low pay",
            "date_start": "03-2015",
            "date_end": "10-2016",
            "currently_pursuing": False,
        },
    ],
}

ZOHO_CANDIDATE_DATA_WITH_TABULAR = {
    **ZOHO_CANDIDATE_DATA,
    **ZOHO_TABULAR_DATA,
}

User = get_user_model()


def get_or_create_default_job_owner(org):
    email = f'{org.__class__.__name__.lower()}{org.id}.default.job.owner@dummy.net'

    default_owner = User.objects.filter(email=email).first()

    if default_owner:
        return default_owner

    user = create_user(email)

    if isinstance(org, Agency):
        org.assign_agency_manager(user)

    if isinstance(org, Client):
        org.assign_administrator(user)

    return user


def create_job(
    org,
    client=None,
    owner=None,
    title=DEFAULT_JOB['title'],
    responsibilities=DEFAULT_JOB['responsibilities'],
    requirements=DEFAULT_JOB['requirements'],
    published=DEFAULT_JOB['published'],
    public=DEFAULT_JOB['public'],
    country='jp',
    contract=None,
    **kwargs,
):
    """Create a Job, return the Job object."""
    if not client:
        if isinstance(org, Client):
            client = org
        if isinstance(org, Agency):
            client = create_client(owner_agency=org)

    if not owner:
        owner = get_or_create_default_job_owner(org)

    job = Job(
        client=client,
        owner=owner,
        title=title,
        responsibilities=responsibilities,
        requirements=requirements,
        published=published,
        country=country,
        **kwargs,
    )

    job.organization = org
    job.save()

    if isinstance(org, Agency):
        job.assign_agency(org)

    if public:
        private_job_posting = PrivateJobPosting(
            job=job,
            title=title,
            responsibilities=responsibilities,
            public_uuid=uuid.uuid4(),
        )
        private_job_posting.save()
    return job


def create_contract_job(contract, **kwargs):
    job = create_job(contract.client, client=contract.client, **kwargs)
    job.assign_agency(contract.agency)

    return job


class DEFAULT_CONTRACT(object):
    status = ContractStatus.INITIATED.key
    start_at = '2019-01-01'
    end_at = '2119-01-01'


def create_contract(
    agency,
    client,
    status=DEFAULT_CONTRACT.status,
    start_at=DEFAULT_CONTRACT.start_at,
    end_at=DEFAULT_CONTRACT.end_at,
    **kwargs,
):
    """Create a Contract between the Agency and the Client."""
    return Contract.objects.create(
        agency=agency,
        client=client,
        status=status,
        start_at=start_at,
        end_at=end_at,
        **kwargs,
    )


def get_or_create_candidate_owner(org):
    email = f'{org.__class__.__name__.lower()}{org.id}.candidate.actor@dummy.net'

    actor = User.objects.filter(email=email).first()
    if actor:
        return actor

    user = create_user(email)

    if isinstance(org, Agency):
        org.assign_agency_administrator(user)

    if isinstance(org, Client):
        org.assign_administrator(user)

    return user


def create_candidate(
    organization,
    first_name=DEFAULT_CANDIDATE['first_name'],
    last_name=DEFAULT_CANDIDATE['last_name'],
    email=DEFAULT_CANDIDATE['email'],
    summary=DEFAULT_CANDIDATE['summary'],
    li_data=DEFAULT_CANDIDATE['li_data'],
    internal_status=DEFAULT_CANDIDATE['internal_status'],
    owner=None,
    current_country='jp',
    current_salary=0,
    **kwargs,
):
    """Create a Candidate, return the Candidate object."""
    candidate = Candidate.objects.create(
        organization=organization,
        first_name=first_name,
        last_name=last_name,
        email=email if email else generate_email(),
        summary=summary,
        li_data=li_data,
        owner=owner if owner else get_or_create_candidate_owner(organization),
        current_country=current_country,
        current_salary=current_salary,
        **kwargs,
    )

    return candidate


def create_candidate_note(candidate, organization, text=DEFAULT_CANDIDATE_NOTE['text']):
    """Create a CandidateNote, return the CandidateNote object."""
    return CandidateNote.objects.create(
        candidate=candidate, organization=organization, text=text
    )


def set_if_missing(dictionary, key, value):
    if dictionary.get(key) is None:
        dictionary[key] = value


def create_proposal(job, candidate, created_by, stage='shortlist', **kwargs):
    """Create a Proposal, return the Proposal object."""
    if 'status' in kwargs:
        status = kwargs.pop('status')
    elif stage == 'longlist':
        status = ProposalStatus.objects.filter(
            stage=ProposalStatusStage.ASSOCIATED.key
        ).first()
    else:
        status = ProposalStatus.objects.filter(
            stage=ProposalStatusStage.SUBMISSIONS.key
        ).first()

    return Proposal.objects.create(
        job=job, candidate=candidate, created_by=created_by, status=status, **kwargs,
    )


def create_proposal_with_candidate(job, created_by, **kwargs):
    candidate = create_candidate(created_by.profile.org)
    return create_proposal(job, candidate, created_by, **kwargs)


def create_proposal_comment(
    author,
    proposal,
    text=DEFAULT_PROPOSAL_COMMENT['text'],
    public=DEFAULT_PROPOSAL_COMMENT['public'],
    system=DEFAULT_PROPOSAL_COMMENT['system'],
):
    """Create a Proposal comment, return the Proposal comment object."""
    return ProposalComment.objects.create(
        author=author, proposal=proposal, text=text, public=public, system=system
    )


def create_team(organization, name=DEFAULT_TEAM['name'], **kwargs):
    return Team.objects.create(
        organization=organization, name=name.format(Team.objects.count()), **kwargs,
    )


def create_django_user(
    email=None,
    password=DEFAULT_USER['password'],
    first_name=DEFAULT_USER['first_name'],
    last_name=DEFAULT_USER['last_name'],
    country=DEFAULT_USER['country'],
    superuser=False,
    **kwargs,
):
    if superuser:
        create_user_method = getattr(User.objects, 'create_superuser')
    else:
        create_user_method = getattr(User.objects, 'create_user')

    if email is None:
        email = DEFAULT_USER['email'].format(User.objects.count())
    return create_user_method(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        country=country,
        **kwargs,
    )


def create_user(*args, **kwargs):
    return create_django_user(*args, **kwargs)


def create_superuser(*args, **kwargs):
    return create_django_user(*args, **kwargs, superuser=True)


def create_agency_administrator(
    agency,
    email=DEFAULT_USER['email'],
    password=DEFAULT_USER['password'],
    user=None,
    **kwargs,
):
    """Create a User and assign them as an Agency Admin for the Agency."""

    if user is None:
        user = create_user(email.format(User.objects.count()), password, **kwargs,)
    agency.assign_agency_administrator(user)

    return user


def create_agency_manager(
    agency, email=DEFAULT_USER['email'], password=DEFAULT_USER['password']
):
    """Create a User and assign them as an Agency Manager for the Agency."""
    user = create_user(email.format(User.objects.count()), password)
    agency.assign_agency_manager(user)

    return user


def create_recruiter(
    agency, email=DEFAULT_USER['email'], password=DEFAULT_USER['password']
):
    """Create a User and assign them as a Recruiter for the Agency."""
    user = create_user(email.format(User.objects.count()), password)
    agency.assign_recruiter(user)

    return user


def create_client_administrator(
    client=None,
    email=DEFAULT_USER['email'],
    password=DEFAULT_USER['password'],
    **kwargs,
):
    client_admin_params = dict(
        user=UserFactory(
            email=email.format(User.objects.count()), password=password, **kwargs
        )
    )
    if client:
        client_admin_params['client'] = client
    return ClientAdministratorFactory(**client_admin_params).user


def create_client_internal_recruiter(
    client=None, email=DEFAULT_USER['email'], password=DEFAULT_USER['password']
):
    kwargs = dict(
        user=UserFactory(email=email.format(User.objects.count()), password=password)
    )
    if client:
        kwargs['client'] = client
    return ClientInternalRecruiterFactory(**kwargs).user


def create_client_standard_user(
    client=None, email=DEFAULT_USER['email'], password=DEFAULT_USER['password']
):
    kwargs = dict(
        user=UserFactory(email=email.format(User.objects.count()), password=password)
    )
    if client:
        kwargs['client'] = client
    return ClientStandardUserFactory(**kwargs).user


def create_hiring_manager(
    client=None, email=DEFAULT_USER['email'], password=DEFAULT_USER['password']
):
    user = create_client_standard_user(client, email, password)
    return user


def create_admin(email=DEFAULT_USER['email'], password=DEFAULT_USER['password']):
    """Create an Admin user, return the User object."""
    return create_superuser(email.format(User.objects.count()), password)


def create_organization(
    org_model, assign_admin_method_name, org_field, name, primary_contact, **kwargs
):
    """Create a Client, return the Client object."""

    should_assign_role = False

    if primary_contact is None:
        should_assign_role = True
        primary_contact = create_user()

    org = org_model.objects.create(name=name, primary_contact=primary_contact, **kwargs)

    if should_assign_role:
        getattr(org, assign_admin_method_name)(primary_contact)

    return org


def create_agency(name=DEFAULT_AGENCY['name'], primary_contact=None, **kwargs):
    """Create a Agency with AgencyAdmin as primary contact, return the Agency object"""
    return create_organization(
        Agency, 'assign_agency_administrator', 'agency', name, primary_contact, **kwargs
    )


def create_client(name=DEFAULT_CLIENT['name'], primary_contact=None, **kwargs):
    """Create a Client with ClientAdministrator as primary contact, return the Client object"""
    return create_organization(
        Client, 'assign_administrator', 'client', name, primary_contact, **kwargs,
    )


def make_create_org_with_primary_contact(create_org, create_primary_contact):
    def create_org_with_primary_contact():
        org = create_org()
        org.primary_contact = create_primary_contact(org)
        org.save()
        return org

    return create_org_with_primary_contact


def make_create_org_with_members(create_org):
    def create_org_with_members(*args):
        org = create_org()
        members = []
        for create_member in args:
            members.append(create_member(org))
        return org, members

    return create_org_with_members


create_client_with_members = make_create_org_with_members(create_org=create_client)

create_agency_with_members = make_create_org_with_members(create_org=create_agency)

DEFAULT_LINKEDIN_CANDIDATE_DATA = {
    'name': 'Some Candidate',
    'headline': 'CEO at Ninja Solutions',
    'company': 'Ninja Solutions',
    'city': 'Tokyo',
    'contact_info': {'linkedIn': 'https://www.linkedin.com/in/someslug/',},
}


def create_candidate_linkedin_data(candidate, data=None):
    """Create CandidateLinkedinData object for candidate."""
    return CandidateLinkedinData.objects.create(
        candidate=candidate,
        data=DEFAULT_LINKEDIN_CANDIDATE_DATA if data is None else data,
    )


def create_candidate_education_detail(candidate):
    return EducationDetail.objects.create(
        candidate=candidate, **DEFAULT_CANDIDATE_EDUCATION
    )


def create_candidate_experience_detail(candidate):
    return ExperienceDetail.objects.create(
        candidate=candidate, **DEFAULT_CANDIDATE_EXPERIENCE
    )


def get_user_uidb64(user):
    """Get User primary key base64 urlsafe representation."""
    return urlsafe_base64_encode(force_bytes(user.pk))


def get_user_token(user):
    """Create User token."""
    return default_token_generator.make_token(user)


def create_notification(
    recipient, verb, sender=None, actor=None, action_object=None, target=None
):

    return Notification.objects.create(
        sender=sender,
        recipient=recipient,
        verb=verb.name.lower(),
        actor=actor,
        action_object=action_object,
        target=target,
    )


def get_random_proposal_status(group):
    return ProposalStatus.objects.filter(group=group).first()


def get_status_name(group):
    for choice in PROPOSAL_STATUS_GROUP_CHOICES:
        if choice[0] == group:
            return choice[1]
    return group


def create_proposal_status(group=None):
    status = ProposalStatus(status=get_status_name(group), group=group,)
    status.save()
    return status


def get_or_create_proposal_status(group):
    status_list = list(ProposalStatus.objects.filter(group=group))
    if len(status_list) > 0:
        return status_list[0]
    else:
        return create_proposal_status(group)


def create_proposal_status_history(proposal, group, **kwargs):
    status_history = ProposalStatusHistory(
        proposal=proposal, status=get_or_create_proposal_status(group), **kwargs,
    )
    status_history.save()
    return status_history


def get_jpeg_image_content():
    f = BytesIO()
    Image.new('RGB', (1, 1)).save(f, 'JPEG')
    f.seek(0)
    return f.read()


class DEFAULT_INTERVIEW:
    invited = ()
    timeslots = ()
    start_at = datetime(2100, 1, 1, 12, 0, tzinfo=pytz.UTC)
    end_at = datetime(2100, 1, 1, 12, 30, tzinfo=pytz.UTC)
    duration = 30
    status = ProposalInterviewSchedule.Status.TO_BE_SCHEDULED


def create_proposal_interview(
    proposal,
    created_by,
    start_at=DEFAULT_INTERVIEW.start_at,
    end_at=None,
    creator_timezone='',
    invited=DEFAULT_INTERVIEW.invited,
    duration=DEFAULT_INTERVIEW.duration,
    **kwargs,
):
    if not end_at and start_at:
        end_at = start_at + timedelta(minutes=duration)
    interview = ProposalInterview.objects.create(
        proposal=proposal, created_by=created_by, **kwargs,
    )
    interview.current_schedule.creator_timezone = creator_timezone
    if start_at and end_at:
        scheduled_timeslot = interview.current_schedule.timeslots.create(
            start_at=start_at, end_at=end_at
        )
        interview.current_schedule.scheduled_timeslot = scheduled_timeslot
    interview.current_schedule.save()

    interview.invited.set(invited)
    return interview


def create_proposal_interview_with_timeslots(
    *args, timeslot_intervals=None, invited=None, **kwargs,
):
    interview = create_proposal_interview(*args, **kwargs)
    if invited:
        for invite in invited:
            user = User.objects.get(id=invite['user'])
            ProposalInterviewInvite.objects.create(
                interview=interview, user=user, email=invite.get('email', user.email),
            )
    if timeslot_intervals:
        schedule = interview.current_schedule
        if schedule is None:
            schedule = ProposalInterviewSchedule.objects.get_or_create(
                interview=interview
            )
            interview.current_schedule = schedule
            interview.save()
        for start_at, end_at in timeslot_intervals:
            ProposalInterviewScheduleTimeSlot.objects.create(
                schedule=schedule, start_at=start_at, end_at=end_at,
            )

    return interview


def get_job_assigned_to_agency_and_client(agency, client=None, job_data=None):
    _client = client or create_client()
    if not Contract.objects.filter(client=_client, agency=agency).exists():
        Contract.objects.create(
            client=_client, agency=agency, status=ContractStatus.INITIATED.key,
        )
    job = create_job(_client, **(job_data or dict()))
    job.assign_agency(agency)
    return job, _client


def get_job_assigned_to_agency(*args, **kwargs):
    job, _client = get_job_assigned_to_agency_and_client(*args, **kwargs)
    return job


@patch('core.models.uuid4')
def create_candidate_file(
    uuid4,
    candidate,
    org,
    prefix='',
    filename='file.txt',
    content=b'test',
    is_shared=False,
):
    uuid4.return_value = prefix
    result = CandidateFile(
        candidate=candidate,
        file=SimpleUploadedFile(filename, content),
        is_shared=is_shared,
    )
    result.organization = org
    result.save()
    return result


ORGANIZATION_CONSTRUCTORS = {'client': create_client, 'agency': create_agency}

USER_CONSTRUCTORS = {
    'client_administrator': create_client_administrator,
    'client_internal_recruiter': create_client_internal_recruiter,
    'client_standard_user': create_client_standard_user,
    'agency_administrator': create_agency_administrator,
    'agency_manager': create_agency_manager,
    'recruiter': create_recruiter,
}

ROLES = {
    'client': (
        'client_administrator',
        'client_internal_recruiter',
        'client_standard_user',
    ),
    'agency': ('agency_administrator', 'agency_manager', 'recruiter',),
}


def get_org_users_map(org_map):
    org = dict()
    users = dict()

    for org_name, org_type in org_map.items():
        org[org_name] = ORGANIZATION_CONSTRUCTORS[org_type]()

        users[org_name] = dict()
        for user_type in ROLES[org_type]:
            users[org_name][user_type] = USER_CONSTRUCTORS[user_type](
                org[org_name], email=f'{user_type}@{org_name}.net'
            )

    return users, org


DEFAULT_FEE = dict(
    status=FeeStatus.DRAFT.key,
    bill_description='Admin fee',
    billing_address='United States of America, Texas, Arlen, Rainy street 4',
    should_send_invoice_email=True,
    invoice_email='test@localhost',
    consulting_fee_type=ConsultingFeeType.FIXED.key,
    consulting_fee='2000',
    invoice_issuance_date='2019-03-10',
    invoice_value='2000',
    consumption_tax='200',
    notes_to_approver='Couple of notes for approver',
    nbv_date='2020-01-01',
    nfi_date='2020-01-02',
)

DEFAULT_PLACEMENT = dict(
    current_salary='2000',
    offered_salary='2000',
    signed_at='2019-03-10',
    starts_work_at='2019-03-10',
    candidate_source='Job Boards',
    candidate_source_details='LinkedIn',
)


def create_placement(proposal, **kwargs):
    for key in DEFAULT_PLACEMENT:
        if key not in kwargs:
            kwargs[key] = DEFAULT_PLACEMENT[key]

    return Placement.objects.create(proposal=proposal, **kwargs,)


def create_fee(proposal, created_by, agency=None, placement=None, job=None, **kwargs):
    for key in DEFAULT_FEE:
        if key not in kwargs:
            kwargs[key] = DEFAULT_FEE[key]

    if placement is None and proposal:
        placement = create_placement(proposal)

    if agency is None:
        agency = created_by.org

    job_contract = JobAgencyContract.objects.get(
        agency=agency, job=job or proposal.job,
    )

    return Fee.objects.create(
        placement=placement,
        proposal=proposal,
        created_by=created_by,
        agency=agency,
        job_contract=job_contract,
        **kwargs,
    )


DEFAULT_ALLOCATION_SPLIT = dict(
    client_originator_split=0.1,
    candidate_owner_split=0.2,
    activator_split=0.15,
    lead_candidate_consultant_split=0.3,
    lead_bd_consultant_split=0.15,
    support_consultant_split=0.1,
)


def create_split_allocation(
    agency, proposal, created_by, submitted_by=None, status=FeeStatus.DRAFT.key,
):
    fee = create_fee(
        proposal=proposal,
        created_by=created_by,
        submitted_by=submitted_by,
        status=status,
        agency=agency,
    )

    agency = fee.agency
    lead_bd_consultant = create_agency_manager(agency, 'lead.bd.consultant@localhost',)
    client_info = AgencyClientInfo.objects.filter(
        client=proposal.job.client, agency=agency,
    ).first()
    candidate = proposal.candidate

    return FeeSplitAllocation.objects.create(
        fee=fee,
        client_originator=client_info.originator,
        candidate_owner=candidate.owner,
        activator=candidate.activator,
        lead_candidate_consultant=candidate.lead_consultant,
        lead_bd_consultant=lead_bd_consultant,
        support_consultant=candidate.support_consultant,
        **DEFAULT_ALLOCATION_SPLIT,
    )
