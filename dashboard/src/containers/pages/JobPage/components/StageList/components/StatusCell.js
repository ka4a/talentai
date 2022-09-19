import React, { memo } from 'react';
import { useParams } from 'react-router-dom';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import { Typography } from '@components';
import { PROPOSAL_STAGES } from '@constants';
import { getLongInterviewName } from '@utils';
import { useIsAuthenticatedByRoles } from '@hooks';
import { CLIENT_ADMINISTRATORS, CLIENT_INTERNAL_RECRUITERS } from '@constants';

import StatusesDropdown from '../../StatusesDropdown';

import styles from '../StageList.module.scss';

const StatusCell = ({ proposal }) => {
  const { proposalId } = useParams();

  const isAdmin = useIsAuthenticatedByRoles([
    CLIENT_ADMINISTRATORS,
    CLIENT_INTERNAL_RECRUITERS,
  ]);

  const isCollapsed = Boolean(proposalId);
  const isCurrentProposal = Number(proposal.id) === Number(proposalId);
  const isInterviewing = proposal.stage === PROPOSAL_STAGES.interviewing;

  return isAdmin && !isInterviewing && (isCurrentProposal || !isCollapsed) ? (
    <StatusesDropdown
      stage={proposal.stage}
      proposalId={proposal.id}
      currentStatus={proposal.status}
      isDisabled={Boolean(proposal.isRejected)}
    />
  ) : (
    <Typography
      variant='caption'
      className={classnames({ [styles.whiteText]: isCollapsed && isCurrentProposal })}
    >
      {isInterviewing
        ? getLongInterviewName(proposal.currentInterview)
        : proposal.status.status}
    </Typography>
  );
};

StatusCell.propTypes = {
  proposal: PropTypes.shape({}).isRequired,
};

export default memo(StatusCell);
