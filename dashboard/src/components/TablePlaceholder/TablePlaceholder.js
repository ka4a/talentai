import React from 'react';

import PropTypes from 'prop-types';

import { Typography } from '@components';

import styles from './TablePlaceholder.module.scss';

function TablePlaceholder({ icon, title, children }) {
  return (
    <div className={styles.root}>
      <div className={styles.icon}>{icon}</div>
      <Typography variant='h2' className={styles.title}>
        {title}
      </Typography>
      <div className={styles.description}>{children}</div>
    </div>
  );
}

TablePlaceholder.propTypes = {
  icon: PropTypes.node.isRequired,
  title: PropTypes.node.isRequired,
};

export default TablePlaceholder;
