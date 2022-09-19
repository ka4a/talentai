import { t } from '@lingui/macro';
import moment from 'moment';

import { INTERVIEW_STATUSES } from '@constants';

export function getStatusText(interview, isExtended = false) {
  const { schedules, assessment, endAt, status, statusDisplay } = interview;

  switch (status) {
    case INTERVIEW_STATUSES.canceled:
    case INTERVIEW_STATUSES.rejected:
      return t`To Be Rescheduled`;

    case INTERVIEW_STATUSES.toBeScheduled:
      if (schedules.length > 1) return t`To Be Rescheduled`;
      break;

    case INTERVIEW_STATUSES.scheduled:
      if (assessment)
        return isExtended ? t`Completed (Pending Decision)` : t`Completed`;

      if (checkIfPastInterviewTime(endAt))
        return isExtended ? t`Completed (Pending Assessment)` : t`Completed`;

      break;

    default:
      break;
  }

  return statusDisplay;
}

export const getLongInterviewName = (interview) => {
  return t`Interview ${interview.order} - ${getStatusText(interview, true)}`;
};

export const checkIfPastInterviewTime = (endAt) => {
  return moment().diff(endAt, 'minute') >= 0;
};
