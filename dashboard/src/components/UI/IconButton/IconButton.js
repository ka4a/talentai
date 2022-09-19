import React, { memo } from 'react';

import PropTypes from 'prop-types';

import styles from './IconButton.module.scss';

const IconButton = ({ onClick, children }) => (
  <div onClick={onClick} className={styles.button}>
    {children}
  </div>
);

IconButton.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func,
};

IconButton.defaultProps = {
  onClick() {},
};

export default memo(IconButton);
