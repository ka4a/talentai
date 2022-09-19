import React, { memo } from 'react';

import { t, Trans } from '@lingui/macro';

import { StatusBar, Typography } from '@components';

import styles from '../CandidateConfirmation.module.scss';

const RequestAdditionalTimeslots = () => (
  <>
    <StatusBar
      className={styles.statusBar}
      variant='regular'
      text={t`Request submitted`}
    />

    <Typography className={styles.requestDescription}>
      <div>
        <Trans>
          We let the company know that none of these time slots are working.
        </Trans>
      </div>

      <div>
        <Trans>They will get back to you with new time slots shortly.</Trans>
      </div>
    </Typography>
  </>
);

export default memo(RequestAdditionalTimeslots);
