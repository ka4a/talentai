import React, { memo } from 'react';
import { BiChevronDown } from 'react-icons/bi';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import { Typography } from '@components';

import styles from './StatusesDropdown.module.scss';

const StatusesDropdownTrigger = ({ value, isDisabled }) => (
  <div className={classnames([styles.trigger, { [styles.disabled]: isDisabled }])}>
    <Typography className={styles.label} variant='caption'>
      {value}
    </Typography>
    <BiChevronDown size={24} />
  </div>
);

StatusesDropdownTrigger.propTypes = {
  value: PropTypes.string.isRequired,
  isDisabled: PropTypes.bool.isRequired,
};

export default memo(StatusesDropdownTrigger);
