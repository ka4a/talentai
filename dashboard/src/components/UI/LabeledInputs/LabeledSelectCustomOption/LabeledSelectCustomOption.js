import React, { memo } from 'react';
import Select from 'react-select';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import { Typography } from '@components';

import IconOption from './IconOption';
import ValueOption from './ValueOption';

import styles from '../LabeledSelect/LabeledSelect.module.scss';

function LabeledSelectCustomOption(props) {
  const {
    label,
    value,
    valueKey,
    options,
    onChange,
    isDisabled,
    placeholder,
    isError,
    required,
    ...rest
  } = props;

  const selectedValue = options.find((option) => option[valueKey] === value);

  return (
    <div className={classnames(styles.wrapper, { [styles.disabled]: isDisabled })}>
      <label className={styles.label}>
        <Typography variant='caption'>
          {label}
          {required && <span className={styles.required}>*</span>}
        </Typography>
      </label>

      <Select
        value={selectedValue}
        onChange={(option) => onChange(option[valueKey])}
        options={options}
        isDisabled={isDisabled}
        components={{ Option: IconOption, SingleValue: ValueOption }}
        placeholder={placeholder}
        className={classnames(styles.select, { [styles.errors]: isError })}
        classNamePrefix='select'
        {...rest}
      />
    </div>
  );
}

LabeledSelectCustomOption.propTypes = {
  value: PropTypes.string,
  label: PropTypes.string,
  options: PropTypes.array,
  onChange: PropTypes.func,
  disabled: PropTypes.bool,
  placeholder: PropTypes.string,
  valueKey: PropTypes.string,
  isError: PropTypes.bool,
  required: PropTypes.bool,
};

LabeledSelectCustomOption.defaultProps = {
  label: 'Label',
  onChange() {},
  options: [],
  valueKey: 'value',
  isDisabled: false,
  required: false,
};

export default memo(LabeledSelectCustomOption);
