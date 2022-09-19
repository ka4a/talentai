import React, { memo } from 'react';
import { Switch, useRouteMatch } from 'react-router-dom';

import { AuthenticatedRoute } from '@components';
import { AGENCY_GROUPS } from '@constants';

import * as pages from '../pages';

const AgencyApprovalsRoutes = () => {
  const { path } = useRouteMatch();

  return (
    <Switch>
      <AuthenticatedRoute
        path={`${path}/fees`}
        component={pages.ApprovalsPage}
        groups={AGENCY_GROUPS}
        exact
      />

      <AuthenticatedRoute
        path={`${path}/fees/:feeId`}
        component={pages.ApprovalsPage}
        groups={AGENCY_GROUPS}
      />

      <AuthenticatedRoute
        path={`${path}/placements`}
        component={pages.ApprovalsPage}
        groups={AGENCY_GROUPS}
        exact
      />

      <AuthenticatedRoute
        path={`${path}/placements/:feeId`}
        component={pages.ApprovalsPage}
        groups={AGENCY_GROUPS}
      />

      <AuthenticatedRoute
        path={`${path}/proposals`}
        component={pages.ApprovalsPage}
        groups={AGENCY_GROUPS}
      />
    </Switch>
  );
};

export default memo(AgencyApprovalsRoutes);
