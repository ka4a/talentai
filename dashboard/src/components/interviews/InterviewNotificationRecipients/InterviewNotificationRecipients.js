import React, { memo } from 'react';

import { t } from '@lingui/macro';
import classNames from 'classnames';
import PropTypes from 'prop-types';

import { Typography } from '@components';
import { INTERVIEW_SCHEDULING_TYPES } from '@constants';

import styles from './InterviewNotificationRecipients.module.scss';

const InterviewNotificationRecipients = ({ schedulingType, title, className }) => {
  const recipients = getRecipients(schedulingType);
  return (
    <Typography variant='caption' className={classNames(styles.root, className)}>
      {recipients.length > 0 ? (
        <>
          {title}
          <ul>
            {recipients.map((recipient) => (
              <li key={recipient}> - {recipient}</li>
            ))}
          </ul>
        </>
      ) : (
        t`No invitation will be sent`
      )}
    </Typography>
  );
};

InterviewNotificationRecipients.propTypes = {
  title: PropTypes.string.isRequired,
  scheduleType: PropTypes.oneOf(Object.keys(INTERVIEW_SCHEDULING_TYPES)).isRequired,
  className: PropTypes.string,
};

InterviewNotificationRecipients.defaultProps = {
  className: '',
};

function getRecipients(schedulingType) {
  if (schedulingType === INTERVIEW_SCHEDULING_TYPES.pastScheduling) return [];

  const interviewers = t`interviewer(s)`;
  const recruiters = t`assigned recruiter(s)`;

  if (schedulingType === INTERVIEW_SCHEDULING_TYPES.interviewProposal) {
    return [t`candidate`, interviewers, recruiters];
  }

  return [interviewers, recruiters];
}

export default memo(InterviewNotificationRecipients);
