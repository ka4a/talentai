import React, { forwardRef, memo, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { Input } from 'reactstrap';
import DatePicker from 'react-datepicker';

import classnames from 'classnames';
import PropTypes from 'prop-types';
import moment from 'moment';

import { DATE_FORMAT } from '@constants';
import { Typography } from '@components';
import { ReactComponent as Calendar } from '@images/icons/calendar.svg';
import { ReactComponent as ClockFilled } from '@images/icons/clockFilled.svg';

import styles from './LabeledDatePicker.module.scss';

const LabeledDatePicker = (props) => {
  const {
    label,
    value,
    onChange,
    isDisabled,
    placeholder,
    isError,
    dateInputFormat,
    format,
    name,
    required,
    showTimeSelectOnly,
    ...rest
  } = props;

  const locale = useSelector((state) => state.settings.locale);

  const DatepickerInput = forwardRef((props, ref) => (
    <div className={styles.inputWrapper}>
      <Input
        ref={ref}
        {...props}
        className={classnames(styles.input, props.className, {
          [styles.errors]: isError,
        })}
      />

      {showTimeSelectOnly ? <ClockFilled /> : <Calendar />}
    </div>
  ));

  const handleChange = useCallback(
    (value) => {
      if (!value) {
        onChange('');
        return;
      }

      const result = format ? moment(value).format(format) : value;
      onChange(result);
    },
    [format, onChange]
  );

  return (
    <div className={classnames(styles.wrapper, { [styles.disabled]: isDisabled })}>
      <label className={styles.label}>
        <Typography variant='caption'>
          {label}
          {required && <span className={styles.required}>*</span>}
        </Typography>
      </label>

      <DatePicker
        name={name}
        disabled={isDisabled}
        selected={value && new Date(value)}
        onChange={handleChange}
        customInput={<DatepickerInput />}
        locale={locale}
        placeholderText={placeholder}
        dateFormat={dateInputFormat}
        showMonthDropdown
        showYearDropdown
        wrapperClassName={styles.datepicker}
        autoComplete='off'
        showTimeSelectOnly={showTimeSelectOnly}
        {...rest}
      />
    </div>
  );
};

LabeledDatePicker.propTypes = {
  value: PropTypes.string,
  label: PropTypes.string,
  onChange: PropTypes.func,
  isDisabled: PropTypes.bool,
  placeholder: PropTypes.string,
  isError: PropTypes.bool,
  format: PropTypes.string,
  dateInputFormat: PropTypes.string,
  required: PropTypes.bool,
  showTimeSelectOnly: PropTypes.bool,
};

LabeledDatePicker.defaultProps = {
  value: null,
  label: 'Label',
  onChange() {},
  isDisabled: false,
  format: null,
  dateInputFormat: DATE_FORMAT.picker,
  required: false,
  showTimeSelectOnly: false,
};

export default memo(LabeledDatePicker);
