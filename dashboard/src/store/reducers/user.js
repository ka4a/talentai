import {
  LOGIN_USER_SUCCESS,
  LOGOUT_USER_SUCCESS,
  READ_USER_FAIL,
  READ_USER_SUCCESS,
  UPDATE_USER_SUCCESS,
  SET_USER,
  DEAUTHENTICATE_USER,
  UPDATE_USER_TABLE_PAGE_SIZE,
  UPDATE_USER_TABLE_PAGE_SIZE_SUCCESS,
} from '@actions';

import createReducer from '../createReducer';

const initialState = {
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
      isCareerSiteEnabled: false,
      careerSiteUrl: '',
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
};

const handleLoginUser = (state, payload) => ({
  ...payload,
  isAuthenticated: true,
  isLoaded: true,
});

const handleLogoutUser = () => ({
  isAuthenticated: false,
  isLoaded: true,
});

const handleUserUpdate = (state, payload) => ({ ...state, ...payload });

const actionHandlers = {
  [SET_USER]: (state, payload) => ({ ...state, ...payload.user }),
  // we update page size naively to increase responsiveness
  // it will be confirmed with actual value
  [UPDATE_USER_TABLE_PAGE_SIZE]: (state, { paginationKey, size }) => ({
    ...state,
    frontendSettings: {
      ...state.frontendSettings,
      [paginationKey]: size,
    },
  }),
  [UPDATE_USER_TABLE_PAGE_SIZE_SUCCESS]: handleUserUpdate,
  [READ_USER_SUCCESS]: handleLoginUser,
  [LOGIN_USER_SUCCESS]: handleLoginUser,
  [READ_USER_FAIL]: (state, payload) =>
    payload.error?.response?.status === 403 ? handleLogoutUser(state, payload) : state,
  [UPDATE_USER_SUCCESS]: handleUserUpdate,
  [LOGOUT_USER_SUCCESS]: handleLogoutUser,
  [DEAUTHENTICATE_USER]: handleLogoutUser,
};

export default createReducer(initialState, actionHandlers);
