import React from 'react';
import { MdUnfoldMore } from 'react-icons/md';

import PropTypes from 'prop-types';

import Typography from '../UI/Typography';

import styles from './SelectInput.module.scss';

function TableTrigger({ value }) {
  return (
    <div className={styles.tableButton}>
      <Typography variant='caption'>{value}</Typography>
      <MdUnfoldMore className={styles.icon} />
    </div>
  );
}

TableTrigger.propTypes = {
  value: PropTypes.string,
};
TableTrigger.defaultProps = {
  value: '',
};

export default TableTrigger;
