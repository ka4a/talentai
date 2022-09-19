import React, { useState, useEffect } from 'react';
import { connect } from 'react-redux';
import { Modal, ModalBody, ModalHeader } from 'reactstrap';

import PropTypes from 'prop-types';
import _ from 'lodash';
import moment from 'moment';
import { Trans, Plural } from '@lingui/macro';

import { TALENT_ASSOCIATES } from '@constants';

import SwaggerTable, {
  TableHeader,
  TableInFilter,
  useFetchTableData,
  useSwaggerTableState,
} from '../../../../components/SwaggerTable';
import { useSwagger } from '../../../../hooks';
import SelectInput from '../../../../components/SelectInput';
import { ShowAuthenticated } from '../../../../components/auth';

const QUERY_DATE_FORMAT = 'YYYY-MM-DD';

const dayFormatter = (d) => moment(d).format('MMMM Do');
const weekPeriodFormatter = (d) => {
  const start = moment(d).format('MMMM Do');
  const now = moment();
  const end = moment(d).add(1, 'weeks');
  if (end > now) {
    return `${start} ~ ${now.format('MMMM Do')}`;
  }
  return `${start} ~ ${end.format('MMMM Do')}`;
};
const monthFormatter = (d) => moment(d).format("MMMM 'YY");

const wrapper = connect((state) => ({
  longlistStatuses: state.settings.localeData.proposalLonglistStatuses,
  shortlistStatuses: state.settings.localeData.proposalShortlistStatuses,
}));

function DatePeriod(props) {
  const {
    params: { granularity, date },
  } = props;

  switch (granularity) {
    case 'day':
      return <>({dayFormatter(date)})</>;
    case 'week':
      return <>({weekPeriodFormatter(date)})</>;
    case 'month':
      return <>({monthFormatter(date)})</>;
    default:
      return;
  }
}

function HiddenProposals(props) {
  const { params, operationId } = props;

  const { obj: data } = useSwagger(`${operationId}_hidden_proposals`, { ...params });
  const hidden = _.get(data, 'hidden');
  return hidden ? (
    <div className='mt-24 font-weight-bold fs-16 text-muted'>
      <Plural
        value={hidden}
        _1='# candidate from agency longlist is not visible in the table'
        other='# candidates from agency longlist are not visible in the table'
      />
    </div>
  ) : null;
}

const DIFF_OPERATION_ID = 'proposals_snapshot_diff';
const STATE_OPERATION_ID = 'proposals_snapshot_state';

const SnapshotProposalStatus = wrapper(function (props) {
  const { status, longlistStatuses } = props;
  const stages = {
    shortlist: <Trans>Shortlist</Trans>,
    longlist: <Trans>Longlist</Trans>,
  };

  const stage = _.find(longlistStatuses, status) ? 'longlist' : 'shortlist';

  return (
    <span className='d-flex align-items-center'>
      <span className='text-dark mr-2'>{stages[stage]}</span>
      <span>({status.status})</span>
    </span>
  );
});

