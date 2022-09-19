import React, { memo } from 'react';

import PropTypes from 'prop-types';

import { Typography } from '@components';

import styles from './MissingInformation.module.scss';

// This is a content for Alert modal
const MissingInformation = ({ emptyFields }) => (
  <div>
    <Typography className={styles.description}>
      The following fields are empty:
    </Typography>

    <ul className={styles.list}>
      {emptyFields.map((field) => (
        <li key={field}>
          <Typography className={styles.field} variant='caption'>
            {field}
          </Typography>
        </li>
      ))}
    </ul>
  </div>
);

MissingInformation.propTypes = {
  emptyFields: PropTypes.arrayOf(PropTypes.string).isRequired,
};

export default memo(MissingInformation);
