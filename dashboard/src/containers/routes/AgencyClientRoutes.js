import React, { memo } from 'react';
import { Switch, useRouteMatch } from 'react-router-dom';

import { AuthenticatedRoute } from '@components';
import { AGENCY_GROUPS } from '@constants';

import * as pages from '../pages';

const AgencyClientRoutes = () => {
  const { path } = useRouteMatch();

  return (
    <Switch>
      <AuthenticatedRoute
        path={path}
        component={pages.ClientPage}
        groups={AGENCY_GROUPS}
        exact
      />

      <AuthenticatedRoute
        key='job-add' // forces component recreation on redirect to edit page
        path={`${path}/jobs/add`}
        groups={AGENCY_GROUPS}
        component={pages.JobEditPage}
      />

      <AuthenticatedRoute
        path={`${path}/edit`}
        groups={AGENCY_GROUPS}
        component={pages.AgencyClientEditPage}
      />
    </Switch>
  );
};

export default memo(AgencyClientRoutes);
