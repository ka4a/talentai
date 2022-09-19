const initialStore = {
  router: {},
  job: {
    isPrivate: null,
  },
  modals: {
    isScrollStart: true,
    alerts: [],
    interviewEdit: {
      isOpen: false,
      interviewId: null,
    },
    interviewScheduling: {
      isOpen: false,
      interviewId: null,
    },
    interviewAssessment: {
      isOpen: false,
      interviewId: null,
      type: null,
    },
    rejection: { isOpen: false },
    addCandidateToJob: { isOpen: false },
  },
  settings: {
    locale: 'en',
    localeData: {},
    cookieUsage: false,
    release: 1,
    version: null,
  },
  table: {},
  user: {
    id: null,
    email: '',
    firstName: '',
    lastName: '',
    photo: null,
    locale: 'en',
    groups: [],

    isStaff: false,
    isActive: false,
    isActivated: false,
    isLoaded: false, // is rehydrated/loaded from server

    profile: {
      org: {
        name: '',
        id: null,
        type: null,
        hasZohoIntegration: false,
      },
    },

    frontendSettings: {
      jobsShowPer: 5,
      staffShowPer: 5,
      candidatesShowPer: 5,
      clientJobsShowPer: 5,
      jobsLonglistShowPer: 5,
      notificationsShowPer: 5,
      organizationsShowPer: 5,
      dashboardJobsShowPer: 5,
      jobsShortlistShowPer: 5,
      agencyDirectoryShowPer: 5,
      agencyProposalsShowPer: 5,
      submitCandidatesShowPer: 5,
      dashboardProposalsShowPer: 5,
    },

    notificationTypes: [],
    emailNotifications: false,
    emailCandidateLonglistedForJob: false,
    emailCandidateShortlistedForJob: false,
    emailTalentAssignedManagerForJob: false,
    emailClientAssignedAgencyForJob: false,
    emailClientAssignedRecruiterForJob: false,
    emailClientUpdatedJob: false,
    emailClientCreatedContract: false,
    emailClientChangedProposalStatus: false,
    emailProposalMoved: false,
  },
};

export default initialStore;
