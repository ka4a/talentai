import React, { memo } from 'react';

import moment from 'moment';
import { Trans, t } from '@lingui/macro';

import { getFormattedDate } from '@utils';
import LabeledItem from '@components/UI/LabeledItem';
import Typography from '@components/UI/Typography';
import useGetCandidate from '@swrAPI/hooks/candidates/useGetCandidate';

import styles from '../CandidateDetailsSection.module.scss';

const PersonalInfoSection = () => {
  const { data: candidate } = useGetCandidate();

  return (
    <div className={styles.wrapper}>
      <Typography variant='subheading' className={styles.title}>
        <Trans>Personal</Trans>
      </Typography>

      <div className={styles.row}>
        <LabeledItem
          label={t`Date of Birth`}
          value={getFormattedDate(candidate.birthdate)}
        />
        <LabeledItem
          label={t`Age`}
          value={
            candidate.birthdate
              ? moment().diff(candidate.birthdate, 'years', false)
              : ''
          }
        />
        <LabeledItem label={t`Nationality`} value={candidate.nationality} />
        <LabeledItem label={t`Gender`} value={candidate.gender} />
      </div>
    </div>
  );
};

export default memo(PersonalInfoSection);
