import React from 'react';
import { BreadcrumbItem, Button, Col, Row } from 'reactstrap';
import { Link } from 'react-router-dom';
import { MdChevronRight } from 'react-icons/md';

import _ from 'lodash';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';

import { client } from '@client';
import { DefaultPageContainer, SwaggerTable, SeeMore } from '@components';
import { fetchErrorHandler } from '@utils';
import {
  getTableState,
  makeFetchTableData,
  makeRefreshTableData,
  makeSetTableData,
  TABLE_KEY,
} from '@components/SwaggerTable';
import { fetchLoadingWrapper } from '@components/ReqStatus';

import { AgencyDirectoryFilters } from './AgencyDirectoryFilters';
import AgencyDirectoryTableHeader from './AgencyDirectoryTableHeader';
import AgencyItem from './AgencyItem';

const isAgencyInvited = (agency) => agency.contract;

const ALL_INVITED_BUTTON_SETTINGS = {
  [true]: {
    // all invited
    color: 'nobg-secondary',
    text: <Trans>Invited</Trans>,
    disabled: true,
  },
  [false]: {
    // not all invited
    color: 'nobg-primary',
    text: <Trans>Invite All</Trans>,
    disabled: false,
  },
};

class AgencyDirectoryPage extends React.Component {
  state = {
    ...getTableState(),
    categoryGroups: null,
    categories: null,
    categoryFilter: [],
    functionFocus: null,
    functionFocusFilter: [],
  };

  onInviteAllAgencies = async () => {
    const { tableData } = this.state;
    await client.execute({
      operationId: 'contracts_invite_multiple_agencies',
      parameters: {
        data: {
          ...tableData.params,
          function_focus__in:
            tableData.params.function_focus__in &&
            tableData.params.function_focus__in.join(),
          categories_filter:
            tableData.params.categories_filter &&
            tableData.params.categories_filter.join(),
        },
      },
    });
    await this.refreshTableData();
  };

  renderAgencyColumnHeader = () => {
    const buttonSettings =
      ALL_INVITED_BUTTON_SETTINGS[
        _.every(this.state.tableData.data.results, isAgencyInvited)
      ];
    return (
      <div className='d-flex justify-content-between align-items-center'>
        <span>
          <Trans>Agency</Trans>
        </span>
        {this.state.tableData.data.results.length !== 0 && (
          <Button
            disabled={buttonSettings.disabled}
            color={buttonSettings.color}
            onClick={this.onInviteAllAgencies}
          >
            {buttonSettings.text}
          </Button>
        )}
      </div>
    );
  };

  COLUMNS = [
    {
      dataField: 'name',
      classes: 'text-dark',
      headerFormatter: this.renderAgencyColumnHeader,
      text: <Trans>Agency</Trans>,
      formatter: (name, agency) => (
        <SeeMore maxHeight={200}>
          <AgencyItem
            agency={agency}
            categoryGroups={this.state.categoryGroups}
            categories={this.state.categories}
            functionFocus={this.state.functionFocus}
            toggleFavorite={this.toggleFavorite}
            onInvite={this.inviteAgency}
            onEndContract={this.removeContract}
          />
        </SeeMore>
      ),
    },
  ];

  fetchData = fetchLoadingWrapper(() => [
    client
      .execute({
        operationId: 'agency_category_list',
      })
      .then((response) => {
        const categories = response.obj;
        const categoryGroups = _.sortBy(_.uniq(_.map(categories, 'group')));

        this.setState({ categories, categoryGroups });
      }),
    client
      .execute({
        operationId: 'function_list',
      })
      .then((response) => {
        this.setState({ functionFocus: response.obj });
      }),
  ]).bind(this);

  fetchTableData = makeFetchTableData('agencies_list').bind(this);
  setTableState = makeSetTableData().bind(this);
  refreshTableData = makeRefreshTableData(this.fetchTableData, this.setTableState);

