import React, { useCallback, memo } from 'react';
import { useHistory } from 'react-router';
import { useParams } from 'react-router-dom';

import { useGetJob } from '@swrAPI';
import { ProposalsPipeline, TableDetailsLayout } from '@components';

import ApplicationStages from '../ApplicationStages';
import Proposal from '../Proposal';

const Applications = () => {
  const history = useHistory();
  const { proposalId } = useParams();

  const { data: job } = useGetJob();
  const { id, organization, proposalsPipeline, openingsCount } = job;

  const closeCandidate = useCallback(() => {
    history.push(`/job/${id}`);
  }, [history, id]);

  return (
    <TableDetailsLayout
      onClose={closeCandidate}
      isOpen={Boolean(proposalId)}
      header={
        <ProposalsPipeline
          pipeline={proposalsPipeline}
          openingsCount={openingsCount}
          jobOrgType={organization.type}
          isCard
        />
      }
      renderTable={() => <ApplicationStages />}
      renderDetails={() => <Proposal />}
    />
  );
};

export default memo(Applications);
