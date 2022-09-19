import React, { memo, useCallback } from 'react';
import Select from 'react-select';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import Typography from '../../Typography';

import styles from './LabeledSelect.module.scss';

const LabeledSelect = (props) => {
  const {
    label,
    value,
    valueKey,
    labelKey,
    options: sourceOptions,
    onChange,
    isDisabled,
    searchable,
    placeholder,
    isError,
    clearable,
    required,
    onSelectCallback,
    ...rest
  } = props;

  const emptyOption = { [valueKey]: '', [labelKey]: '-' };
  const options = clearable ? [emptyOption, ...sourceOptions] : sourceOptions;

  const selectedValue = options.find((option) => option[valueKey] === value);

  const onSelect = useCallback(
    (option) => {
      onChange(option[valueKey]);
      onSelectCallback(option);
    },
    [onChange, onSelectCallback, valueKey]
  );

  const inlineStyles = {
    menuPortal: (base) => ({
      ...base,
      zIndex: 310,
    }),
  };

  return (
    <div className={classnames(styles.wrapper, { [styles.disabled]: isDisabled })}>
      <label className={styles.label}>
        <Typography variant='caption'>
          {label}
          {required && <span className={styles.required}>*</span>}
        </Typography>
      </label>

      <Select
        styles={inlineStyles}
        value={selectedValue}
        menuPortalTarget={document.body}
        portalPlacement='bottom'
        onChange={onSelect}
        getOptionLabel={(option) => option[labelKey]}
        getOptionValue={(option) => option[valueKey]}
        options={options}
        placeholder={placeholder}
        isDisabled={isDisabled}
        isSearchable={searchable}
        className={classnames(styles.select, { [styles.errors]: isError })}
        classNamePrefix='select'
        {...rest}
      />
    </div>
  );
};

LabeledSelect.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  valueKey: PropTypes.string,
  labelKey: PropTypes.string,
  onChange: PropTypes.func,
  options: PropTypes.array,
  isDisabled: PropTypes.bool,
  searchable: PropTypes.bool,
  placeholder: PropTypes.string,
  isError: PropTypes.bool,
  required: PropTypes.bool,
  onSelectCallback: PropTypes.func,
};

LabeledSelect.defaultProps = {
  value: '',
  valueKey: 'value',
  labelKey: 'name',
  options: [],
  isDisabled: false,
  searchable: false,
  required: false,
  onChange: () => {},
  onSelectCallback: () => {},
};

export default memo(LabeledSelect);
