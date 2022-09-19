import React from 'react';
import { Link } from 'react-router-dom';
import { connect } from 'react-redux';

import _ from 'lodash';
import { withI18n } from '@lingui/react';
import { Trans } from '@lingui/macro';

import HumanizedDate from '@components/format/HumanizedDate';

import SwaggerTable, {
  getTableState,
  makeFetchTableData,
  makeSetTableData,
  TABLE_KEY,
  TableHeader,
  TableInFilter,
} from '../../../../components/SwaggerTable';
import ProposalStatus from '../../../../components/ProposalStatus';
import Statistics from './Statistics';

const mapStateToProps = (state) => ({
  proposalShortlistStatuses: state.settings.localeData.proposalShortlistStatuses,
});

const DEFAULT_PROPOSAL_STATUS_GROUPS = [
  'new',
  'proceeding',
  'offer_accepted',
  'interviewing',
  'offer',
  'approved',
];

const getDefaultProposalOptions = (options) => {
  const defaultOptions = _.filter(options, (option) =>
    _.includes(DEFAULT_PROPOSAL_STATUS_GROUPS, option.group)
  );

  return _.map(defaultOptions, (option) => option.id);
};

class ProposalsTable extends React.Component {
  constructor(props) {
    super(props);

    const { proposalShortlistStatuses } = props;

    this.state = {
      ...getTableState({
        params: {
          status__in: getDefaultProposalOptions(proposalShortlistStatuses),
          stage: 'shortlist',
        },
      }),
    };
  }

  getColumns = (additionalColumns) => {
    return [
      {
        dataField: 'candidate.name',
        text: <Trans>Candidate Name</Trans>,
        formatter: (cell, proposal, link) => <Link to={link}>{cell}</Link>,
      },
      {
        dataField: 'job.title',
        text: <Trans>Job Title</Trans>,
        classes: 'text-dark',
      },
      {
        dataField: 'createdAt',
        sort: true,
        text: <Trans>Date Submitted</Trans>,
        formatter: (cell) => <HumanizedDate date={cell} />,
      },
      {
        dataField: 'lastActivityAt',
        text: <Trans>Last activity</Trans>,
        formatter: (cell) => <HumanizedDate date={cell} />,
      },
      ...additionalColumns,
      {
        dataField: 'status',
        text: <Trans>Status</Trans>,
        formatter: (status) => <ProposalStatus status={status} />,
        filter: (defaultAttrs) => (
          <>
            {this.props.proposalShortlistStatuses ? (
              <TableInFilter
                {...defaultAttrs}
                filter='status__in'
                options={_.map(this.props.proposalShortlistStatuses, (s) => ({
                  value: s.id,
                  label: s.status,
                }))}
              />
            ) : null}
          </>
        ),
      },
    ];
  };

  TA_COLUMNS = [
    {
      dataField: 'source.name',
      text: <Trans>Source</Trans>,
      classes: 'text-dark',
    },
  ];

  fetchTableData = makeFetchTableData('proposals_list').bind(this);
  setTableState = makeSetTableData().bind(this);
  getLink = (proposal) => `/job/${proposal.job.id}/proposal/${proposal.id}`;

  render() {
    const { isTalentAssociate } = this.props;

    return (
      <>
        <TableHeader
          title={<Trans>Submitted Candidates</Trans>}
          search
          state={this.state[TABLE_KEY]}
          setState={this.setTableState}
        />
        <div className='my-16'>
          <Statistics />
        </div>
        <SwaggerTable
          columns={this.getColumns(isTalentAssociate ? this.TA_COLUMNS : [])}
          primaryLink={this.getLink}
          defaultSort='-createdAt'
          fetchFn={this.fetchTableData}
          state={this.state[TABLE_KEY]}
          setState={this.setTableState}
          paginationKey='dashboardProposalsShowPer'
        />
      </>
    );
  }
}

export default connect(mapStateToProps)(withI18n()(ProposalsTable));
