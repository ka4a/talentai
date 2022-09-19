import React, { memo, useMemo, useCallback } from 'react';

import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import { DefaultPageContainer } from '@components';

import SwaggerTable, {
  TableHeader,
  useFetchTableData,
  useSwaggerTableState,
} from '../../../components/SwaggerTable';
import Invitation from './Invitation';
import { CONTRACT_STATUS } from '../client/AgencyDirectoryPage/constants';

const FILTER_PARAMS = {
  status__in: [
    CONTRACT_STATUS.PENDING,
    CONTRACT_STATUS.AGENCY_INVITED,
    CONTRACT_STATUS.REJECTED,
    CONTRACT_STATUS.EXPIRED,
  ],
};

function InvitationsPage(props) {
  const [tableData, setTableData] = useSwaggerTableState({
    params: FILTER_PARAMS,
  });
  const fetchTableData = useFetchTableData('contracts_list');
  const updateInvite = useCallback(() => setTableData({ initialized: false }), [
    setTableData,
  ]);

  const columns = useMemo(
    () => [
      {
        dataField: 'id',
        header: (
          <div className='d-flex justify-content-between align-items-center'>
            <span>
              <Trans>Invitations</Trans>
            </span>
          </div>
        ),
        formatter(id, contract) {
          return <Invitation key={id} updateInvite={updateInvite} {...contract} />;
        },
      },
    ],
    [updateInvite]
  );

  return (
    <DefaultPageContainer title={props.i18n._(t`Invitations`)}>
      <TableHeader
        title={props.i18n._(t`Invitations`)}
        state={tableData}
        setState={setTableData}
      />
      <SwaggerTable
        hideHeader
        operationId='contracts_list'
        fetchFn={fetchTableData}
        state={tableData}
        setState={setTableData}
        columns={columns}
      />
    </DefaultPageContainer>
  );
}

InvitationsPage.displayName = 'InvitationPage';
InvitationsPage.propTypes = {};
InvitationsPage.defaultProps = {};

export default memo(withI18n()(InvitationsPage));
