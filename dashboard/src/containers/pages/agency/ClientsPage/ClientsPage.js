import React from 'react';
import { Link } from 'react-router-dom';
import { Button, DropdownItem } from 'reactstrap';
import { MdMoreHoriz } from 'react-icons/md';

import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';

import SimpleDropdown from '@components/SimpleDropdown';
import { DefaultPageContainer } from '@components';

import SwaggerTable, {
  getTableState,
  makeFetchTableData,
  makeSetTableData,
  makeRefreshTableData,
  TABLE_KEY,
  TableHeader,
} from '../../../../components/SwaggerTable';
import CreateAgencyClientModal from './CreateAgencyClientModal';

class ClientsPage extends React.Component {
  state = {
    ...getTableState(),
  };

  COLUMNS = [
    {
      dataField: 'name',
      sort: true,
      text: <Trans>Name</Trans>,
      formatter: (cell, client, link) => <Link to={link}>{cell}</Link>,
    },
    {
      dataField: 'proposalsCount',
      text: <Trans>Candidates Submitted</Trans>,
      align: 'right',
    },
    {
      dataField: 'openJobsCount',
      text: <Trans>Active Jobs</Trans>,
      align: 'right',
    },
    {
      dataField: 'action',
      text: '',
      align: 'right',
      formatter: (cell, client) => (
        <SimpleDropdown
          className='d-inline-block'
          buttonClassname='p-0'
          trigger={<MdMoreHoriz size='1.5em' />}
        >
          <DropdownItem tag={Link} to={`/a/client/${client.id}/edit`}>
            <Trans>Edit</Trans>
          </DropdownItem>
        </SimpleDropdown>
      ),
    },
  ];

  fetchTableData = makeFetchTableData('clients_list').bind(this);
  setTableState = makeSetTableData().bind(this);
  refreshTableData = makeRefreshTableData(this.fetchTableData, this.setTableState).bind(
    this
  );

  getLink = (client) => ({ pathname: `/a/client/${client.id}`, state: { client } });

  render() {
    return (
      <DefaultPageContainer
        title={this.props.i18n._(t`Clients`)}
        colAttrs={{ xs: 12, md: { offset: 2, size: 8 } }}
      >
        <TableHeader
          title={this.props.i18n._(t`Clients`)}
          search
          state={this.state[TABLE_KEY]}
          setState={this.setTableState}
          rightSide={
            <CreateAgencyClientModal onClosed={this.refreshTableData}>
              <Button className='ml-3' color='primary'>
                <Trans>Create a Client</Trans>
              </Button>
            </CreateAgencyClientModal>
          }
        />
        <SwaggerTable
          columns={this.COLUMNS}
          primaryLink={this.getLink}
          fetchFn={this.fetchTableData}
          state={this.state[TABLE_KEY]}
          setState={this.setTableState}
          paginationKey='organizationsShowPer'
        />
      </DefaultPageContainer>
    );
  }
}

export default withI18n()(ClientsPage);
