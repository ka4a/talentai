import React, { memo } from 'react';

import { t, Trans } from '@lingui/macro';

import { formatSchedule } from '@utils';
import { StatusBar, Typography } from '@components';
import { ReactComponent as Clock } from '@images/icons/clockOutlined.svg';

import styles from '../CandidateConfirmation.module.scss';

const CandidateConfirmed = ({ interview }) => {
  const { startAt, endAt, job } = interview;

  return (
    <>
      <StatusBar
        className={styles.statusBar}
        variant='success'
        text={t`Thank you for confirming your interview`}
      />

      <div className={styles.confirmedTimeWrapper}>
        <Typography>
          <Trans>Your meeting with {job?.clientName} has been scheduled:</Trans>
        </Typography>

        <Typography className={styles.confirmedTime}>
          <Clock className={styles.clock} />
          {formatSchedule(startAt, endAt)}
        </Typography>
      </div>

      <hr className={styles.divider} />

      <Typography className={styles.requestDescription}>
        <Trans>A calendar invitation has been sent to your email address.</Trans>
      </Typography>
    </>
  );
};

export default memo(CandidateConfirmed);
