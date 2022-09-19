import React, { memo } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import styles from './WindowBackground.module.scss';

const WindowBackground = ({ children, className }) => (
  <div className={classnames([styles.wrapper, className])}>{children}</div>
);

WindowBackground.propTypes = {
  className: PropTypes.string,
};

export default memo(WindowBackground);
