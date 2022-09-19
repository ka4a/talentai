import React, { memo } from 'react';
import { Switch, useRouteMatch } from 'react-router-dom';

import { AuthenticatedRoute } from '@components';

import { PersonalSettings, CompanySettings } from '../pages';

const SettingsRoutes = () => {
  const { path } = useRouteMatch();

  return (
    <Switch>
      <AuthenticatedRoute path={`${path}/personal`} component={PersonalSettings} />
      <AuthenticatedRoute path={`${path}/company`} component={CompanySettings} />
    </Switch>
  );
};

SettingsRoutes.propTypes = {};

export default memo(SettingsRoutes);
