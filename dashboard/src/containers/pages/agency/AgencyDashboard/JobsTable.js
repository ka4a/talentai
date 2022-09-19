import React from 'react';

import { Trans } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import _ from 'lodash';
import PropTypes from 'prop-types';

import HumanizedDate from '@components/format/HumanizedDate';
import JobStatus from '@components/jobs/JobStatus';
import JobTitle from '@components/jobs/JobTitle';
import { AGENCY_ADMINISTRATORS, AGENCY_MANAGERS, JOB_STATUS_CHOICES } from '@constants';
import { translateChoices } from '@utils';

import ShowAuthenticated from '../../../../components/auth/ShowAuthenticated';
import SwaggerTable, {
  getTableState,
  makeFetchTableData,
  makeSetTableData,
  TABLE_KEY,
  TableHeader,
  TableInFilter,
  ToggleTableFilter,
} from '../../../../components/SwaggerTable';
import UsersTooltip from '../../../../components/UsersTooltip';

class JobsTable extends React.Component {
  state = {
    ...getTableState({
      params: {
        status__in: ['open', 'on_hold'],
        client__in: [],
        only_my_jobs: true,
        show_live_proposal_count: true,
      },
    }),
  };

  static propTypes = {
    clients: PropTypes.array.isRequired,
  };

  static defaultProps = {
    clients: [],
  };

  COLUMNS = [
    {
      dataField: 'title',
      text: <Trans>Job Title</Trans>,
      formatter: (cell, job) => <JobTitle job={job} link />,
    },
    {
      dataField: 'clientName',
      text: <Trans>Client</Trans>,
      filter: (defaultAttrs) => (
        <TableInFilter
          {...defaultAttrs}
          filter='client__in'
          options={_.map(this.props.clients, ({ id, name }) => ({
            label: name,
            value: id,
          }))}
        />
      ),
    },
    {
      dataField: 'haveAccessSince',
      text: <Trans>Job opened</Trans>,
      sort: true,
      formatter: (cell) => <HumanizedDate date={cell} />,
    },
    {
      dataField: 'talentAssociates',
      text: <Trans>Talent Associate</Trans>,
      formatter: (talentAssociates) => <UsersTooltip users={talentAssociates} />,
    },
    {
      dataField: 'managers',
      text: <Trans>Hiring Manager</Trans>,
      formatter: (managers) => <UsersTooltip users={managers} />,
    },
    {
      dataField: 'liveProposalsCount',
      text: <Trans>Candidates</Trans>,
      align: 'right',
      formatter: (cell) => <div>{cell}</div>,
    },
    {
      dataField: 'status',
      text: <Trans>Status</Trans>,
      formatter: (status) => <JobStatus status={status} />,
      filter: (defaultAttrs) => (
        <TableInFilter
          {...defaultAttrs}
          filter='status__in'
          options={translateChoices(this.props.i18n, JOB_STATUS_CHOICES)}
        />
      ),
    },
  ];

  getTableTitle = (state) => {
    return state.params.only_my_jobs ? <Trans>My Jobs</Trans> : <Trans>All Jobs</Trans>;
  };

  fetchTableData = makeFetchTableData('jobs_list').bind(this);
  setTableState = makeSetTableData().bind(this);
  getLink = (job) => `/job/${job.id}`;

  render() {
    return (
      <>
        <TableHeader
          title={this.getTableTitle}
          search
          state={this.state[TABLE_KEY]}
          setState={this.setTableState}
          leftSide={
            <ShowAuthenticated groups={[AGENCY_ADMINISTRATORS, AGENCY_MANAGERS]}>
              <ToggleTableFilter
                className='ml-3'
                filter='only_my_jobs'
                state={this.state[TABLE_KEY]}
                setState={this.setTableState}
                options={[
                  { label: <Trans>My Jobs</Trans>, value: true },
                  { label: <Trans>All Jobs</Trans>, value: false },
                ]}
              />
            </ShowAuthenticated>
          }
        />
        <SwaggerTable
          // to make sure change of client objects would trigger filter update
          watchClientOptions={this.props.clients}
          columns={this.COLUMNS}
          primaryLink={this.getLink}
          defaultSort='-haveAccessSince'
          fetchFn={this.fetchTableData}
          state={this.state[TABLE_KEY]}
          setState={this.setTableState}
          paginationKey='dashboardJobsShowPer'
        />
      </>
    );
  }
}

export default withI18n()(JobsTable);
