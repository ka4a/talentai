import React, { memo, useCallback } from 'react';

import PropTypes from 'prop-types';

import { LabeledInput } from '@components';

const RE_NUMBER = /^\d*\.?\d*$/;
const RE_COMMA_SEPARATOR = /,/g;
const RE_DIGIT_BEFORE_THREE_DIGITS = /(\d)(?=(\d{3})+(?!\d)\.?)/g;

const getFormattedNumber = (value) => {
  value = String(value);
  if (value === '.') return '0.';
  return value.replace(RE_DIGIT_BEFORE_THREE_DIGITS, '$1,');
};

const FormattedNumberInput = ({ value, onChange, ...rest }) => {
  const handleChange = useCallback(
    (event) => {
      const newValue = event.target.value;

      const noCommaValue = newValue.replace(RE_COMMA_SEPARATOR, '');
      const valueIsNumber = RE_NUMBER.test(noCommaValue);
      if (!valueIsNumber) return;

      event.target.value = noCommaValue;
      onChange(event);
    },
    [onChange]
  );

  return (
    <LabeledInput value={getFormattedNumber(value)} onChange={handleChange} {...rest} />
  );
};

FormattedNumberInput.propTypes = {
  onChange: PropTypes.func,
};

FormattedNumberInput.defaultProps = {
  onChange: () => {},
};

export default memo(FormattedNumberInput);
