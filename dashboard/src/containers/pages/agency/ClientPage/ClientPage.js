import React from 'react';
import { Link } from 'react-router-dom';
import { BreadcrumbItem, Button, DropdownItem } from 'reactstrap';
import { MdChevronRight, MdMoreHoriz } from 'react-icons/md';

import _ from 'lodash';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';

import {
  Loading,
  DefaultPageContainer,
  ReqStatus,
  SwaggerTable,
  JobStatus,
  JobTitle,
  ShowMatchUserOrg,
  SimpleDropdown,
  ModalFormAgencyJobContract,
  ShowAuthenticated,
  LocaleOptionLabel,
  FeeModal,
} from '@components';
import { fetchLoadingWrapper, getDefaultReqState } from '@components/ReqStatus';
import {
  getTableState,
  makeFetchTableData,
  makeSetTableData,
  TABLE_KEY,
  TableHeader,
  TableInFilter,
} from '@components/SwaggerTable';
import { client } from '@client';
import { AGENCY_ADMINISTRATORS, AGENCY_MANAGERS, JOB_STATUS_CHOICES } from '@constants';

class ClientPage extends React.Component {
  constructor(props) {
    super(props);
    const locState = props.location.state;

    this.state = {
      ...getDefaultReqState(),
      ...getTableState({
        params: { status__in: ['open', 'on_hold'] },
      }),
      client: locState && locState.client ? locState.client : null,
      jobAgencyContractId: null,
      shouldPreviewJobAgencyContract: true,
      jobAgencyContractForFee: null,
    };
  }

  openFeeModal = (job) =>
    this.setState({
      jobAgencyContractForFee: job.agencyContracts[0],
    });

  closeFeeModal = () =>
    this.setState({
      jobAgencyContractForFee: null,
    });

  setIsOpenFeeModal = () => {
    if (this.state.jobAgencyContractForFee != null) this.closeFeeModal();
  };

  openContractModalForJob = (job, shouldPreviewJobAgencyContract = false) =>
    this.setState({
      jobAgencyContractId: job.agencyContracts[0].id,
      shouldPreviewJobAgencyContract,
    });
  closeContractModal = () =>
    this.setState({ jobAgencyContractId: null, shouldPreviewJobAgencyContract: true });
  allowEditing = (event) => {
    event.preventDefault();
    this.setState({ shouldPreviewJobAgencyContract: false });
  };

  COLUMNS = [
    {
      dataField: 'title',
      sort: true,
      text: <Trans>Job Title</Trans>,
      formatter: (cell, job) => <JobTitle job={job} link />,
    },
    {
      dataField: 'agencyContracts',
      text: <Trans>Contract type</Trans>,
      formatter: (contracts) =>
        contracts.length > 0 ? (
          <LocaleOptionLabel
            optionsKey='jobContractTypes'
            value={contracts[0].contractType}
          />
        ) : (
          '-'
        ),
    },
    {
      dataField: 'liveProposalsCount',
      text: <Trans>Candidates Submitted</Trans>,
      align: 'right',
    },
    {
      dataField: 'status',
      text: <Trans>Status</Trans>,
      formatter: (status) => <JobStatus status={status} />,
      filter: (defaultAttrs) => (
        <TableInFilter
          {...defaultAttrs}
          filter='status__in'
          options={_.map(JOB_STATUS_CHOICES, ({ name, value }) => ({
            label: this.props.i18n._(name),
            value,
          }))}
        />
      ),
    },
    {
      dataField: 'action',
      text: '',
      align: 'right',
      preventRowMouseEvents: true,
      formatter: (cell, job) =>
        job.agencyContracts[0].isFilledIn ? (
          <SimpleDropdown
            className='d-inline-block'
            buttonClassname='p-0'
            trigger={<MdMoreHoriz size='1.5em' />}
          >
            <DropdownItem
              tag={Link}
              onClick={() => this.openContractModalForJob(job, true)}
            >
              <Trans>See Contract</Trans>
            </DropdownItem>
            <DropdownItem tag={Link} to={`/job/${job.id}/analytics`}>
              <Trans>See Analytics</Trans>
            </DropdownItem>
            <DropdownItem onClick={() => this.openFeeModal(job)}>
              <Trans>Issue a Fee</Trans>
            </DropdownItem>
          </SimpleDropdown>
        ) : (
          <ShowAuthenticated groups={[AGENCY_MANAGERS, AGENCY_ADMINISTRATORS]}>
            <Button
              tag={Link}
              color='primary'
              onClick={() => this.openContractModalForJob(job)}
            >
              <Trans>Fill Contract</Trans>
            </Button>
          </ShowAuthenticated>
        ),
    },
  ];

