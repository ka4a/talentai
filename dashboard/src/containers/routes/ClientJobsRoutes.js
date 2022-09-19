import React, { memo } from 'react';
import { Switch, useRouteMatch } from 'react-router-dom';

import { AuthenticatedRoute } from '@components';
import {
  CLIENT_ADMINISTRATORS,
  CLIENT_GROUPS,
  CLIENT_INTERNAL_RECRUITERS,
} from '@constants';

import { JobsPage, JobEditPage } from '../pages';

const ClientJobsRoutes = () => {
  const { path } = useRouteMatch();

  return (
    <Switch>
      <AuthenticatedRoute
        path={path}
        component={JobsPage}
        groups={CLIENT_GROUPS}
        exact
      />

      <AuthenticatedRoute
        key='job-add' // forces component recreation on redirect to edit page
        path={`${path}/add`}
        groups={[CLIENT_ADMINISTRATORS, CLIENT_INTERNAL_RECRUITERS]}
        component={JobEditPage}
      />
    </Switch>
  );
};

export default memo(ClientJobsRoutes);
