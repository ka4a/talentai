import React from 'react';

import { t, Trans } from '@lingui/macro';

import { TablePlaceholder, Typography } from '@components';
import jobIcon from '@images/icons/job.svg';

import styles from './NoJobPostingsPlaceholder.module.scss';

function NoJobPostingsPlaceholder() {
  return (
    <TablePlaceholder
      title={t`No Current Openings`}
      icon={
        <div className={styles.iconCircle}>
          <img src={jobIcon} width={63} height={55} alt='no-jobs' />
        </div>
      }
    >
      <Trans>
        <Typography>Thank you for your interest!</Typography>
        <br />
        <Typography>Please check back soon.</Typography>
      </Trans>
    </TablePlaceholder>
  );
}

export default NoJobPostingsPlaceholder;
