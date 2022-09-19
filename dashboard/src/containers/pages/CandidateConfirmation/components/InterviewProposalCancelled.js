import React, { memo } from 'react';

import { t, Trans } from '@lingui/macro';
import parse from 'html-react-parser';

import { StatusBar, Typography } from '@components';

import styles from '../CandidateConfirmation.module.scss';

const InterviewProposalCancelled = ({ message }) => (
  <>
    <StatusBar
      className={styles.statusBar}
      variant='warning'
      text={t`This interview proposal link is no longer valid`}
    />

    {message && (
      <Typography className={styles.requestDescription}>
        <div className={styles.highlight}>
          <Trans>Message from company:</Trans>
        </div>

        <Typography hasParsedMarkup>{parse(message)}</Typography>
      </Typography>
    )}
  </>
);

export default memo(InterviewProposalCancelled);
