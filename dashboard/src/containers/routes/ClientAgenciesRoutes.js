import React, { memo } from 'react';
import { Switch, useRouteMatch } from 'react-router-dom';

import { AuthenticatedRoute } from '@components';
import { CLIENT_ADMINISTRATORS } from '@constants';

import { AgenciesPage, AgencyDirectoryPage } from '../pages';

const ClientAgenciesRoutes = () => {
  const { path } = useRouteMatch();

  return (
    <Switch>
      <AuthenticatedRoute
        path={path}
        component={AgenciesPage}
        groups={[CLIENT_ADMINISTRATORS]}
        exact
      />

      <AuthenticatedRoute
        path={`${path}/directory`}
        groups={[CLIENT_ADMINISTRATORS]}
        component={AgencyDirectoryPage}
      />
    </Switch>
  );
};

export default memo(ClientAgenciesRoutes);
