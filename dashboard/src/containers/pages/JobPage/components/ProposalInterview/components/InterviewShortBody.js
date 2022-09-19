import React, { memo } from 'react';

import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

import { LabeledItem } from '@components';

import styles from '../ProposalInterview.module.scss';

const InterviewShortBody = ({ interview, interviewerName }) => (
  <div className={styles.details}>
    <div className={styles.interviewerWrapper}>
      <LabeledItem label={t`Interviewer`} value={interviewerName} />
    </div>

    <LabeledItem
      label={t`Interview Details`}
      variant='textarea'
      value={interview.description}
    />
  </div>
);

InterviewShortBody.propTypes = {
  interview: PropTypes.shape({}).isRequired,
  interviewerName: PropTypes.string.isRequired,
};

export default memo(InterviewShortBody);
