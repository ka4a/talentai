import React, { memo } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import { Typography } from '@components';

import styles from './TextCell.module.scss';

function TextCell({ isActive, children }) {
  return (
    <Typography
      variant='caption'
      className={classnames(styles.root, {
        [styles.isActive]: isActive,
      })}
    >
      {children}
    </Typography>
  );
}

TextCell.propTypes = {
  isActive: PropTypes.bool,
};

export default memo(TextCell);
