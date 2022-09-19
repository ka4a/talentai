import React, { memo } from 'react';

import { Trans } from '@lingui/macro';

import { ReqStatus, Typography, WindowBackground } from '@components';

import styles from '../AuthPage.module.scss';

const LoginInProgress = () => (
  <WindowBackground className={styles.contentWrapper}>
    <Typography variant='h1' className={styles.contentHeader}>
      <Trans>Please wait</Trans>
    </Typography>
    <Typography>
      <ReqStatus loading />
    </Typography>
  </WindowBackground>
);

export default memo(LoginInProgress);
