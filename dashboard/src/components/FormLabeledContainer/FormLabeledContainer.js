import React from 'react';
import { FormGroup, Label } from 'reactstrap';

import PropTypes from 'prop-types';

import styles from './FormLabeledContainer.module.scss';

FormLabeledContainer.propTypes = {
  label: PropTypes.string,
  isText: PropTypes.bool,
  className: PropTypes.string,
  rightFloat: PropTypes.string,
  isCompact: PropTypes.bool,
};

function FormLabeledContainer(props) {
  const { isText, isCompact, children, label, className, rightFloat } = props;
  return (
    <FormGroup className={className}>
      {rightFloat ? (
        <div className='clearfix'>
          <Label>{label}</Label>
          <div className='float-right p-0 border-0'>{rightFloat}</div>
        </div>
      ) : (
        <Label className='text-left'>{label}</Label>
      )}
      {isText ? (
        <div className={isCompact ? styles.compactTextContainer : styles.textContainer}>
          {children}
        </div>
      ) : (
        children
      )}
    </FormGroup>
  );
}

export default FormLabeledContainer;
