import React from 'react';
import { Redirect, Route } from 'react-router-dom';
import { useSelector } from 'react-redux';

import _ from 'lodash';

const AuthenticatedRoute = ({ groups = null, component: Component, ...rest }) => {
  const user = useSelector((state) => state.user);

  return (
    <Route
      {...rest}
      render={(props) => {
        if (!user.isAuthenticated) return <Redirect to='/login/' />;

        if (groups !== null && !_.intersection(user.groups, groups).length) {
          return <Redirect to='/' />;
        }

        return <Component {...props} user={user} />;
      }}
    />
  );
};

export default AuthenticatedRoute;
