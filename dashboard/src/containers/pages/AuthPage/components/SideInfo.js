import React, { memo } from 'react';

import { Trans } from '@lingui/macro';

import { Logo, Typography } from '@components';

import styles from '../AuthPage.module.scss';

const SideInfo = () => (
  <div className={styles.sideInfoWrapper}>
    <div />

    <div className={styles.sideInfo}>
      <Logo variant='h1' />
      <Typography variant='h2' className={styles.description}>
        <Trans>Your Talent Acquisition Enabler</Trans>
      </Typography>
    </div>

    <div className={styles.footer}>
      <Typography variant='caption' className={styles.footerText}>
        <Trans>© {new Date().getFullYear()} ZooKeep</Trans>
      </Typography>

      <Typography variant='caption' className={styles.footerText}>
        <Trans>All Rights Reserved.</Trans>
      </Typography>
    </div>
  </div>
);

export default memo(SideInfo);
