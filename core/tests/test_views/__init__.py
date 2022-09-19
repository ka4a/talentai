from .views import *
from .ext_api import ExtApiViewSetTests
from .note_activities import NoteActivityTests
from .proposal import ProposalTests, ProposalFieldAccessTests
from .job import JobTests
from .job_agency_contract import JobAgencyContractTests
from .fee_split_allocation import (
    TalentAssociateRetrieveSplitAllocation,
    HiringManagerRetrieveSplitAllocation,
    AgencyAdminRetrieveSplitAllocation,
    AgencyManagerRetrieveSplitAllocation,
    RecruiterRetrieveSplitAllocation,
    TalentAssociateUpdateSplitAllocation,
    HiringManagerUpdateSplitAllocation,
    AgencyAdminUpdateSplitAllocation,
    AgencyManagerUpdateSplitAllocation,
    RecruiterUpdateSplitAllocation,
    TalentAssociateCreateSplitAllocation,
    HiringManagerCreateSplitAllocation,
    AgencyAdminCreateSplitAllocation,
    AgencyManagerCreateSplitAllocation,
    RecruiterCreateSplitAllocation,
    TalentAssociateUploadFileSplitAllocation,
    HiringManagerUploadFileSplitAllocation,
    AgencyAdminUploadFileSplitAllocation,
    AgencyManagerUploadFileSplitAllocation,
    RecruiterUploadFileSplitAllocation,
    TalentAssociateGetFileSplitAllocation,
    HiringManagerGetFileSplitAllocation,
    AgencyAdminGetFileSplitAllocation,
    AgencyManagerGetFileSplitAllocation,
    RecruiterGetFileSplitAllocation,
    TalentAssociateDeleteFileSplitAllocation,
    HiringManagerDeleteFileSplitAllocation,
    AgencyAdminDeleteFileSplitAllocation,
    AgencyManagerDeleteFileSplitAllocation,
    RecruiterDeleteFileSplitAllocation,
)
from .approvals import ApprovalGetTest
from .client_settings import ClientSettingsTest
from .zendesk_sso import ZendeskSSOTests
from .staff import StaffTests
from .candidates import CandidateTests, CandidateFieldAccessTests, ClientCandidateTests
