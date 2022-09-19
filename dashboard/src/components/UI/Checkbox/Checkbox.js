import React, { memo } from 'react';

import classnames from 'classnames';
import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import styles from './Checkbox.module.scss';

const Checkbox = ({ label, checked, className, isDisabled, ...props }) => (
  <label className={classnames([styles.wrapper, className])}>
    <input
      className={styles.hiddenCheckbox}
      type='checkbox'
      checked={checked}
      disabled={isDisabled}
      {...props}
    />

    <div className={classnames([styles.styledCheckbox, { [styles.checked]: checked }])}>
      {checked && (
        <svg
          width='18'
          height='20'
          viewBox='0 0 12 18'
          fill='none'
          xmlns='http://www.w3.org/2000/svg'
        >
          <path
            d='M1 4L4 7L10 1'
            stroke='white'
            strokeWidth='2'
            strokeMiterlimit='10'
            strokeLinecap='round'
            strokeLinejoin='round'
          />
        </svg>
      )}
    </div>

    {label && (
      <span className={styles.label}>
        <Trans>{label}</Trans>
      </span>
    )}
  </label>
);

Checkbox.propTypes = {
  checked: PropTypes.bool.isRequired,
  className: PropTypes.string,
  isDisabled: PropTypes.bool,
  label: PropTypes.string,
};

Checkbox.defaultProps = {
  className: '',
  isDisabled: false,
  label: null,
};

export default memo(Checkbox);
