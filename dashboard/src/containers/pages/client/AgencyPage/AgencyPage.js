import React from 'react';

import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';

import { client } from '@client';
import {
  DefaultPageContainer,
  ReqStatus,
  HumanizedDate,
  Loading,
  SwaggerTable,
  ProposalStatus,
  ProposalStatusSelector,
  JobTitle,
} from '@components';
import { fetchLoadingWrapper, getDefaultReqState } from '@components/ReqStatus';
import {
  getTableState,
  makeFetchTableData,
  makeSetTableData,
  TABLE_KEY,
  TableHeader,
} from '@components/SwaggerTable';

const commonTriggerProps = {
  className: 'd-inline-block w-auto mr-4',
};

class AgencyPage extends React.Component {
  state = {
    ...getDefaultReqState(),
    ...getTableState(),
    agency: null,
    statusFilter: '',
  };

  getColumns = () => [
    {
      dataField: 'job',
      text: <Trans>Job</Trans>,
      formatter: (job, proposal) => (
        <JobTitle job={job} proposalId={proposal.id} link />
      ),
    },
    {
      dataField: 'candidate',
      text: <Trans>Candidate</Trans>,
      formatter: (candidate) => <span>{candidate.name}</span>,
    },
    {
      dataField: 'createdAt',
      text: <Trans>Created</Trans>,
      formatter: (cell) => <HumanizedDate date={cell} />,
    },
    {
      dataField: 'status',
      text: <Trans>Status</Trans>,
      formatter: (status) => <ProposalStatus status={status} />,
    },
  ];

  fetchTableData = makeFetchTableData('proposals_list').bind(this);
  setTableState = makeSetTableData().bind(this);

  fetchData = fetchLoadingWrapper(() => [
    client
      .execute({
        operationId: 'agencies_read',
        parameters: {
          id: this.props.match.params.agencyId,
        },
      })
      .then((response) => {
        this.setState({ agency: response.obj });
      }),
  ]).bind(this);

  componentDidMount() {
    this.fetchData();
  }

  onStatusFilterSelect = (statusFilter) => {
    this.setState({ statusFilter });
  };

  getLink = (proposal) => `/job/${proposal.job.id}/proposal/${proposal.id}`;

  render() {
    const {
      agency,
      statusFilter,
      reqStatus: { loading, errorObj },
    } = this.state;

    if (loading || errorObj) {
      return <ReqStatus {...{ loading, error: errorObj }} />;
    }

    return (
      <DefaultPageContainer
        title={agency !== null ? agency.name : this.props.i18n._(t`Loading...`)}
      >
        <TableHeader
          title={
            agency !== null ? (
              <Trans>
                <span>Proposals by {agency.name}:</span>
              </Trans>
            ) : (
              <Loading />
            )
          }
          rightSide={
            <>
              <ProposalStatusSelector
                noValueOption={this.props.i18n._(t`All Statuses`)}
                name='statusFilter'
                value={statusFilter}
                triggerComponentProps={commonTriggerProps}
                onSelect={this.onStatusFilterSelect}
              />
            </>
          }
          state={this.state[TABLE_KEY]}
          setState={this.setTableState}
        />
        <SwaggerTable
          columns={this.getColumns()}
          primaryLink={this.getLink}
          params={{
            candidate__agency: this.props.match.params.agencyId,
            status: statusFilter,
          }}
          defaultSort='-createdAt'
          fetchFn={this.fetchTableData}
          state={this.state[TABLE_KEY]}
          setState={this.setTableState}
          paginationKey='agencyProposalsShowPer'
        />
      </DefaultPageContainer>
    );
  }
}

export default withI18n()(AgencyPage);
