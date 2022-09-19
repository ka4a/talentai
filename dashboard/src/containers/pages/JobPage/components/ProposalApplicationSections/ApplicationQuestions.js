import React, { memo } from 'react';

import { Trans } from '@lingui/macro';

import { Typography } from '@components';
import { useProposalsRead } from '@swrAPI';

import ProposalQuestion from '../ProposalQuestion';

import styles from './Sections.module.scss';

const ApplicationQuestions = () => {
  const { data } = useProposalsRead();
  const { questions } = data;

  if (!questions?.length) return null;

  return (
    <div className={styles.itemsSection}>
      <div className={styles.itemHeaderWrapper}>
        <Typography variant='subheading'>
          <Trans>Screening Questions</Trans>
        </Typography>
      </div>

      <div className={styles.itemsList}>
        {questions.map((question, index) => (
          <ProposalQuestion key={question.id} index={index + 1} question={question} />
        ))}
      </div>
    </div>
  );
};

export default memo(ApplicationQuestions);
