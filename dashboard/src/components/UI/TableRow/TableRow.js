import React, { memo } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import styles from './TableRow.module.scss';

const TableRow = ({ isActive, onClick, children, className }) => (
  <div
    onClick={onClick}
    className={classnames([styles.wrapper, { [styles.active]: isActive }, className])}
  >
    {children}
  </div>
);

TableRow.propTypes = {
  isActive: PropTypes.bool.isRequired,
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  onClick: PropTypes.func,
};

TableRow.defaultProps = {
  onClick() {},
  className: '',
};

export default memo(TableRow);
