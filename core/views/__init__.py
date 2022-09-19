from core.views.analytics import (
    AnalyticsViewSet,
    ProposalSnapshotDiffViewSet,
    ProposalSnapshotStateViewSet,
)
from core.views.ext_api import ExtApiViewSet, ExtApiJobListViewSet
from core.views.user_activate_account import ActivateAccountView
from core.views.user_change_password import PasswordChangeView
from core.views.user_reset_password import (
    PasswordResetConfirmView,
    PasswordResetView,
)
from core.views.approvals import ApprovalViewSet

from core.views.jobs import (
    get_job_file_public,
    JobViewSet,
    JobFileViewSet,
    JobValidateViewSet,
    JobAgencyContractViewSet,
    CareerSiteJobPostingViewSet,
    CareerSiteJobPostingValidateViewSet,
    PrivateJobPostingViewSet,
    PrivateJobPostingPublicViewSet,
    PrivateJobPostingValidateViewSet,
)
from core.views.career_site import PublicCareerSiteOrganizationViewSet

from core.views.candidates import (
    CandidateLinkedinDataViewSet,
    CandidateFileViewSet,
    CandidateMiscFilesViewSet,
    CandidateNoteViewSet,
    CandidateClientBriefViewSet,
    CandidateViewSet,
    CandidateValidateViewSet,
    CandidateLogViewSet,
    CandidateCommentViewSet,
)

from core.views.proposals import (
    ProposalInterviewViewSet,
    ProposalInterviewPublicViewSet,
    ProposalCommentViewSet,
    ProposalQuestionViewSet,
    ProposalViewSet,
)
from core.views.views import (
    LocaleViewSet,
    DataViewSet,
    ClientViewSet,
    AgencyViewSet,
    ContractViewSet,
    UserViewSet,
    AgencyRegistrationViewSet,
    TeamViewSet,
    ClientRegistrationViewSet,
    DashboardViewSet,
    ManagerViewSet,
    NotificationsViewSet,
    ZohoViewSet,
    LoginView,
    RegistrationCheckEmailView,
    RecruiterRegistrationView,
    FeedbackViewSet,
    AgencyCategoryViewSet,
    FunctionViewSet,
    TagViewSet,
    FeeViewSet,
    AgencyClientInfoViewSet,
    DealPipelineViewSet,
    FeeSplitAllocationViewSet,
    InterviewTemplateViewSet,
    LegalAgreementViewSet,
    NoteActivityViewSet,
)
from core.views.staff import StaffViewSet
from core.views.client_settings import ClientSettingsViewSet, ClientSettingsLogoView
from core.views.zendesk_sso import ZendeskJWTView
from core.views.career_site import (
    PublicCareerSiteJobPostingsViewSet,
    PublicCareerSiteOrganizationViewSet,
)
