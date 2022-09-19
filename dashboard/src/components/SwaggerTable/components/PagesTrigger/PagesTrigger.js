import React, { memo } from 'react';
import { MdUnfoldMore } from 'react-icons/md';

import PropTypes from 'prop-types';

import Typography from '../../../UI/Typography';

import styles from './PagesTrigger.module.scss';

const PagesTrigger = ({ limit }) => (
  <div className={styles.trigger}>
    <Typography variant='caption'>{limit}</Typography>
    <MdUnfoldMore className={styles.icon} size={20} />
  </div>
);

PagesTrigger.propTypes = {
  limit: PropTypes.number.isRequired,
};

export default memo(PagesTrigger);
