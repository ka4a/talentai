import React, { memo, useCallback } from 'react';

import { useIsAuthenticatedByRoles } from '@hooks';
import { Badge, StagesDropdown } from '@components';
import { useOrgProposalStatuses, useProposalsRead } from '@swrAPI';
import {
  CLIENT_ADMINISTRATORS,
  CLIENT_INTERNAL_RECRUITERS,
  PROPOSAL_STAGES,
} from '@constants';

import styles from './StagesPipeline.module.scss';

const StagesPipeline = () => {
  const { data } = useProposalsRead();
  const { job = {}, stage: currentStage } = data;

  const isAdmin = useIsAuthenticatedByRoles([
    CLIENT_ADMINISTRATORS,
    CLIENT_INTERNAL_RECRUITERS,
  ]);

  const stages = useOrgProposalStatuses(job.orgId, job.orgType);

  const getBadgeVariant = useCallback(
    (stage) => {
      if (currentStage === PROPOSAL_STAGES.hired && currentStage === stage)
        return 'success';
      if (currentStage === stage) return 'normal';
      return 'neutral';
    },
    [currentStage]
  );

  return (
    <div className={styles.wrapper}>
      {Object.keys(stages).map((stage) =>
        isAdmin ? (
          <StagesDropdown key={stage} title={stage} options={stages[stage]} />
        ) : (
          <Badge text={stage} variant={getBadgeVariant(stage)} />
        )
      )}
    </div>
  );
};

export default memo(StagesPipeline);
