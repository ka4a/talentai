import React, { memo } from 'react';

import { t, Trans } from '@lingui/macro';

import { LabeledItem, Typography } from '@components';
import { useProposalsRead } from '@swrAPI';

import styles from './Sections.module.scss';

const ApplicationCandidates = () => {
  const { data } = useProposalsRead();
  const { candidate } = data;

  return (
    <div className={styles.halfSection}>
      <Typography variant='subheading' className={styles.title}>
        <Trans>Candidate</Trans>
      </Typography>

      <LabeledItem
        className={styles.row}
        label={t`Current Job Title`}
        value={candidate?.currentPosition}
      />

      <LabeledItem
        className={styles.row}
        label={t`Current Employer`}
        value={candidate?.currentCompany}
      />

      <LabeledItem
        className={styles.row}
        label={t`Source`}
        value={candidate?.source || data?.source?.name}
      />
    </div>
  );
};

export default memo(ApplicationCandidates);
