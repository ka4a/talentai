import React from 'react';
import { Link } from 'react-router-dom';

import _ from 'lodash';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import JobTitle from '@components/jobs/JobTitle';
import HumanizedDate from '@components/format/HumanizedDate';
import { PROPOSAL_STATUS_GROUP_CATEGORY_CHOICES } from '@constants';
import { translateChoices } from '@utils';

import SwaggerTable, {
  getTableState,
  makeFetchTableData,
  makeSetTableData,
  TABLE_KEY,
  TableHeader,
  TableInFilter,
} from '../../../../components/SwaggerTable';
import ProposalStatus from '../../../../components/ProposalStatus';
import BackendSearchSelectInput from '../../../../components/SelectInput/BackendSearchSelectInput';
import DealPipelineMetrics from './DealPipelineMetrics';
import FilterButton from './FilterButton';

const staffToOption = ({ id, firstName, lastName }) => ({
  value: id,
  label: `${firstName} ${lastName}`,
});

class CandidatesTable extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      ...getTableState({
        params: {
          status_group_category__in: ['new', 'proceeding'],
          client__in: [],
          stage: 'shortlist',
        },
      }),
      shortlistedBy: null,
    };
  }

  handleStaffSelect = (userId) => {
    this.setState({ shortlistedBy: userId });
  };

  static propTypes = {
    clients: PropTypes.array.isRequired,
  };

  static defaultProps = {
    clients: [],
  };

  COLUMNS = [
    {
      dataField: 'candidate',
      text: <Trans>Candidate Name</Trans>,
      formatter: this.getNameFormatter,
    },
    {
      dataField: 'job',
      preventRowMouseEvents: true,
      text: <Trans>Job title</Trans>,
      formatter: this.getJobFormatter,
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
      dataField: 'lastActivityAt',
      text: <Trans>Last Activity</Trans>,
      formatter: (date) => <HumanizedDate date={date} />,
    },
    {
      dataField: 'status',
      text: <Trans>Status</Trans>,
      formatter: (status, proposal) => {
        if (!proposal.onHold) {
          return <ProposalStatus status={status} />;
        }

        return (
          <Trans>
            On Hold
            <span>&nbsp;</span>
            <span className='text-muted'>({status.status})</span>
          </Trans>
        );
      },
      filter: (defaultAttrs) => (
        <TableInFilter
          {...defaultAttrs}
          filter='status_group_category__in'
          options={translateChoices(PROPOSAL_STATUS_GROUP_CATEGORY_CHOICES)}
        />
      ),
    },
  ];

  getNameFormatter(candidate, proposal, link) {
    if (proposal.onHold) {
      return candidate.name;
    }

    return <Link to={link}>{candidate.name}</Link>;
  }

  getJobFormatter(job, proposal) {
    if (proposal.onHold) {
      return job.title;
    }

    return <JobTitle job={job} link />;
  }

  fetchTableData = makeFetchTableData('proposals_list').bind(this);
  setTableState = makeSetTableData().bind(this);
  getLink = (proposal) => `/job/${proposal.job.id}/proposal/${proposal.id}`;

  render() {
    const { i18n } = this.props;
    const { shortlistedBy } = this.state;
    return (
      <div className='mt-24'>
        <TableHeader
          title={
            <div className='d-flex align-items-end'>
              <div>
                <Trans>Submitted Candidates</Trans>
              </div>
              <BackendSearchSelectInput
                TriggerComponent={FilterButton}
                operationId='staff_list'
                toOption={staffToOption}
                onSelect={this.handleStaffSelect}
                nullOption={i18n._(t`All Users`)}
              />
            </div>
          }
          search
          state={this.state[TABLE_KEY]}
          setState={this.setTableState}
        />
        <DealPipelineMetrics shortlistedBy={shortlistedBy} />
        <SwaggerTable
          columns={this.COLUMNS}
          primaryLink={this.getLink}
          defaultSort='-lastActivityAt'
          fetchFn={this.fetchTableData}
          state={this.state[TABLE_KEY]}
          setState={this.setTableState}
          paginationKey='dashboardProposalsShowPer'
        />
      </div>
    );
  }
}

export default withI18n()(CandidatesTable);
