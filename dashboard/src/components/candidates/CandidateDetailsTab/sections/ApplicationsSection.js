import React, { memo } from 'react';

import classnames from 'classnames';
import { Trans } from '@lingui/macro';

import { useGetCandidate } from '@swrAPI';
import { Badge, Typography } from '@components';

import styles from '../CandidateDetailsSection.module.scss';

const ApplicationsSection = () => {
  const { data: candidate } = useGetCandidate();

  const getBadgeVariant = (stage) => {
    const variants = {
      associated: 'neutral',
      interviewing: 'normal',
      hired: 'success',
      rejected: 'danger',
    };
    return variants[stage] ?? 'neutral';
  };

  if (!candidate.proposals?.length) {
    return null;
  }

  return (
    <div className={styles.wrapper}>
      <Typography variant='subheading' className={styles.title}>
        <Trans>Job Applications</Trans>
      </Typography>

      {candidate.proposals?.map((proposal) => (
        <div key={proposal.id} className={classnames([styles.applicationRow])}>
          <Typography>{proposal.jobName}</Typography>

          <div>
            <Badge variant={getBadgeVariant(proposal.stage)} text={proposal.stage} />
          </div>
        </div>
      ))}
    </div>
  );
};

export default memo(ApplicationsSection);
