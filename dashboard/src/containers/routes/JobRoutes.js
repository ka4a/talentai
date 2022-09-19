import React, { memo } from 'react';
import { Switch, useRouteMatch } from 'react-router-dom';

import { AuthenticatedRoute } from '@components';
import { AGENCY_GROUPS, CLIENT_ADMINISTRATORS } from '@constants';

import * as pages from '../pages';

const JobRoutes = () => {
  const { path } = useRouteMatch();

  return (
    <Switch>
      <AuthenticatedRoute
        exact
        path={[path, `${path}/:tabId(proposals|share)`]}
        component={pages.JobPage}
      />

      <AuthenticatedRoute
        key='job-edit'
        path={`${path}/edit`}
        component={pages.JobEditPage}
      />

      <AuthenticatedRoute
        path={`${path}/analytics`}
        groups={[CLIENT_ADMINISTRATORS, ...AGENCY_GROUPS]}
        component={pages.JobAnalyticsPage}
      />

      <AuthenticatedRoute
        path={`${path}/proposal/:proposalId`}
        component={pages.JobPage}
      />
    </Switch>
  );
};

export default memo(JobRoutes);
