import React, { memo, useMemo } from 'react';

import { t, Trans } from '@lingui/macro';

import { LabeledItem, Typography } from '@components';
import { useGetJob, useProposalsRead } from '@swrAPI';

import styles from './Sections.module.scss';

const ApplicationJob = () => {
  const { data: jobData } = useGetJob();
  const { data: proposalData } = useProposalsRead();

  const { job } = proposalData;
  const { managers, department } = jobData;

  const managersString = useMemo(
    () =>
      managers.map((manager) => `${manager.firstName} ${manager.lastName}`).join(', '),
    [managers]
  );

  return (
    <div className={styles.halfSection}>
      <Typography variant='subheading' className={styles.title}>
        <Trans>Job</Trans>
      </Typography>

      <LabeledItem
        className={styles.row}
        label={t`Applied Job Title`}
        value={job?.title}
      />

      <LabeledItem className={styles.row} label={t`Department`} value={department} />

      <LabeledItem
        className={styles.row}
        label={t`Hiring Manager`}
        value={managersString}
      />
    </div>
  );
};

export default memo(ApplicationJob);
