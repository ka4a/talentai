import React, { useMemo, useCallback, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Modal, ModalBody, ModalHeader } from 'reactstrap';
import { Link } from 'react-router-dom';

import _ from 'lodash';
import PropTypes from 'prop-types';
import { Trans, t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import JobTitle from '@components/jobs/JobTitle';

import SwaggerTable, {
  TableHeader,
  useFetchTableData,
  useSwaggerTableState,
  TableInFilter,
} from '../../../../components/SwaggerTable';

const DEAL_STAGE_FILTER_MAP = {
  firstRound: 'first_round',
  intermediateRound: 'intermediate_round',
  finalRound: 'final_round',
  offer: 'offer',
  total: '',
};

function DealPipelineCandidatesModal({ isOpen, toggle, i18n, stageFilter }) {
  const dealStages = useSelector((state) =>
    _.get(state.settings.localeData, 'proposalDealStages', [])
  );
  const [state, setState] = useSwaggerTableState();

  useEffect(() => {
    setState((state) => ({
      ...state,
      params: {
        ...state.params,
        deal_stage__in: DEAL_STAGE_FILTER_MAP[stageFilter],
      },
    }));
  }, [stageFilter, setState]);

  const columns = useMemo(
    () => [
      {
        dataField: 'candidate.name',
        text: <Trans>Candidate name</Trans>,
        formatter: (cell, proposal, link) => <Link to={link}>{cell}</Link>,
      },
      {
        dataField: 'job',
        text: <Trans>Job title</Trans>,
        formatter: (cell) => <JobTitle job={cell} />,
      },
      {
        dataField: 'clientName',
        text: <Trans>Client</Trans>,
      },
      {
        dataField: 'dealStage',
        text: <Trans>Stage</Trans>,
        formatter: (cell) => _.find(dealStages, ({ value }) => value === cell).label,
        filter: (defaultAttrs) => (
          <TableInFilter
            {...defaultAttrs}
            filter='deal_stage__in'
            options={dealStages}
          />
        ),
      },
      {
        dataField: 'totalValue',
        text: <Trans>Total value</Trans>,
      },
      {
        dataField: 'realisticValue',
        text: <Trans>Realistic value</Trans>,
      },
    ],
    [dealStages]
  );

  const fetchTableData = useFetchTableData('deal_pipeline_list');
  const getLink = useCallback(
    (proposal) => `/job/${proposal.job.id}/proposal/${proposal.id}`,
    []
  );

  return (
    <Modal isOpen={isOpen} toggle={toggle} size='xl'>
      <ModalHeader tag='h1'>
        <Trans>Deal Pipeline</Trans>
      </ModalHeader>
      <ModalBody>
        <TableHeader
          title={i18n._(t`Candidates`)}
          state={state}
          setState={setState}
          search
        />
        <SwaggerTable
          primaryLink={getLink}
          columns={columns}
          fetchFn={fetchTableData}
          state={state}
          setState={setState}
          paginationKey='dealPipelineCandidatesShowPer'
        />
      </ModalBody>
    </Modal>
  );
}

DealPipelineCandidatesModal.propTypes = {
  stageFilter: PropTypes.string,
};

DealPipelineCandidatesModal.defaultProps = {
  stageFilter: '',
};

export default withI18n()(DealPipelineCandidatesModal);
