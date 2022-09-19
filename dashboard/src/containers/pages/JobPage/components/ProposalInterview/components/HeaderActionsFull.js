import React, { memo } from 'react';

import PropTypes from 'prop-types';

import { Typography } from '@components';
import { INTERVIEW_STATUSES } from '@constants';
import { checkIfPastInterviewTime, formatTimeslot } from '@utils';
import { ReactComponent as Clock } from '@images/icons/clockOutlined.svg';

import InterviewButtons from './InterviewButtons';

import styles from '../ProposalInterview.module.scss';

const HeaderActionsFull = ({ interview, isOpen, isDisabled }) => {
  const { startAt, status, endAt } = interview;

  const shouldShowInterviewTime =
    !isOpen &&
    status === INTERVIEW_STATUSES.scheduled &&
    !checkIfPastInterviewTime(interview.endAt) &&
    !interview.assessment;

  return (
    <>
      {shouldShowInterviewTime && (
        <div className={styles.headerScheduledDate}>
          <Clock />
          <Typography>{formatTimeslot(startAt, endAt)}</Typography>
        </div>
      )}

      <InterviewButtons
        interview={interview}
        isCollapseOpen={isOpen}
        isCollapseDisabled={isDisabled}
      />
    </>
  );
};

HeaderActionsFull.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  isDisabled: PropTypes.bool.isRequired,
  interview: PropTypes.shape({}).isRequired,
};

export default memo(HeaderActionsFull);
