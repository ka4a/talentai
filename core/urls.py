from django.urls import include, path, re_path
from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register(r'locale', views.LocaleViewSet, 'locale')
router.register(r'data', views.DataViewSet, 'data')
router.register(r'clients', views.ClientViewSet)
router.register(r'legal_agreements', views.LegalAgreementViewSet)
router.register(r'jobs', views.JobViewSet, 'job')
router.register(
    r'job_agency_contracts', views.JobAgencyContractViewSet, 'job-agency-contract'
)
router.register(r'job_files', views.JobFileViewSet, 'job-file')
router.register(r'jobs_validation', views.JobValidateViewSet)

router.register(
    r'job_postings/private_public',
    views.PrivateJobPostingPublicViewSet,
    'private-job-posting-public',
)
router.register(
    r'job_postings/private', views.PrivateJobPostingViewSet, 'private-job-posting'
)
router.register(
    r'job_postings/private_validation', views.PrivateJobPostingValidateViewSet
)

router.register(
    r'public/career_site/organization',
    views.PublicCareerSiteOrganizationViewSet,
    'public-career-site-organization',
)

router.register(
    r'public/career_site/(?P<slug>[-a-zA-Z0-9_]+)/job_postings',
    views.PublicCareerSiteJobPostingsViewSet,
)

router.register(
    r'job_postings/career', views.CareerSiteJobPostingViewSet, 'career-site-job-posting'
)
router.register(
    r'job_postings/career_validation', views.CareerSiteJobPostingValidateViewSet
)

router.register(r'interview_templates', views.InterviewTemplateViewSet)
router.register(r'candidates', views.CandidateValidateViewSet)
router.register(r'agencies', views.AgencyViewSet)
router.register(r'contracts', views.ContractViewSet)
router.register(r'candidates', views.CandidateViewSet)
router.register(r'candidates_linkedin_data', views.CandidateLinkedinDataViewSet)
router.register(
    r'candidate_files/(?P<ftype>[a-zA-Z_]+)',
    views.CandidateFileViewSet,
    'candidate-file',
)
router.register(
    r'candidate_misc_file', views.CandidateMiscFilesViewSet, 'candidate-misc-file'
)
router.register(r'candidate_notes', views.CandidateNoteViewSet, 'candidate-note')
router.register(
    r'candidate_client_brief',
    views.CandidateClientBriefViewSet,
    'candidate-client-brief',
)
router.register(r'candidate_logs', views.CandidateLogViewSet, 'candidate-logs')
router.register(r'proposals', views.ProposalViewSet)
router.register(r'managers', views.ManagerViewSet, 'manager')
router.register(r'proposal_comment', views.ProposalCommentViewSet)
router.register(r'proposal_question', views.ProposalQuestionViewSet)
router.register(r'candidate_comment', views.CandidateCommentViewSet)
router.register(r'staff', views.StaffViewSet, 'staff')
router.register(r'team', views.TeamViewSet)
router.register(r'agency_registration_request', views.AgencyRegistrationViewSet)
router.register(r'client_registration_request', views.ClientRegistrationViewSet)
router.register(r'notifications', views.NotificationsViewSet)
router.register(r'ext_api', views.ExtApiViewSet, 'ext-api')
router.register(r'user', views.UserViewSet, 'user')
router.register(r'dashboard', views.DashboardViewSet, 'dashboard')
router.register(r'zoho', views.ZohoViewSet, 'zoho')
router.register(r'feedback', views.FeedbackViewSet, 'feedback')
router.register(r'agency_category', views.AgencyCategoryViewSet)
router.register(r'function', views.FunctionViewSet)
router.register(r'stats', views.AnalyticsViewSet, 'stats')
router.register(r'tags', views.TagViewSet, 'tags')
router.register(r'deal_pipeline', views.DealPipelineViewSet, 'deal_pipeline')
router.register(
    r'agency_client_info', views.AgencyClientInfoViewSet, 'agency_client_info'
)
router.register(
    r'proposals_snapshot_diff',
    views.ProposalSnapshotDiffViewSet,
    'proposals_snapshot_diff',
)
router.register(
    r'proposals_snapshot_state',
    views.ProposalSnapshotStateViewSet,
    'proposals_snapshot_state',
)
router.register(
    r'proposal_interviews', views.ProposalInterviewViewSet, 'proposal_interviews'
)
router.register(
    r'proposal_interviews/public',
    views.ProposalInterviewPublicViewSet,
    'proposal_interview_public',
)

router.register(r'fee', views.FeeViewSet, 'fee')
router.register(
    r'fee_split_allocation', views.FeeSplitAllocationViewSet, 'fee_split_allocation',
)
router.register(r'approval', views.ApprovalViewSet, 'approval')
router.register(r'note_activities', views.NoteActivityViewSet, 'note_activities')

urlpatterns = [
    # Ext api routes
    re_path(
        r'^ext_api/job_search/$',
        views.ExtApiJobListViewSet.as_view({'get': 'list'}),
        name='ext-api-job-search',
    ),
    # Job routes
    path(
        r'jobs/public/<uuid:uuid>/files/<int:pk>',
        views.get_job_file_public,
        name='job-file-get-public',
    ),
    re_path(
        r'clients/settings/$',
        views.ClientSettingsViewSet.as_view(
            {'get': 'retrieve', 'patch': 'partial_update'}
        ),
        name='client-settings',
    ),
    re_path(
        r'clients/settings/logo$',
        views.ClientSettingsLogoView.as_view(),
        name='client-settings-logo',
    ),
    re_path(
        r'clients/settings/validate_partial_update/$',
        views.ClientSettingsViewSet.as_view({'post': 'validate_partial_update'}),
        name='validate-client-settings',
    ),
    re_path(r'', include(router.urls)),
    re_path(
        r'user/login/$', views.LoginView.as_view({'post': 'login'}), name='user-login'
    ),
    re_path(
        r'user/logout/$',
        views.LoginView.as_view({'post': 'logout'}),
        name='user-logout',
    ),
    # User settings
    re_path(
        r'user/change_password/$',
        views.PasswordChangeView.as_view({'post': 'change_password'}),
        name='change-password',
    ),
    # Reset password
    re_path(
        r'user/reset_password/$',
        views.PasswordResetView.as_view({'post': 'reset_password'}),
        name='reset-password',
    ),
    re_path(
        r'user/confirm_password_reset/$',
        views.PasswordResetConfirmView.as_view({'post': 'confirm_password_reset'}),
        name='confirm-password-reset',
    ),
    # Activate account
    re_path(
        r'user/activate/$',
        views.ActivateAccountView.as_view({'post': 'activate_user'}),
        name='activate-account',
    ),
    # Registration
    re_path(
        r'registration/check_email/$',
        views.RegistrationCheckEmailView.as_view({'post': 'check_email'}),
        name='registration-check-email',
    ),
    # Recruiter Registration
    re_path(
        r'recruiter_registration/register/$',
        views.RecruiterRegistrationView.as_view({'post': 'register'}),
        name='recruiter-registration-register',
    ),
    re_path(r'zendesk/sso', views.ZendeskJWTView.as_view(), name='zendesk-sso-jwt',),
]
