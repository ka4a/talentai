import React, { useCallback, useState, memo } from 'react';
import { useParams, useHistory } from 'react-router';

import PropTypes from 'prop-types';
import _ from 'lodash';
import { Trans } from '@lingui/macro';

import { client } from '@client';

import SwaggerTable, {
  useFetchTableData,
  useSwaggerTableState,
} from '../../SwaggerTable';
import FeeModal from '../FeeModal/FeeModal';
import LocaleOptionLabel from '../../LocaleOptionLabel';

const joinContextualOptionLists = (options) => _.flatten(_.values(options));

function statusFormatter(status) {
  switch (status) {
    case 'pending':
      return (
        <span className='text-warning'>
          <Trans>Pending approval</Trans>
        </span>
      );
    case 'approved':
      return (
        <span className='text-success'>
          <Trans>Approved</Trans>
        </span>
      );
    case 'draft':
      return (
        <span className='text-muted'>
          <Trans>Draft</Trans>
        </span>
      );
    case 'needs_revision':
      return (
        <span className='text-danger'>
          <Trans>In revision</Trans>
        </span>
      );
    default:
      return (
        <span className='text-dark'>
          <Trans>Needs placement</Trans>
        </span>
      );
  }
}

const COLUMNS = [
  {
    dataField: 'contractType',
    text: <Trans>Contract Type</Trans>,
    formatter: (value) => (
      <LocaleOptionLabel optionsKey='jobContractTypes' value={value} />
    ),
  },
  {
    dataField: 'billDescription',
    text: <Trans>Bill Description</Trans>,
    formatter: (value) => (
      <LocaleOptionLabel
        optionsKey='billDescriptions'
        value={value}
        placeholder={value}
        processOptions={joinContextualOptionLists}
      />
    ),
  },
  {
    dataField: 'candidateName',
    text: <Trans>Candidate Name</Trans>,
  },
  {
    dataField: 'clientName',
    text: <Trans>Client</Trans>,
  },
  {
    dataField: 'jobTitle',
    text: <Trans>Job Title</Trans>,
  },
  {
    dataField: 'submittedByName',
    text: <Trans>Submitted By</Trans>,
  },
  {
    dataField: 'submittedAt',
    text: <Trans>Submission Date</Trans>,
  },
  {
    dataField: 'feeStatus',
    text: <Trans>Status</Trans>,
    formatter: statusFormatter,
  },
];

const PROPOSAL_COLUMNS = COLUMNS.filter(
  (columnDef) =>
    !['feeStatus', 'billDescription', 'submittedByName', 'submittedAt'].includes(
      columnDef.dataField
    )
);

FeeApprovalsTable.propTypes = {
  i18n: PropTypes.shape({
    _: PropTypes.func,
  }),
  baseUrl: PropTypes.string.isRequired,
  type: PropTypes.oneOf(['placement', 'fee', 'proposal']),
};

const fetchObj = (operationId, id) =>
  client.execute({
    operationId,
    parameters: { id },
  });

function FeeApprovalsTable(props) {
  const { type, baseUrl } = props;
  const { feeId } = useParams();
  const history = useHistory();

  const [state, setState] = useSwaggerTableState({
    params: {
      stage: 'shortlist',
      status__group: 'offer_accepted',
      is_placement_available: true,
    },
  });

  const [isClosing, setIsClosing] = useState(false);
  const [modalDataNewPlacement, setModalDataNewPlacement] = useState(null);

  const getLink = useCallback(({ feeId }) => (feeId ? `${baseUrl}/${feeId}` : null), [
    baseUrl,
  ]);

  const handleRowClick = useCallback((event, { feeId, proposalId, jobContractId }) => {
    if (feeId != null) return;

    Promise.all([
      fetchObj('proposals_read', proposalId),
      fetchObj('job_agency_contracts_read', jobContractId),
    ]).then(([proposal, jobContract]) => {
      setModalDataNewPlacement({
        proposal: proposal.obj,
        jobContract: jobContract.obj,
      });
    });
  }, []);

  const isEditing = feeId != null;

  const setIsEditing = useCallback(
    (newValue) => {
      if (typeof newValue === 'function') newValue = newValue(isEditing);
      if (!newValue) {
        setIsClosing(true);
        history.push(baseUrl);
      }
    },
    [history, isEditing, baseUrl]
  );

  const isCreating = modalDataNewPlacement != null;

  const setIsCreating = useCallback(
    (newValue) => {
      if (typeof newValue === 'function') newValue = newValue(isCreating);
      if (!newValue) {
        setModalDataNewPlacement(null);
      }
    },
    [isCreating]
  );

  const fetchFn = useFetchTableData('approval_list');
  const params = state.params;

  const handleSaved = useCallback(() => {
    fetchFn(params).then(setState);
  }, [fetchFn, params, setState]);

  const handleClosed = useCallback(() => {
    setIsClosing(false);
  }, []);

  return (
    <>
      <SwaggerTable
        state={state}
        setState={setState}
        onRowClick={handleRowClick}
        fetchFn={fetchFn}
        columns={type === 'proposal' ? PROPOSAL_COLUMNS : COLUMNS}
        primaryLink={getLink}
        params={{ type }}
        paginationKey='candidatePlacementsShowPer'
      />
      {isEditing || isClosing ? (
        <FeeModal
          noButton
          feeId={feeId}
          setIsOpen={setIsEditing}
          isOpen={isEditing}
          onSaved={handleSaved}
          onClosed={handleClosed}
        />
      ) : null}
      {isCreating ? (
        <FeeModal
          noButton
          feeId={feeId}
          setIsOpen={setIsCreating}
          isOpen={isCreating}
          proposal={modalDataNewPlacement.proposal}
          jobContract={modalDataNewPlacement.jobContract}
          onSaved={handleSaved}
          onClosed={handleClosed}
        />
      ) : null}
    </>
  );
}

export default memo(FeeApprovalsTable);
