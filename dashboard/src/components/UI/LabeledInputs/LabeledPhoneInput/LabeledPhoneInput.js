import React, { memo, useCallback } from 'react';
import PhoneInput from 'react-phone-input-2';
import { useDebounce } from 'react-use';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import Typography from '../../Typography';

import styles from './LabeledPhoneInput.module.scss';
import 'react-phone-input-2/lib/high-res.css';

const LabeledPhoneInput = (props) => {
  const {
    name,
    value,
    label,
    defaultCountry,
    wrapperClassName,
    preferredCountries,
    required,
    isDisabled,
    isError,
    onChange,
    onBlur,
    withPlus,
  } = props;

  // assume that blur contains validation handler
  const [, validate] = useDebounce(onBlur, 1000, [value]);

  const handleChange = useCallback(
    (value) => {
      onChange(withPlus && value ? `+${value}` : value);
      validate();
    },
    [validate, onChange, withPlus]
  );

  return (
    <div
      className={classnames(styles.wrapper, wrapperClassName, {
        [styles.disabled]: isDisabled,
      })}
    >
      <label className={styles.label}>
        <Typography variant='caption'>
          {label}
          {required && <span className={styles.required}>*</span>}
        </Typography>
      </label>

      <div className={classnames({ [styles.errors]: isError })}>
        <PhoneInput
          value={value ?? ''}
          country={defaultCountry}
          preferredCountries={preferredCountries}
          onChange={handleChange}
          onBlur={onBlur}
          inputProps={{ name }}
          disabled={Boolean(isDisabled)}
          inputClass={styles.input}
          buttonClass={styles.dropdownButton}
        />
      </div>
    </div>
  );
};

LabeledPhoneInput.propTypes = {
  name: PropTypes.string,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  label: PropTypes.string,
  defaultCountry: PropTypes.string,
  preferredCountries: PropTypes.array,
  required: PropTypes.bool,
  isDisabled: PropTypes.bool,
  isError: PropTypes.bool,
  wrapperClassName: PropTypes.string,
  onChange: PropTypes.func,
  onBlur: PropTypes.func,
  withPlus: PropTypes.bool,
};

LabeledPhoneInput.defaultProps = {
  name: '',
  value: '',
  label: '',
  defaultCountry: 'jp',
  wrapperClassName: '',
  preferredCountries: [],
  required: false,
  isDisabled: false,
  isError: false,
  withPlus: true,
  onChange: () => {},
  onBlur: () => {},
};

export default memo(LabeledPhoneInput);
