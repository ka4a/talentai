import React from 'react';
import { Route, Switch } from 'react-router';

import PropTypes from 'prop-types';

import { UserViewPage, UserEditPage } from '../pages/users';

function UserRoutes({ match }) {
  const { path } = match;
  return (
    <Switch>
      <Route exact path={`${path}/:userId/edit`} component={UserEditPage} />
      <Route exact path={[path, `${path}/:userId`]}>
        <UserViewPage basePath={path} />
      </Route>
    </Switch>
  );
}

UserRoutes.propTypes = {
  match: PropTypes.shape({
    path: PropTypes.string,
  }),
};

export default UserRoutes;
