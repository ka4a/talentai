import React, { useEffect } from 'react';
import { Redirect } from 'react-router';

import PropTypes from 'prop-types';

import { ZendeskError, useReportError } from '@utils';

function ZendeskLogoutRoute(props) {
  const { search } = props.location;

  const reportError = useReportError();

  useEffect(() => {
    const params = new URLSearchParams(search);
    if (params.get('kind') === 'error') {
      reportError(new ZendeskError(params.get('message')));
    }
  }, [search, reportError]);
  return <Redirect to='/' />;
}

ZendeskLogoutRoute.propTypes = {
  location: PropTypes.shape({
    search: PropTypes.string,
  }).isRequired,
};

export default ZendeskLogoutRoute;
