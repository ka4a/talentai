import React from 'react';
import { Route } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { withRouter } from 'react-router';

const PublicRoute = ({ component: Component, ...rest }) => {
  const user = useSelector((state) => state.user);

  return (
    <Route
      {...rest}
      render={(props) => <Component {...props} user={user} isPublic />}
    />
  );
};

export default withRouter(PublicRoute);
