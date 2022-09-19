import React, { memo } from 'react';

import { t, Trans } from '@lingui/macro';

import { StatusBar, Typography } from '@components';

import styles from '../InterviewSchedulingModal.module.scss';

const NoEmailMessage = () => (
  <div className={styles.bottomGap}>
    <StatusBar variant='danger' text={t`Candidate has no email!`} />

    <Typography variant='caption' className={styles.error}>
      <span>
        <Trans>This invitation will not be sent to the Candidate.</Trans>
      </span>

      <span>
        <Trans>Please invite the Candidate to this interview outside ZooKeep.</Trans>
      </span>
    </Typography>
  </div>
);

export default memo(NoEmailMessage);
