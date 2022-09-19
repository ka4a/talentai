import React, { memo } from 'react';
import { InputGroup, Input } from 'reactstrap';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import Typography from '../../Typography';

import styles from '../commonInputStyles.module.scss';

const LabeledInput = (props) => {
  const {
    label,
    value,
    onChange,
    isDisabled,
    isError,
    required,
    inputClassName,
    wrapperClassName,
    withoutCapitalize,
    children,
    ...rest
  } = props;

  return (
    <div
      className={classnames(styles.wrapper, wrapperClassName, {
        [styles.disabled]: isDisabled,
      })}
    >
      <label
        className={classnames([
          styles.label,
          { [styles.withoutCapitalize]: withoutCapitalize },
        ])}
      >
        <Typography variant='caption'>
          {label}
          {required && <span className={styles.required}>*</span>}
        </Typography>
      </label>

      <InputGroup className={classnames({ [styles.errors]: isError })}>
        <Input
          type='text'
          value={value ?? ''}
          onChange={onChange}
          className={classnames([styles.input, inputClassName])}
          disabled={isDisabled}
          autoComplete='false'
          {...rest}
        />
      </InputGroup>
      {children}
    </div>
  );
};

export default memo(LabeledInput);

LabeledInput.propTypes = {
  onChange: PropTypes.func,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  label: PropTypes.string,
  wrapperClassName: PropTypes.string,
  inputClassName: PropTypes.string,
  isDisabled: PropTypes.bool,
  placeholder: PropTypes.string,
  required: PropTypes.bool,
  isError: PropTypes.bool,
  componentValue: PropTypes.element,
  type: PropTypes.string,
  withoutCapitalize: PropTypes.bool,
  children: PropTypes.oneOfType([PropTypes.arrayOf(PropTypes.node), PropTypes.node]),
};

LabeledInput.defaultProps = {
  label: '',
  value: '',
  wrapperClassName: '',
  inputClassName: '',
  onChange: () => {},
  required: false,
  isDisabled: false,
  withoutCapitalize: false,
};
