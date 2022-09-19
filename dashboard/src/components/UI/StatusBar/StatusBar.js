import React, { memo } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import styles from './StatusBar.module.scss';

const StatusBar = ({ variant, className, text }) => {
  return <div className={classnames([styles[variant], className])}>{text}</div>;
};

StatusBar.propTypes = {
  text: PropTypes.node,
  variant: PropTypes.oneOf(['regular', 'success', 'danger', 'warning']).isRequired,
  className: PropTypes.string,
};

StatusBar.defaultProps = {
  text: '',
  className: '',
};

export default memo(StatusBar);
