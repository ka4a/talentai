import React from 'react';
import { Button } from 'reactstrap';
import { Link } from 'react-router-dom';
import { Container } from 'reactstrap';

import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';

import { TALENT_ASSOCIATES } from '@constants';
import { DefaultPageContainer } from '@components';

import ShowAuthenticated from '../../../../components/auth/ShowAuthenticated';
import SwaggerTable, {
  getTableState,
  makeFetchTableData,
  makeSetTableData,
  TABLE_KEY,
  TableHeader,
} from '../../../../components/SwaggerTable';

const paramsWorkingWith = { working_with: true };

class AgenciesPage extends React.Component {
  state = {
    ...getTableState(),
  };

  COLUMNS = [
    {
      dataField: 'name',
      sort: true,
      text: <Trans>Agency</Trans>,
      formatter: (cell, agency, link) => <Link to={link}>{cell}</Link>,
    },
    {
      dataField: 'proposalsCount',
      text: <Trans>Candidates Submitted</Trans>,
      align: 'right',
    },
  ];

  fetchTableData = makeFetchTableData('agencies_list').bind(this);
  setTableState = makeSetTableData().bind(this);
  getLink = (agency) => `/c/agency/${agency.id}`;

  render() {
    return (
      <DefaultPageContainer
        title={this.props.i18n._(t`Agencies`)}
        colAttrs={{ xs: 12, lg: { size: 12 } }}
      >
        <div className='with-header-offset'>
          <TableHeader
            title={<Trans>Currently Engaged Agencies</Trans>}
            search
            rightSide={
              <>
                <ShowAuthenticated groups={[TALENT_ASSOCIATES]}>
                  <Link to='/c/agencies/directory'>
                    <Button color='primary' className='ml-16'>
                      <Trans>Agency Directory</Trans>
                    </Button>
                  </Link>
                </ShowAuthenticated>
              </>
            }
            state={this.state[TABLE_KEY]}
            setState={this.setTableState}
          />
        </div>
        <Container className='with-table-offset'>
          <SwaggerTable
            columns={this.COLUMNS}
            primaryLink={this.getLink}
            defaultSort='name'
            params={paramsWorkingWith}
            fetchFn={this.fetchTableData}
            state={this.state[TABLE_KEY]}
            setState={this.setTableState}
            paginationKey='organizationsShowPer'
          />
        </Container>
      </DefaultPageContainer>
    );
  }
}

export default withI18n()(AgenciesPage);
