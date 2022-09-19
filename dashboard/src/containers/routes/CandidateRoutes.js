import React, { memo } from 'react';
import { Switch, useRouteMatch } from 'react-router-dom';

import { AuthenticatedRoute } from '@components';

import { CandidateEditPage, CandidatePreviewPage } from '../pages';

const CandidateRoutes = () => {
  const { path } = useRouteMatch();

  return (
    <Switch>
      <AuthenticatedRoute path={`${path}/edit`} component={CandidateEditPage} />
      <AuthenticatedRoute path={`${path}/preview`} component={CandidatePreviewPage} />
    </Switch>
  );
};

export default memo(CandidateRoutes);
