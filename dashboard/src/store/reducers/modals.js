import {
  OPEN_ALERT,
  CLOSE_ALERT,
  SET_IS_SCROLL_START,
  OPEN_INTERVIEW_EDIT,
  CLOSE_INTERVIEW_EDIT,
  OPEN_INTERVIEW_SCHEDULING,
  CLOSE_INTERVIEW_SCHEDULING,
  OPEN_INTERVIEW_ASSESSMENT,
  CLOSE_INTERVIEW_ASSESSMENT,
  OPEN_REJECTION,
  CLOSE_REJECTION,
  OPEN_ADD_CANDIDATE_TO_JOB,
  CLOSE_ADD_CANDIDATE_TO_JOB,
  OPEN_CANCEL_INTERVIEW_PROPOSAL,
  CLOSE_CANCEL_INTERVIEW_PROPOSAL,
} from '@actions';

import createReducer from '../createReducer';

const defaultInterviewState = {
  isOpen: false,
  interviewId: null,
};

const initialState = {
  isScrollStart: true,
  alerts: [],
  interviewEdit: defaultInterviewState,
  interviewScheduling: defaultInterviewState,
  cancelInterview: defaultInterviewState,
  interviewAssessment: {
    ...defaultInterviewState,
    type: null,
  },
  rejection: { isOpen: false },
  addCandidateToJob: { isOpen: false },
};

const toggleModalReducer = (modalKey, isOpen) => (state) => ({
  ...state,
  [modalKey]: { isOpen },
});

const resetModalReducer = (modalKey, defaultModalState) => (state) => ({
  ...state,
  [modalKey]: defaultModalState,
});

const openInterviewReducer = (modalKey) => (state, payload) => ({
  ...state,
  [modalKey]: {
    isOpen: true,
    interviewId: payload.interviewId,
  },
});

const actionHandlers = {
  [SET_IS_SCROLL_START]: (state, payload) => ({
    ...state,
    isScrollStart: payload.isStart,
  }),

  [OPEN_INTERVIEW_EDIT]: openInterviewReducer('interviewEdit'),
  [CLOSE_INTERVIEW_EDIT]: resetModalReducer(
    'interviewEdit',
    initialState.interviewEdit
  ),

  [OPEN_INTERVIEW_SCHEDULING]: openInterviewReducer('interviewScheduling'),
  [CLOSE_INTERVIEW_SCHEDULING]: resetModalReducer(
    'interviewScheduling',
    initialState.interviewScheduling
  ),

  [OPEN_CANCEL_INTERVIEW_PROPOSAL]: openInterviewReducer('cancelInterview'),
  [CLOSE_CANCEL_INTERVIEW_PROPOSAL]: resetModalReducer(
    'cancelInterview',
    initialState.cancelInterview
  ),

  [OPEN_INTERVIEW_ASSESSMENT]: (state, payload) => ({
    ...state,
    interviewAssessment: {
      isOpen: true,
      interviewId: payload.interviewId,
      type: payload.type,
    },
  }),
  [CLOSE_INTERVIEW_ASSESSMENT]: resetModalReducer(
    'interviewAssessment',
    initialState.interviewAssessment
  ),

  [OPEN_ALERT]: (state, payload) => ({
    ...state,
    alerts: [payload, ...state.alerts],
  }),
  [CLOSE_ALERT]: (state, payload) => ({
    ...state,
    alerts: state.alerts.filter((alert) => alert.id !== payload.id),
  }),

  [OPEN_REJECTION]: toggleModalReducer('rejection', true),
  [CLOSE_REJECTION]: toggleModalReducer('rejection', false),

  [OPEN_ADD_CANDIDATE_TO_JOB]: toggleModalReducer('addCandidateToJob', true),
  [CLOSE_ADD_CANDIDATE_TO_JOB]: toggleModalReducer('addCandidateToJob', false),
};

export default createReducer(initialState, actionHandlers);
