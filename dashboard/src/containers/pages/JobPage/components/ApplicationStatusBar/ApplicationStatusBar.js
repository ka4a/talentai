import React, { memo, useMemo } from 'react';

import { t } from '@lingui/macro';

import { StatusBar } from '@components';
import { useProposalsRead } from '@swrAPI';
import { formatStageLabel, getLongInterviewName } from '@utils';

import styles from '../ProposalApplication/ProposalApplication.module.scss';

const renderRejectedLabel = (by, reason) => (
  <span>
    {t`Rejected by ${by}:`}
    <span className={styles.reason}>{reason}</span>
  </span>
);

const ApplicationStatusBar = () => {
  const { data } = useProposalsRead();
  const { isRejected } = data;

  const rejectedStatusLabel = useRejectedStatusLabel(data);
  const statusLabel = useStatusLabel(data);

  return (
    <StatusBar
      className={styles.statusBar}
      variant={getStatusBarVariant(data)}
      text={isRejected ? rejectedStatusLabel : statusLabel}
    />
  );
};

function getStatusBarVariant(proposal) {
  const { isRejected, stage } = proposal;

  if (isRejected) return 'danger';
  if (stage === 'hired') return 'success';
  return 'regular';
}

const useRejectedStatusLabel = (proposal) => {
  const {
    declineReasons,
    reasonsNotInterested,
    reasonDeclinedDescription,
    reasonNotInterestedDescription,
  } = proposal;

  const companyDeclineReason = reasonDeclinedDescription || declineReasons[0]?.text;
  if (companyDeclineReason) {
    return renderRejectedLabel(t`Company`, companyDeclineReason);
  }

  const candidateNotInterestedReason =
    reasonNotInterestedDescription || reasonsNotInterested[0]?.text;
  if (candidateNotInterestedReason) {
    return renderRejectedLabel(t`Candidate`, candidateNotInterestedReason);
  }
};

const useStatusLabel = (proposal) => {
  const { job, status, currentInterview } = proposal;

  const statusLabel = useMemo(
    () =>
      status.group === 'interviewing'
        ? getLongInterviewName(currentInterview)
        : status?.status ?? '',
    [currentInterview, status]
  );

  const orgType = job?.orgType;

  return useMemo(() => formatStageLabel(statusLabel, orgType), [statusLabel, orgType]);
};

export default memo(ApplicationStatusBar);
