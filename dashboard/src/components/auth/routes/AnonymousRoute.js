import React from 'react';
import { withRouter } from 'react-router';
import { useSelector } from 'react-redux';
import { Redirect, Route } from 'react-router-dom';

const AnonymousRoute = (props) => {
  const { component: Component, to_if_authenticated = '/', ...rest } = props;

  const user = useSelector((state) => state.user);

  return (
    <Route
      {...rest}
      render={(props) =>
        user.isAuthenticated ? (
          <Redirect to={to_if_authenticated} />
        ) : (
          <Component {...props} />
        )
      }
    />
  );
};

export default withRouter(AnonymousRoute);
