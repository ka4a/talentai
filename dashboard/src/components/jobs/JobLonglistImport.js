import React, { useState, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { Button, Label } from 'reactstrap';

import _ from 'lodash';
import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import { client } from '@client';
import { CLIENT_GROUPS } from '@constants';

import SwaggerTable, { TableHeader } from '../SwaggerTable';
import { useSwaggerTableState, useFetchTableData } from '../SwaggerTable';
import OptionsProvider from './OptionsProvider';
import SelectInput from '../SelectInput';
import Checkbox from '../UI/Checkbox';

function JobLonglistImport({ i18n, onSuccess, onError, jobId }) {
  const user = useSelector((state) => state.user);

  const [candidatesToImport, setCandidates] = useState([]);
  const [state, setState] = useSwaggerTableState({
    params: { stage: 'longlist' },
  });
  const fetchTableData = useFetchTableData('proposals_list');

  const setFromJob = useCallback(
    (job) => {
      setState((state) => ({
        ...state,
        params: {
          ...state.params,
          job,
        },
      }));
      setCandidates([]);
    },
    [setState]
  );

  const getJobLabel = useCallback(
    (job) => {
      if (_.intersection(user.groups, CLIENT_GROUPS).length > 0) {
        return job.title;
      } else {
        return `${job.clientName} - ${job.title}`;
      }
    },
    [user]
  );
  const getJobValue = useCallback((job) => job.id, []);
  const jobFilterPredicate = useCallback((job) => job.id !== jobId, [jobId]);

  const isCandidateSelected = (id) => Boolean(candidatesToImport.indexOf(id) + 1);

  const onSelectCandidate = (candidateId) => {
    if (isCandidateSelected(candidateId)) {
      setCandidates((state) => _.filter(state, (id) => id !== candidateId));
    } else {
      setCandidates((state) => [...state, candidateId]);
    }
  };

  const getAllCandidates = () => {
    const data = _.get(state, 'data.results', []);
    return _.map(data, (row) => row.candidate.id);
  };

  const areAllSelected = () => {
    return (
      candidatesToImport.length &&
      _.isEqual(getAllCandidates().sort(), candidatesToImport.sort())
    );
  };

  const selectAll = () => {
    if (areAllSelected()) {
      setCandidates([]);
    } else {
      setCandidates((state) => _.uniq([...state, ...getAllCandidates()]));
    }
  };

  const importCandidates = () => {
    client
      .execute({
        operationId: 'job_import_longlist',
        parameters: {
          id: jobId,
          data: {
            fromJob: state.params.job,
            candidates: candidatesToImport,
          },
        },
      })
      .then(onSuccess)
      .catch(onError);
  };

  const columns = [
    {
      dataField: 'candidate.name',
      text: <Trans>Name</Trans>,
    },
    {
      dataField: 'action',
      text: <Trans>Total Selected: {candidatesToImport.length}</Trans>,
      align: 'right',
      formatter: (cell, proposal) => (
        <Checkbox
          checked={isCandidateSelected(proposal.candidate.id)}
          onChange={() => onSelectCandidate(proposal.candidate.id)}
        />
      ),
    },
  ];

  return (
    <>
      <OptionsProvider
        operationId='jobs_list'
        getLabel={getJobLabel}
        getValue={getJobValue}
        filterPredicate={jobFilterPredicate}
      >
        <SelectInput
          placeholder={i18n._(t`Select Job`)}
          className='py-3'
          searchable
          value={state.params.job}
          onSelect={setFromJob}
        />
      </OptionsProvider>
      {state.params.job ? (
        <>
          <TableHeader
            search
            state={state}
            setState={setState}
            rightSide={
              <Label className='ml-2' check>
                <Checkbox
                  checked={areAllSelected()}
                  onChange={selectAll}
                  isDisabled={!getAllCandidates().length}
                />
                <Trans>Select all</Trans>
              </Label>
            }
          />
          <SwaggerTable
            state={state}
            setState={setState}
            columns={columns}
            fetchFn={fetchTableData}
            paginationKey='jobImportLonglistShowPer'
          />
          <div className='mt-3 d-flex justify-content-end'>
            <Button
              color='primary'
              disabled={!candidatesToImport.length}
              onClick={importCandidates}
            >
              <Trans>Import</Trans>
            </Button>
          </div>
        </>
      ) : null}
    </>
  );
}

export default withI18n()(JobLonglistImport);
