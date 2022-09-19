import React, { memo, useCallback, useMemo } from 'react';

import PropTypes from 'prop-types';

import { fetchErrorHandler } from '@utils';
import { Dropdown } from '@components';
import { client } from '@client';
import {
  useGetJob,
  useOrgProposalStatuses,
  useProposalsList,
  useProposalsRead,
} from '@swrAPI';

import StatusesDropdownTrigger from './StatusesDropdownTrigger';

const StatusesDropdown = (props) => {
  const { currentStatus, stage, proposalId, isDisabled } = props;

  const { data: job, mutate: refreshJob } = useGetJob();
  const { mutate: refreshProposal } = useProposalsRead();
  const { mutate: refreshStages } = useProposalsList();

  const stagesStatuses = useOrgProposalStatuses(
    job.organization?.id,
    job.organization?.type
  );
  const statuses = stagesStatuses[stage];

  const options = useMemo(
    () => statuses?.map(({ value, label }) => ({ id: value, label })) ?? [],
    [statuses]
  );

  const handleChangeProposalStatus = useCallback(
    async ({ id }) => {
      try {
        await client.execute({
          operationId: 'proposals_partial_update',
          parameters: { id: proposalId, data: { status: id } },
        });

        await Promise.all([refreshJob(), refreshProposal(), refreshStages()]);
      } catch (error) {
        fetchErrorHandler(error);
      }
    },
    [proposalId, refreshJob, refreshProposal, refreshStages]
  );

  return (
    <Dropdown
      options={options}
      isDisabled={isDisabled}
      selected={currentStatus.id}
      handleChange={handleChangeProposalStatus}
      trigger={
        <StatusesDropdownTrigger value={currentStatus.status} isDisabled={isDisabled} />
      }
    />
  );
};

StatusesDropdown.propTypes = {
  currentStatus: PropTypes.shape({
    id: PropTypes.number,
    status: PropTypes.string,
  }).isRequired,
  stage: PropTypes.string.isRequired,
  proposalId: PropTypes.number.isRequired,
  isDisabled: PropTypes.bool.isRequired,
};

export default memo(StatusesDropdown);
