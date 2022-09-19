import React from 'react';

import PropTypes from 'prop-types';
import classNames from 'classnames';

import styles from './FormSection.module.scss';

function FormSubsection({ columnCount, isGrid, children }) {
  const columnStyle = { gridTemplateColumns: `repeat(${columnCount}, 1fr)` };

  return (
    <div
      className={classNames(styles.subsection, { [styles.isGrid]: isGrid })}
      style={columnStyle}
    >
      {children}
    </div>
  );
}

FormSubsection.propTypes = {
  columnCount: PropTypes.number,
  isGrid: PropTypes.bool,
};

FormSubsection.defaultProps = {
  columnCount: 2,
  isGrid: false,
};

export default FormSubsection;
