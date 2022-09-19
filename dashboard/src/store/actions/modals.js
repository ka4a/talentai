import { uniqueId } from 'lodash';

export const SET_IS_SCROLL_START = 'SET_IS_SCROLL_START';

export const OPEN_INTERVIEW_EDIT = 'OPEN_INTERVIEW_EDIT';
export const CLOSE_INTERVIEW_EDIT = 'CLOSE_INTERVIEW_EDIT';

export const OPEN_INTERVIEW_SCHEDULING = 'OPEN_INTERVIEW_SCHEDULING';
export const CLOSE_INTERVIEW_SCHEDULING = 'CLOSE_INTERVIEW_SCHEDULING';

export const OPEN_INTERVIEW_ASSESSMENT = 'OPEN_INTERVIEW_ASSESSMENT';
export const CLOSE_INTERVIEW_ASSESSMENT = 'CLOSE_INTERVIEW_ASSESSMENT';

export const OPEN_REJECTION = 'OPEN_REJECTION';
export const CLOSE_REJECTION = 'CLOSE_REJECTION';

export const OPEN_ADD_CANDIDATE_TO_JOB = 'OPEN_ADD_CANDIDATE_TO_JOB';
export const CLOSE_ADD_CANDIDATE_TO_JOB = 'CLOSE_ADD_CANDIDATE_TO_JOB';

export const OPEN_ALERT = 'OPEN_ALERT';
export const CLOSE_ALERT = 'CLOSE_ALERT';

export const setIsScrollStart = (isStart) => ({
  type: SET_IS_SCROLL_START,
  payload: { isStart },
});

export const openInterviewEdit = (interviewId) => ({
  type: OPEN_INTERVIEW_EDIT,
  payload: { interviewId },
});
export const closeInterviewEdit = () => ({ type: CLOSE_INTERVIEW_EDIT });

export const openInterviewScheduling = (interviewId) => ({
  type: OPEN_INTERVIEW_SCHEDULING,
  payload: { interviewId },
});
export const closeInterviewScheduling = () => ({ type: CLOSE_INTERVIEW_SCHEDULING });

export const openAddCandidateToJob = () => ({ type: OPEN_ADD_CANDIDATE_TO_JOB });
export const closeAddCandidateToJob = () => ({ type: CLOSE_ADD_CANDIDATE_TO_JOB });

/**
 * @param interviewId
 * @param type is for defining add/edit modal. Accepts 'add' or 'edit' values
 */
export const openInterviewAssessment = (interviewId, type = 'add') => ({
  type: OPEN_INTERVIEW_ASSESSMENT,
  payload: { interviewId, type },
});
export const closeInterviewAssessment = () => ({ type: CLOSE_INTERVIEW_ASSESSMENT });

export const openAlert = (title, description, content, getButtons) => ({
  type: OPEN_ALERT,
  payload: {
    id: uniqueId('AlertWindow'),
    title,
    description,
    content,
    getButtons,
  },
});
export const closeAlert = (id) => ({
  type: CLOSE_ALERT,
  payload: { id },
});

export const openRejection = (proposalId) => ({
  type: OPEN_REJECTION,
  payload: { proposalId },
});
export const closeRejection = () => ({ type: CLOSE_REJECTION });

export const OPEN_CANCEL_INTERVIEW_PROPOSAL = 'OPEN_CANCEL_INTERVIEW_PROPOSAL';

export const openCancelInterviewProposal = (interviewId) => ({
  type: OPEN_CANCEL_INTERVIEW_PROPOSAL,
  payload: { interviewId },
});

export const CLOSE_CANCEL_INTERVIEW_PROPOSAL = 'CLOSE_CANCEL_INTERVIEW_PROPOSAL';

export const closeCancelInterviewProposal = () => ({
  type: CLOSE_CANCEL_INTERVIEW_PROPOSAL,
});
