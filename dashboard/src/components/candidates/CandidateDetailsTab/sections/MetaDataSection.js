import React, { memo } from 'react';

import { Trans, t } from '@lingui/macro';

import { getFormattedDate } from '@utils';
import LabeledItem from '@components/UI/LabeledItem';
import Typography from '@components/UI/Typography';
import useGetCandidate from '@swrAPI/hooks/candidates/useGetCandidate';

import styles from '../CandidateDetailsSection.module.scss';

const MetaDataSection = () => {
  const { data: candidate } = useGetCandidate();

  return (
    <div className={styles.wrapper}>
      <Typography variant='subheading' className={styles.title}>
        <Trans>MetaData</Trans>
      </Typography>

      <div className={styles.row}>
        <LabeledItem
          label={t`Created By`}
          value={
            candidate.createdBy &&
            `${candidate.createdBy.firstName} ${candidate.createdBy?.lastName}`
          }
        />

        <LabeledItem label={t`ID`} value={candidate.createdBy?.id} />
      </div>

      <br />

      <div className={styles.row}>
        <LabeledItem
          label={t`Created Date`}
          value={getFormattedDate(candidate.createdAt)}
        />

        <LabeledItem
          label={t`Modified Date`}
          value={getFormattedDate(candidate.updatedAt)}
        />
      </div>
    </div>
  );
};

export default memo(MetaDataSection);
