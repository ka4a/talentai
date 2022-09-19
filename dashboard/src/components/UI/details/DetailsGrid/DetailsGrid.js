import React from 'react';

import PropTypes from 'prop-types';

import styles from './DetailsGrid.module.scss';

function DetailsGrid({ children, columnCount }) {
  const columnStyle = { gridTemplateColumns: `repeat(${columnCount}, 1fr)` };
  return (
    <div className={styles.root} style={columnStyle}>
      {children}
    </div>
  );
}

DetailsGrid.propTypes = {
  columnCount: PropTypes.number,
};

DetailsGrid.defaultProps = {
  columnCount: 4,
};

export default DetailsGrid;
