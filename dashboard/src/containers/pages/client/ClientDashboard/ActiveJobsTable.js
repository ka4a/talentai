import React from 'react';
import { MdMoreHoriz } from 'react-icons/md';
import { DropdownItem } from 'reactstrap';
import { Link } from 'react-router-dom';
import { Container } from 'reactstrap';

import { Trans } from '@lingui/macro';

import SimpleDropdown from '@components/SimpleDropdown';
import FormattedSalary from '@components/format/FormattedSalary';
import HumanizedDate from '@components/format/HumanizedDate';
import JobTitle from '@components/jobs/JobTitle';
import { TALENT_ASSOCIATES } from '@constants';

import UsersTooltip from '../../../../components/UsersTooltip';
import SwaggerTable, {
  getTableState,
  makeFetchTableData,
  makeSetTableData,
  TABLE_KEY,
  TableHeader,
} from '../../../../components/SwaggerTable';
import ProposalsPipeline from '../../../../components/jobs/ProposalsPipeline';
import ShowAuthenticated from '../../../../components/auth/ShowAuthenticated';

export default class ActiveJobsTable extends React.Component {
  state = {
    ...getTableState({
      params: {
        status__in: 'open',
        show_pipeline: 'true',
      },
    }),
  };

  COLUMNS = [
    {
      dataField: 'title',
      sort: true,
      text: <Trans>Job Title</Trans>,
      formatter: (cell, job) => <JobTitle job={job} link />,
    },
    {
      dataField: 'publishedAt',
      sort: true,
      text: <Trans>Date Published</Trans>,
      formatter: (publishedAt, job) =>
        job.published ? <HumanizedDate date={publishedAt} /> : 'Draft',
    },
    {
      dataField: 'managers',
      text: <Trans>Hiring Manager</Trans>,
      formatter: (managers) => <UsersTooltip users={managers} />,
    },
    {
      dataField: 'salary',
      text: <Trans>Salary</Trans>,
      formatter: (cell, job) => <FormattedSalary job={job} hidePerName={true} />,
    },
    {
      dataField: 'proposalsPipeline',
      formatter: (pipeline) => <ProposalsPipeline pipeline={pipeline} />,
    },
    {
      dataField: 'actions',
      text: '',
      align: 'right',
      classes: 'pl-0 pr-2',
      formatter: (cell, job) => (
        <ShowAuthenticated groups={[TALENT_ASSOCIATES]}>
          <SimpleDropdown
            className='d-inline-block'
            buttonClassname='p-0'
            trigger={<MdMoreHoriz size='1.5em' />}
          >
            <DropdownItem tag={Link} to={`/job/${job.id}/analytics`}>
              <Trans>See Analytics</Trans>
            </DropdownItem>
          </SimpleDropdown>
        </ShowAuthenticated>
      ),
    },
  ];

  fetchTableData = makeFetchTableData('jobs_list').bind(this);
  setTableState = makeSetTableData().bind(this);
  getLink = (job) => `/job/${job.id}`;

  render() {
    return (
      <>
        <div className='with-header-offset'>
          <TableHeader
            title={<Trans>Active Jobs</Trans>}
            search
            state={this.state[TABLE_KEY]}
            setState={this.setTableState}
          />
        </div>
        <Container className='with-table-offset'>
          <SwaggerTable
            columns={this.COLUMNS}
            primaryLink={this.getLink}
            defaultSort='-publishedAt'
            fetchFn={this.fetchTableData}
            state={this.state[TABLE_KEY]}
            setState={this.setTableState}
            paginationKey='dashboardJobsShowPer'
          />
        </Container>
      </>
    );
  }
}