  toggleFavorite = (agency) => {
    client
      .execute(
        agency.contract
          ? {
              operationId: 'contracts_delete',
              parameters: { id: agency.contract.id },
            }
          : {
              operationId: 'contracts_create',
              parameters: { data: { agency: agency.id } },
            }
      )
      .then(() => {
        this.refreshTableData();
      })
      .catch(fetchErrorHandler);
  };

  createContract = (agency) => {
    return client.execute({
      operationId: 'contracts_create',
      parameters: { data: { agency: agency.id } },
    });
  };

  removeContract = async (agency) => {
    if (!agency || !agency.contract || agency.contract.id == null) return;
    await client.execute({
      operationId: 'contracts_delete',
      parameters: { id: agency.contract.id },
    });
    await this.refreshTableData();
  };

  setStartUpdatingContract = () => {
    this.setState({
      isUpdatingContract: true,
    });
  };

  setStopUpdatingContract = () => {
    this.setState({
      isUpdatingContract: false,
    });
  };

  componentDidMount() {
    this.fetchData();
  }

  inviteAgency = async (agency) => {
    if (agency.contract != null) return;
    if (this.state.isUpdatingContract) return;
    this.setStartUpdatingContract();
    try {
      await this.createContract(agency);
      await this.refreshTableData();
    } finally {
      this.setStopUpdatingContract();
    }
  };

  onFilterToggle = (categoryId) => {
    this.setState((state) => ({
      categoryFilter: _.xor(state.categoryFilter, [categoryId]),
    }));
  };

  onFunctionFocusFilterToggle = (functionFocusId) => {
    this.setState((state) => ({
      functionFocusFilter: _.xor(state.functionFocusFilter, [functionFocusId]),
    }));
  };

  onFilterClear = () => {
    this.setState({ categoryFilter: [], functionFocusFilter: [] });
  };

  render() {
    const {
      categories,
      categoryGroups,
      categoryFilter,
      functionFocus,
      functionFocusFilter,
    } = this.state;

    return (
      <DefaultPageContainer
        title={this.props.i18n._(t`Agency Directory`)}
        breadcrumb={
          <>
            <BreadcrumbItem>
              <Link to='/c/agencies'>
                <Trans>Currently Engaged Agencies</Trans>
              </Link>
              <MdChevronRight size='1.5em' />
            </BreadcrumbItem>
            <BreadcrumbItem active>
              <Trans>Agency Directory</Trans>
            </BreadcrumbItem>
          </>
        }
      >
        <Row>
          <Col>
            <h2>
              <Trans>Agency Directory</Trans>
            </h2>
          </Col>
        </Row>
        <Row className='mb-24'>
          <Col>
            <span className='fs-18 text-muted'>
              <Trans>
                Search vetted, quality firms and recruiting agencies in Japan.
              </Trans>
            </span>
          </Col>
        </Row>

        <Row>
          <Col xs={12} md={4}>
            <AgencyDirectoryFilters
              loading={categoryGroups === null}
              categoryGroups={categoryGroups}
              categories={categories}
              categoryFilter={categoryFilter}
              onToggle={this.onFilterToggle}
              functionFocus={functionFocus}
              functionFocusFilter={functionFocusFilter}
              onFunctionFocusToggle={this.onFunctionFocusFilterToggle}
              onClear={this.onFilterClear}
            />
          </Col>
          <Col xs={12} md={8}>
            <AgencyDirectoryTableHeader
              state={this.state[TABLE_KEY]}
              setState={this.setTableState}
            />
            <SwaggerTable
              columns={this.COLUMNS}
              defaultSort='-contract_ann,name'
              fetchFn={this.fetchTableData}
              params={{
                categories_filter: categoryFilter.length ? categoryFilter : null,
                function_focus__in: functionFocusFilter.length
                  ? functionFocusFilter
                  : null,
              }}
              state={this.state[TABLE_KEY]}
              setState={this.setTableState}
              paginationKey='agencyDirectoryShowPer'
            />
          </Col>
        </Row>
      </DefaultPageContainer>
    );
  }
}

export default withI18n()(AgencyDirectoryPage);
