import React, { memo, useContext } from 'react';
import Select from 'react-select';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import { Typography } from '@components';

import MenuPortalContext from './MenuPortalContext';

import styles from './LabeledMultiSelect.module.scss';

const LabeledMultiSelect = (props) => {
  const {
    label,
    labelKey,
    value,
    options,
    onChange,
    isDisabled,
    placeholder,
    required,
    ...rest
  } = props;

  const selectedValues = options.filter((el) => value.includes(el.value));

  const menuContainerRef = useContext(MenuPortalContext);

  return (
    <div className={classnames(styles.wrapper, { [styles.disabled]: isDisabled })}>
      <label className={styles.label}>
        <Typography variant='caption'>{label}</Typography>
        {required && <span className={styles.required}>*</span>}
      </label>

      <Select
        menuPortalTarget={menuContainerRef?.current}
        value={selectedValues}
        options={options}
        hideSelectedOptions={false}
        className={styles.multiselect}
        classNamePrefix='multiselect'
        placeholder={placeholder}
        onChange={onChange}
        closeMenuOnSelect={false}
        getOptionLabel={(option) => option[labelKey]}
        isMulti
        {...rest}
      />
    </div>
  );
};

LabeledMultiSelect.propTypes = {
  value: PropTypes.arrayOf(PropTypes.string),
  label: PropTypes.string,
  labelKey: PropTypes.string,
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string,
    })
  ),
  onChange: PropTypes.func,
  isDisabled: PropTypes.bool,
  placeholder: PropTypes.string,
  required: PropTypes.bool,
  isError: PropTypes.bool,
};

LabeledMultiSelect.defaultProps = {
  label: '',
  options: [],
  onChange() {},
  labelKey: 'name',
  isDisabled: false,
  required: false,
};

export default memo(LabeledMultiSelect);
