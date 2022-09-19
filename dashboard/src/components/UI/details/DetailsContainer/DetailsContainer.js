import React from 'react';

import PropTypes from 'prop-types';

import { Loading, ReqStatus } from '@components';

import styles from './DetailsContainer.module.scss';

function DetailsContainer({ isLoading, data, error, renderDetails }) {
  let content;
  if (!data || error) {
    content = <ReqStatus error={error} loading={isLoading} />;
  } else if (isLoading) {
    content = <Loading />;
  } else {
    content = renderDetails();
  }
  return <div className={styles.root}>{content}</div>;
}

DetailsContainer.propTypes = {
  isLoading: PropTypes.bool,
  error: PropTypes.object,
  renderDetails: PropTypes.func.isRequired,
};

export default DetailsContainer;
