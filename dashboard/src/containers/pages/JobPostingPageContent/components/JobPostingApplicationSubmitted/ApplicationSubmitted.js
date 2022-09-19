import React, { memo } from 'react';

import { t, Trans } from '@lingui/macro';
import PropTypes from 'prop-types';

import { StatusBar, Typography, WindowBackground } from '@components';

import styles from './ApplicationSubmitted.module.scss';

const ApplicationSubmitted = ({ email }) => (
  <WindowBackground className={styles.container}>
    <Typography variant='h3'>
      <Trans>Application Submitted</Trans>
    </Typography>

    <StatusBar
      className={styles.statusBar}
      variant='success'
      text={t`Thank you for applying to this job!`}
    />

    <Typography className={styles.text}>
      <Trans>
        The company has been notified and will review your application shortly.
        <br />A confirmation email has been sent to{' '}
        <span className={styles.email}>{email}</span>.
      </Trans>
    </Typography>
  </WindowBackground>
);

ApplicationSubmitted.propTypes = {
  email: PropTypes.string.isRequired,
};

export default memo(ApplicationSubmitted);