function SnapshotTableModal(props) {
  const {
    params,
    isOpen,
    toggle,
    job,
    onClosed,
    longlistStatuses,
    shortlistStatuses,
  } = props;

  const requestParams = {
    date: params.date,
    job: params.job,
    granularity: params.granularity,
    date_start: moment(params.dateStart).format(QUERY_DATE_FORMAT),
    date_end: moment(params.dateEnd).format(QUERY_DATE_FORMAT),
  };

  const [operationId, setOperationId] = useState(DIFF_OPERATION_ID);

  const [tableData, setTableData] = useSwaggerTableState();
  const fetchTableData = useFetchTableData(`${operationId}_list`);

  useEffect(() => {
    setTableData((state) => ({
      ...state,
      params: {
        ...state.params,
        status__in: params.status__in,
      },
    }));
  }, [params.status__in, setTableData]);

  const statuses = _.concat(longlistStatuses, shortlistStatuses);

  const getStatusOptions = () => {
    const longlistLabel = { type: 'title', label: <Trans>Longlist</Trans> };
    const shortlistLabel = { type: 'title', label: <Trans>Shortlist</Trans> };

    const optionize = (statuses, type) => {
      return _.map(statuses, (s) => ({
        value: s.id,
        label: s.status,
      }));
    };

    const longlistOptions = optionize(longlistStatuses, 'longlist');
    const shortlistOptions = optionize(shortlistStatuses, 'shortlist');

    return _.concat(
      [longlistLabel],
      longlistOptions,
      [shortlistLabel],
      shortlistOptions
    );
  };

  const getSnapshotOptions = () => {
    let diffLabel = null;
    let stateLabel = null;
    switch (params.granularity) {
      case 'day':
        diffLabel = <Trans>This day</Trans>;
        stateLabel = <Trans>Up to this day</Trans>;
        break;
      case 'week':
        diffLabel = <Trans>This week</Trans>;
        stateLabel = <Trans>Up to this week</Trans>;
        break;
      case 'month':
        diffLabel = <Trans>This month</Trans>;
        stateLabel = <Trans>Up to this month</Trans>;
        break;
      default:
        break;
    }

    return [
      { value: DIFF_OPERATION_ID, label: diffLabel },
      { value: STATE_OPERATION_ID, label: stateLabel },
    ];
  };

  const columns = [
    {
      dataField: 'candidate',
      text: <Trans>Candidate</Trans>,
      formatter: (cell) => cell.name,
    },
    {
      dataField: 'candidate',
      text: <Trans>Company</Trans>,
      formatter: (cell) => cell.currentCompany,
    },
    {
      dataField: 'candidate',
      text: <Trans>Current Job Title</Trans>,
      formatter: (cell) => cell.currentPosition,
    },
    {
      dataField: 'changedAt',
      sort: true,
      text: <Trans>Date</Trans>,
      formatter: dayFormatter,
    },
    {
      dataField: 'status',
      filter: (defaultAttrs) => (
        <>
          {statuses ? (
            <TableInFilter
              {...defaultAttrs}
              filter='status__in'
              options={getStatusOptions()}
              direction='down'
            />
          ) : null}
        </>
      ),
      text: <Trans>Status</Trans>,
      formatter: (cell) => <SnapshotProposalStatus status={cell} />,
    },
  ];

  return (
    <Modal isOpen={isOpen} toggle={toggle} onClosed={onClosed} size='xl'>
      <ModalHeader className='d-flex justify-content-center'>
        <div className='fs-24'>
          <span className='mr-2'>{job.title}</span>
          <span className='fs-20 text-muted'>
            <DatePeriod params={params} />
          </span>
        </div>
      </ModalHeader>
      <ModalBody>
        <TableHeader
          title={<Trans>Candidates</Trans>}
          rightSide={
            <SelectInput
              options={getSnapshotOptions()}
              onSelect={setOperationId}
              value={operationId}
            />
          }
        />
        <SwaggerTable
          primaryLink={(s) => `/job/${job.id}/proposal/${s.proposal}/`}
          primaryLinkNewTab
          columns={columns}
          state={tableData}
          defaultSort='-changedAt'
          setState={setTableData}
          fetchFn={fetchTableData}
          params={requestParams}
          paginationKey='proposalsSnapshotShowPer'
        />
        <ShowAuthenticated groups={TALENT_ASSOCIATES}>
          <HiddenProposals params={requestParams} operationId={operationId} />
        </ShowAuthenticated>
      </ModalBody>
    </Modal>
  );
}

SnapshotTableModal.propTypes = {
  params: PropTypes.shape({
    granularity: PropTypes.oneOf(['day', 'month', 'week']),
    date_start: PropTypes.string,
    date_end: PropTypes.string,
  }).isRequired,
  isOpen: PropTypes.bool.isRequired,
  onClosed: PropTypes.func,
};

export default wrapper(SnapshotTableModal);
