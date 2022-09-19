import React, { useCallback, useState } from 'react';

import classNames from 'classnames';
import PropTypes from 'prop-types';

import styles from './StuffedLabeledInput.module.scss';

// Input that allows to put stuff on the left and on the right inside of input
function StuffedLabeledInput(props) {
  const {
    onChange,
    onBlur,
    required,
    value,
    label,
    type,
    beforeInput,
    afterInput,
    isDisabled,
    wrapperClassName,
    ...rest
  } = props;

  const [isFocused, setIsFocused] = useState(false);
  const handleFocus = useCallback(() => setIsFocused(true), []);
  const handleBlur = useCallback(
    (event) => {
      setIsFocused(false);
      onBlur?.(event);
    },
    [onBlur]
  );

  return (
    <label
      className={classNames(styles.root, wrapperClassName, {
        [styles.disabled]: isDisabled,
        [styles.focused]: isFocused,
      })}
    >
      <div className={styles.label}>
        {label}
        {required && <span className={styles.required}>*</span>}
      </div>
      {beforeInput}
      <input
        onFocus={handleFocus}
        onBlur={handleBlur}
        onChange={onChange}
        value={value}
        type={type}
        disabled={isDisabled}
        className={styles.input}
        {...rest}
      />
      {afterInput}
    </label>
  );
}

StuffedLabeledInput.propTypes = {
  onChange: PropTypes.func,
  onBlur: PropTypes.func,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  label: PropTypes.string,
  isDisabled: PropTypes.bool,
  placeholder: PropTypes.string,
  required: PropTypes.bool,
  isError: PropTypes.bool,
  type: PropTypes.string,
  beforeInput: PropTypes.node,
  afterInput: PropTypes.node,
};

export default StuffedLabeledInput;
