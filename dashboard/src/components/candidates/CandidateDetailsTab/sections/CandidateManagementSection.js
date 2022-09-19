import React, { memo } from 'react';

import { Trans, t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { useStaffOptions } from '@swrAPI';
import { CANDIDATE_SOURCE_CHOICES, PLATFORM_CHOICES } from '@constants';
import Typography from '@components/UI/Typography';
import LabeledItem from '@components/UI/LabeledItem';
import useGetCandidate from '@swrAPI/hooks/candidates/useGetCandidate';
import { useTranslatedChoices } from '@hooks';
import { LabeledChoiceName } from '@components';

import styles from '../CandidateDetailsSection.module.scss';

const CandidateManagementSection = () => {
  const { i18n } = useLingui();
  const candidateSourceChoices = useTranslatedChoices(i18n, CANDIDATE_SOURCE_CHOICES);
  const platformChoices = useTranslatedChoices(i18n, PLATFORM_CHOICES);

  const { data: candidate } = useGetCandidate();
  const staffList = useStaffOptions();

  return (
    <div className={styles.wrapper}>
      <Typography variant='subheading' className={styles.title}>
        <Trans>Candidate Management</Trans>
      </Typography>

      <div className={styles.detailList}>
        <div className={styles.multiRowWrapper}>
          <LabeledChoiceName
            label={t`Source`}
            choices={candidateSourceChoices}
            value={candidate.source}
            otherChoiceValue='Other'
            otherChoiceName={candidate.sourceDetails}
          />
          <LabeledChoiceName
            label={t`Platform`}
            choices={platformChoices}
            value={candidate.platform}
            otherChoiceValue='other'
            otherChoiceName={candidate.platformOtherDetails}
          />
          <LabeledChoiceName
            label={t`Sourced By`}
            choices={staffList}
            value={candidate.owner}
          />
        </div>

        <LabeledItem
          label={t`Candidate Notes`}
          value={candidate.note}
          variant='textarea'
        />
      </div>
    </div>
  );
};

export default memo(CandidateManagementSection);
