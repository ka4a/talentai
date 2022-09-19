import React from 'react';
import { MdUnfoldMore } from 'react-icons/md';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import styles from './SelectInput.module.scss';

function SelectInputFormTrigger({
  value,
  className,
  disabled,
  bsSize = 'lg',
  invalid,
  placeholder,
  ...rest
}) {
  return (
    <div
      tabIndex={-1 /* so it would be focusable on click*/}
      className={classnames(styles.button, className, 'form-control', {
        'form-control-lg': bsSize === 'lg',
        'is-invalid': invalid,
      })}
      {...rest}
    >
      {value ? (
        <span>{value}</span>
      ) : (
        <span className={styles.placeholder}>{placeholder}</span>
      )}

      <MdUnfoldMore
        className={classnames(styles.icon, { [styles.iconInvalid]: invalid })}
      />
    </div>
  );
}

SelectInputFormTrigger.propTypes = {
  value: PropTypes.string,
  placeholder: PropTypes.string,
  className: PropTypes.string,
  bsSize: PropTypes.string,
  empty: PropTypes.bool,
  invalid: PropTypes.bool,
  disabled: PropTypes.bool,
};

SelectInputFormTrigger.defaultValue = {
  value: '',
  placeholder: '',
  className: '',
  bsSize: 'lg',
  invalid: false,
  disabled: false,
};

export default SelectInputFormTrigger;
