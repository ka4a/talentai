import React, { memo } from 'react';
import {
  TiArrowSortedDown as ArrowDown,
  TiArrowSortedUp as ArrowUp,
} from 'react-icons/ti';

import classnames from 'classnames';
import PropTypes from 'prop-types';

import styles from './CollapseArrowButton.module.scss';

const CollapseArrowButton = ({ isOpen, isDisabled, toggle, className }) => (
  <button
    onClick={toggle}
    className={classnames([
      styles.button,
      { [styles.disabled]: isDisabled },
      className,
    ])}
  >
    {isOpen && !isDisabled ? <ArrowUp /> : <ArrowDown />}
  </button>
);

CollapseArrowButton.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  className: PropTypes.string,
  isDisabled: PropTypes.bool,
  toggle: PropTypes.func,
};

CollapseArrowButton.defaultProps = {
  isDisabled: false,
  className: '',
  toggle() {},
};

export default memo(CollapseArrowButton);
