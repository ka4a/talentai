import React, { memo, useCallback, useMemo } from 'react';
import { useParams, useHistory } from 'react-router-dom';

import PropTypes from 'prop-types';
import { useLingui } from '@lingui/react';
import { t, Trans } from '@lingui/macro';

import {
  NameAndAvatarCell,
  DefaultPageContainer,
  Table,
  TableDetailsLayout,
  TableHeader,
  NotFoundTablePlaceholder,
} from '@components';
import { useStaffList } from '@swrAPI';
import { useTable } from '@hooks';
import TextCell from '@components/tableCells/TextCell';

import { useGroupToRoleMap } from './hooks';
import UserDetails from './components/UserDetails/UserDetails';

function UserViewPage({ basePath }) {
  const { i18n } = useLingui();
  const { userId } = useParams();
  const history = useHistory();

  const data = useTable({
    useGetData: useStaffList,
    storeKey: STORE_TABLE_KEY,
    paginationKey: 'staffShowPer',
  });

  const groupToRoleMap = useGroupToRoleMap(i18n);

  const handleRowClick = useCallback(
    (event, user) => {
      history.push(`${basePath}/${user.id}`);
    },
    [basePath, history]
  );

  const handleCloseDetails = useCallback(() => history.push(basePath), [
    basePath,
    history,
  ]);

  const columns = useMemo(
    () => [
      {
        sort: true,
        width: 502,
        text: i18n._(t`Name`),
        dataField: 'name',
        formatter: (_, { photo, firstName, lastName, id }) => (
          <NameAndAvatarCell
            avatarSrc={photo}
            name={`${firstName} ${lastName}`}
            tooltipId={`userNameTooltip${id}`}
          />
        ),
      },
      {
        sort: true,
        width: 281,
        text: i18n._(t`Role`),
        dataField: 'group',
        formatter: (group, _, { isActive }) => (
          <TextCell isActive={isActive}>{groupToRoleMap[group] ?? '-'}</TextCell>
        ),
      },
      {
        hideInSidebar: true,
        width: 270,
        text: i18n._(t`Email`),
        dataField: 'email',
        formatter: (email) => <TextCell>{email}</TextCell>,
      },
      {
        sort: true,
        hideInSidebar: true,
        width: 112,
        text: i18n._(t`Status`),
        dataField: 'isActive',
        formatter: (isUserActive) => (
          <TextCell>
            {isUserActive ? <Trans>Active</Trans> : <Trans>Inactive</Trans>}
          </TextCell>
        ),
      },
    ],
    [i18n, groupToRoleMap]
  );

  return (
    <DefaultPageContainer title={t`Users`}>
      <TableDetailsLayout
        isOpen={Boolean(userId)}
        onClose={handleCloseDetails}
        header={<TableHeader storeKey={STORE_TABLE_KEY} />}
        renderTable={({ areDetailsOpen, hideHeader }) => (
          <Table
            data={data}
            isOpenColumn={areDetailsOpen}
            hideHeader={hideHeader}
            columns={columns}
            storeKey={STORE_TABLE_KEY}
            onRowClick={handleRowClick}
            activeRowId={Number(userId)}
            noDataPlaceholder={<NotFoundTablePlaceholder title={t`No Users found`} />}
          />
        )}
        renderDetails={() => <UserDetails userId={userId} basePath={basePath} />}
      />
    </DefaultPageContainer>
  );
}

const STORE_TABLE_KEY = 'users';

UserViewPage.propTypes = {
  basePath: PropTypes.string.isRequired,
};

export default memo(UserViewPage);
