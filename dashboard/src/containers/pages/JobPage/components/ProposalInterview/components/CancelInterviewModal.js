import React, { memo } from 'react';

import { Trans, t } from '@lingui/macro';
import PropTypes from 'prop-types';

import { Typography, InterviewNotificationRecipients } from '@components';
import { formatSchedule } from '@utils';
import { INTERVIEW_SCHEDULING_TYPES } from '@constants';
import { ReactComponent as Clock } from '@images/icons/clockOutlined.svg';

import styles from '../ProposalInterview.module.scss';

const CancelInterviewModal = ({ proposal }) => {
  const { startAt, endAt, schedulingType } = proposal.currentInterview || {};

  return (
    <>
      <Typography>
        <Trans>Are you sure you want to cancel this Interview?</Trans>
      </Typography>

      <Typography className={styles.confirmedTime}>
        <Clock className={styles.clock} />
        {formatSchedule(startAt, endAt)}
      </Typography>

      <InterviewNotificationRecipients
        title={t`Once you cancel, an interview cancellation will be sent to:`}
        className={styles.recipients}
        schedulingType={schedulingType}
      />
    </>
  );
};

CancelInterviewModal.propTypes = {
  proposal: PropTypes.shape({
    candidate: PropTypes.object,
    currentInterview: PropTypes.shape({
      startAt: PropTypes.instanceOf(Date),
      endAt: PropTypes.instanceOf(Date),
      schedulingType: PropTypes.oneOf(Object.keys(INTERVIEW_SCHEDULING_TYPES)),
    }),
  }).isRequired,
};

export default memo(CancelInterviewModal);
