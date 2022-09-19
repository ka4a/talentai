import React, { memo } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import Typography from '../Typography';

import styles from './Badge.module.scss';

let Badge = ({ text, variant, className }) => (
  <div className={classnames(className, styles[variant])}>
    <Typography variant='button'>{text}</Typography>
  </div>
);

Badge = memo(Badge);

Badge.propTypes = {
  text: PropTypes.string.isRequired,
  className: PropTypes.string,
  variant: PropTypes.oneOf(['warning', 'normal', 'neutral', 'success', 'danger']),
};

Badge.defaultProps = {
  className: '',
  variant: 'normal',
};

export default Badge;
