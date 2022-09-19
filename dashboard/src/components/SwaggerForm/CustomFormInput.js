import React, { memo } from 'react';
import { useSelector } from 'react-redux';

import PropTypes from 'prop-types';

import {
  LabeledDatePicker,
  LabeledInput,
  LabeledMultiSelect,
  LabeledRichEditor,
  LabeledSelect,
  LabeledSelectCustomOption,
  LabeledPhoneInput,
  RatingInput,
} from '@components';
import StuffedLabeledInput from '@components/UI/LabeledInputs/StuffedLabeledInput/StuffedLabeledInput';

import Checkbox from '../UI/Checkbox';
import FormattedNumberInput from '../format/FormattedNumberInput';
import PercentageInput from '../PercentageInput';
import URLInput from '../URLInput';
import PasswordInput from '../PasswordInput';

const CustomFormInput = (props) => {
  const {
    type,
    name,
    id,
    value,
    options,
    onChange,
    validate,
    invalid,
    label,
    placeholder,
    tabIndex,
    disabled,
    required,
    ...rest
  } = props;

  const locale = useSelector((state) => state.settings.locale);

  const commonProps = {
    id,
    name,
    label,
    value,
    isError: invalid,
    isDisabled: disabled,
    placeholder,
    tabIndex,
  };

  commonProps.required = !commonProps.isDisabled && required;

  const onChangeHandler = (value) => onChange({ target: { name, value } });

  switch (type) {
    // old
    case 'percentage':
      return (
        <PercentageInput
          id={id}
          name={name}
          onChange={onChange}
          onBlur={validate}
          invalid={invalid}
          value={value}
          label={label}
          placeholder={placeholder}
          tabIndex={tabIndex}
          {...rest}
        />
      );
    case 'url':
      return (
        <URLInput
          bsSize='lg'
          id={id}
          name={name}
          value={value}
          onChange={onChange}
          invalid={invalid}
          onBlur={validate}
          label={label}
          placeholder={placeholder}
          tabIndex={tabIndex}
          {...rest}
        />
      );
    case 'password':
      return (
        <PasswordInput
          bsSize='lg'
          id={id}
          name={name}
          value={value}
          onChange={onChange}
          invalid={invalid}
          onBlur={validate}
          label={label}
          placeholder={placeholder}
          tabIndex={tabIndex}
          {...rest}
        />
      );

    // updated
    case 'checkbox': {
      return (
        <Checkbox
          checked={value}
          onChange={onChange}
          id={id}
          name={name}
          label={label}
          isDisabled={commonProps.isDisabled}
          {...rest}
        />
      );
    }
    case 'multi-select':
      return (
        <LabeledMultiSelect
          onChange={(selectedOptions) => {
            const event = {
              target: { name, value: selectedOptions?.map((el) => el.value) ?? [] },
            };
            onChange(event);
          }}
          options={options}
          {...commonProps}
          {...rest}
        />
      );
    case 'formatted-number':
      return (
        <FormattedNumberInput
          id={id}
          name={name}
          onChange={onChange}
          onBlur={validate}
          isError={invalid}
          value={value}
          label={label}
          placeholder={placeholder}
          tabIndex={tabIndex}
          {...rest}
        />
      );
    case 'rich-editor':
      return (
        <LabeledRichEditor onChange={onChangeHandler} {...commonProps} {...rest} />
      );
    case 'custom-option-select':
      return (
        <LabeledSelectCustomOption
          onChange={onChangeHandler}
          options={options}
          {...commonProps}
          {...rest}
        />
      );
    case 'select':
      return (
        <LabeledSelect
          onChange={onChangeHandler}
          options={options}
          {...commonProps}
          {...rest}
        />
      );
    case 'simple-datepicker':
      return (
        <LabeledDatePicker
          {...commonProps}
          {...rest}
          onChange={onChangeHandler}
          locale={locale}
        />
      );
    case 'password-no-icon':
      return (
        <LabeledInput
          onChange={onChange}
          onBlur={validate}
          type='password'
          {...commonProps}
          {...rest}
        />
      );
    case 'phone':
      return (
        <LabeledPhoneInput
          onBlur={() => validate({ target: { name } })}
          onChange={onChangeHandler}
          {...commonProps}
          {...rest}
        />
      );
    case 'rating':
      return <RatingInput onChange={onChangeHandler} {...commonProps} {...rest} />;
    case 'stuffed':
      return (
        <StuffedLabeledInput
          onBlur={validate}
          onChange={onChange}
          {...commonProps}
          {...rest}
        />
      );
    default:
      return (
        <LabeledInput
          onChange={onChange}
          onBlur={validate}
          {...commonProps}
          {...rest}
        />
      );
  }
};

CustomFormInput.displayName = 'CustomFormInput';

CustomFormInput.propTypes = {
  id: PropTypes.string,
  type: PropTypes.string,
  name: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  value: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.number,
    PropTypes.bool,
    PropTypes.array,
  ]),
  options: PropTypes.arrayOf(PropTypes.object),
  onChange: PropTypes.func,
  validate: PropTypes.func,
  invalid: PropTypes.bool,
  checkboxLabel: PropTypes.string,
};

CustomFormInput.defaultProps = {
  id: null,
  type: 'text',
  value: null,
  options: null,
  onChange() {},
  validate() {},
  invalid: false,
  checkboxLabel: null,
};

export default memo(CustomFormInput);
