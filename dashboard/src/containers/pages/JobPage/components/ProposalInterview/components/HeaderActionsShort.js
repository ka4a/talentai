import React, { memo } from 'react';

import { Trans } from '@lingui/macro';
import PropTypes from 'prop-types';

import { CollapseArrowButton, Typography } from '@components';

import styles from '../ProposalInterview.module.scss';

const HeaderActionsShort = ({ interview, isOpen, interviewerName, isDisabled }) => (
  <div className={styles.headerRight}>
    {interview.interviewer && !isOpen && (
      <div className={styles.headerInterviewer}>
        <Typography variant='caption' className={styles.interviewer}>
          <Trans>Interviewer:</Trans>
        </Typography>

        <Typography>{interviewerName}</Typography>
      </div>
    )}

    <CollapseArrowButton
      isOpen={isOpen}
      isDisabled={isDisabled}
      className={styles.collapseArrow}
    />
  </div>
);

HeaderActionsShort.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  isDisabled: PropTypes.bool.isRequired,
  interview: PropTypes.shape({}).isRequired,
  interviewerName: PropTypes.string.isRequired,
};

export default memo(HeaderActionsShort);