  fetchData = fetchLoadingWrapper(() =>
    client
      .execute({
        operationId: 'clients_read',
        parameters: {
          id: this.props.match.params.clientId,
        },
      })
      .then((response) => {
        this.setState({ client: response.obj });
      })
  ).bind(this);

  fetchTableData = makeFetchTableData('jobs_list').bind(this);
  setTableState = makeSetTableData().bind(this);
  refreshTable = () => {
    this.fetchTableData().then(this.setTableState);
  };

  componentDidMount() {
    if (this.state.client === null) {
      this.fetchData();
    }
  }

  getLink = (job) => `/job/${job.id}`;

  render() {
    const {
      client,
      jobAgencyContractId,
      shouldPreviewJobAgencyContract,
      reqStatus,
      jobAgencyContractForFee,
    } = this.state;

    const { loading } = reqStatus;
    const error = reqStatus.errorObj;

    if (loading || error) {
      return <ReqStatus {...{ loading, error }} />;
    }

    const { url, params } = this.props.match;

    const { clientId } = params;

    return (
      <DefaultPageContainer
        title={client !== null ? client.name : this.props.i18n._(t`Loading...`)}
        colAttrs={{ xs: 12, lg: { offset: 1, size: 10 } }}
        breadcrumb={
          client !== null ? (
            <>
              <BreadcrumbItem>
                <Link to='/a/clients'>
                  <Trans>Clients</Trans>
                </Link>
                <MdChevronRight size='1.5em' />
              </BreadcrumbItem>
              <BreadcrumbItem active>{client.name}</BreadcrumbItem>
            </>
          ) : null
        }
      >
        <TableHeader
          title={client !== null ? client.name : <Loading />}
          rightSide={
            <ShowMatchUserOrg orgType='agency' orgId={_.get(client, 'ownerAgencyId')}>
              <Link to={`${url}/jobs/add`} className='align-top'>
                <Button className='ml-8' color='primary'>
                  <Trans>Create a job</Trans>
                </Button>
              </Link>
            </ShowMatchUserOrg>
          }
          search
          state={this.state[TABLE_KEY]}
          setState={this.setTableState}
        />
        <SwaggerTable
          columns={this.COLUMNS}
          primaryLink={this.getLink}
          defaultSort='title'
          params={{
            client: clientId,
            show_live_proposal_count: true,
          }}
          fetchFn={this.fetchTableData}
          state={this.state[TABLE_KEY]}
          setState={this.setTableState}
          paginationKey='clientJobsShowPer'
        />
        {jobAgencyContractId != null ? (
          <ModalFormAgencyJobContract
            isPreview={shouldPreviewJobAgencyContract}
            editingId={jobAgencyContractId}
            onClosed={this.closeContractModal}
            onSaved={this.refreshTable}
            onEdit={this.allowEditing}
          />
        ) : null}
        {jobAgencyContractForFee != null ? (
          <FeeModal
            isOpen={true}
            setIsOpen={this.setIsOpenFeeModal}
            onClosed={this.closeFeeModal}
            jobContract={jobAgencyContractForFee}
          />
        ) : null}
      </DefaultPageContainer>
    );
  }
}

export default withI18n()(ClientPage);
