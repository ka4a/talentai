import React, { memo } from 'react';

import classnames from 'classnames';
import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import { Typography, WindowBackground } from '@components';

import styles from '../AuthPage.module.scss';

const InstructionsSent = ({ email }) => (
  <WindowBackground className={styles.contentWrapper}>
    <Typography
      variant='h1'
      className={classnames([styles.contentHeader, styles.instructionsText])}
    >
      <Trans>Instructions sent!</Trans>
    </Typography>

    <Typography
      className={classnames([styles.instructionsText, styles.instructionsGap])}
    >
      <Trans>Instructions for resetting your password have been sent to {email}</Trans>
    </Typography>

    <Typography className={styles.instructionsText}>
      <Trans>You’ll receive this email within 5 minutes.</Trans>
    </Typography>

    <Typography className={styles.instructionsText}>
      <Trans>Be sure to check your spam folder, too.</Trans>
    </Typography>
  </WindowBackground>
);

InstructionsSent.propTypes = {
  email: PropTypes.string.isRequired,
};

export default memo(InstructionsSent);
