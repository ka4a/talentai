import React from 'react';
import { Link } from 'react-router-dom';
import { HiOutlineArrowLeft } from 'react-icons/hi';

import { Typography } from '@components';

import styles from './BackNavButton.module.scss';

const BackNavButton = ({ link, linkText }) => {
  return (
    <Link to={link} className={styles.back}>
      <Typography variant='caption'>
        <HiOutlineArrowLeft />
        {linkText}
      </Typography>
    </Link>
  );
};

export default BackNavButton;
