import React from 'react';

import { Typography } from '@components';

import searchIcon from '../../assets/images/icons/no-results-found.svg';

import styles from './NoData.module.scss';

const NoData = ({ message }) => {
  return (
    <div className={styles.root}>
      <img src={searchIcon} width={213} height={186} alt='search' />
      <Typography variant='h2'>{message}</Typography>
    </div>
  );
};

export default NoData;
