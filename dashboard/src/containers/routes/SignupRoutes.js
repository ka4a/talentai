import React, { memo } from 'react';
import { useSelector } from 'react-redux';
import { Switch, useRouteMatch } from 'react-router-dom';

import { AnonymousRoute } from '@components';

import { SignUpPage } from '../pages';

const SignupRoutes = () => {
  const disableSignup = useSelector((state) => state.settings.localeData.disableSignup);

  const { path } = useRouteMatch();

  return (
    <Switch>
      {!disableSignup && <AnonymousRoute exact path={path} component={SignUpPage} />}

      <AnonymousRoute path={`${path}/invite/:token`} component={SignUpPage} />

      <AnonymousRoute path={`${path}/via/:viaJob`} component={SignUpPage} />
    </Switch>
  );
};

export default memo(SignupRoutes);
