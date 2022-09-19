import React, { memo, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { Trans } from '@lingui/macro';
import PropTypes from 'prop-types';

import { openInterviewAssessment, openInterviewScheduling } from '@actions';
import { CLIENT_STANDARD_USERS, INTERVIEW_STATUSES } from '@constants';
import { Badge, Button, CollapseArrowButton } from '@components';
import { useIsAuthenticatedByRoles } from '@hooks';
import { getStatusText } from '@utils';

import InterviewDropdown from './InterviewDropdown';

import styles from '../ProposalInterview.module.scss';

const { rejected, scheduled, toBeScheduled, canceled, skipped } = INTERVIEW_STATUSES;

const ALLOWED_SCHEDULE_STATUSES = new Set([toBeScheduled, rejected, canceled]);

const InterviewButtons = ({ interview, isCollapseOpen, isCollapseDisabled }) => {
  const { id, isCurrentInterview, status, interviewer } = interview;

  const userId = useSelector((state) => state.user.id);

  const dispatch = useDispatch();

  const openSchedulingModal = useCallback(
    (event) => {
      event.stopPropagation();
      dispatch(openInterviewScheduling(id));
    },
    [dispatch, id]
  );

  const openAssessmentModal = useCallback(
    (event) => {
      event.stopPropagation();
      dispatch(openInterviewAssessment(id, 'add'));
    },
    [dispatch, id]
  );

  // Interviewer can only add assessments
  const isInterviewer = userId === interviewer?.id;
  const isStandardUser = useIsAuthenticatedByRoles([CLIENT_STANDARD_USERS]);
  const canUserEdit = !isStandardUser;
  const canUserAssess = canUserEdit || isInterviewer;

  const shouldShowAssessmentButton =
    status === scheduled && !interview.assessment && canUserAssess;

  const isToBeScheduled = ALLOWED_SCHEDULE_STATUSES.has(status);
  const shouldShowScheduleButton = isToBeScheduled && isCurrentInterview;

  return (
    <div className={styles.control}>
      {shouldShowScheduleButton && (
        <Button variant='secondary' onClick={openSchedulingModal}>
          <Trans>Schedule Interview</Trans>
        </Button>
      )}

      {shouldShowAssessmentButton && (
        <Button variant='secondary' onClick={openAssessmentModal}>
          <Trans>Add Assessment</Trans>
        </Button>
      )}

      {(status !== toBeScheduled || isCurrentInterview) && (
        <Badge
          className={styles.headerItem}
          variant={getBadgeVariant(status)}
          text={getStatusText(interview)}
        />
      )}

      <InterviewDropdown
        interview={interview}
        canUserAssess={canUserAssess}
        canUserEdit={canUserEdit}
      />

      <CollapseArrowButton
        isOpen={isCollapseOpen}
        isDisabled={isCollapseDisabled}
        className={styles.collapseArrow}
      />
    </div>
  );
};

function getBadgeVariant(status) {
  switch (status) {
    case scheduled:
      return 'success';
    case skipped:
      return 'warning';
    default:
      return 'normal';
  }
}

InterviewButtons.propTypes = {
  interview: PropTypes.shape({
    id: PropTypes.number,
    isCurrentInterview: PropTypes.bool,
    status: PropTypes.string,
    statusDisplay: PropTypes.string,
  }).isRequired,
  isCollapseOpen: PropTypes.bool.isRequired,
  isCollapseDisabled: PropTypes.bool.isRequired,
};

export default memo(InterviewButtons);
