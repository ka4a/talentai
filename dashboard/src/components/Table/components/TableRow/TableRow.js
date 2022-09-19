import React, { memo, useContext, useRef } from 'react';
import { useHoverDirty } from 'react-use';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import TableContext from '../../tableContext';
import TableCell from './TableCell';

import styles from './TableRow.module.scss';

const TableRow = ({ row, columns, rowClasses, onClick, isActive }) => {
  const { isOpenColumn } = useContext(TableContext);

  const rowRef = useRef(null);
  const isHovering = useHoverDirty(rowRef);

  const handleClick = (e) => onClick(e, row);

  return (
    <tr
      ref={rowRef}
      onClick={handleClick}
      className={classnames(rowClasses(row), {
        [styles.rowHover]: isHovering,
        [styles.isActive]: isActive,
      })}
    >
      {columns.map((col, i) => {
        if (isOpenColumn && col.hideInSidebar) return null;
        return <TableCell key={i} col={col} row={row} isActive={isActive} />;
      })}
    </tr>
  );
};

TableRow.propTypes = {
  row: PropTypes.shape({}).isRequired,
  columns: PropTypes.arrayOf(PropTypes.object).isRequired,
  rowClasses: PropTypes.func.isRequired,
  onClick: PropTypes.func.isRequired,
  isActive: PropTypes.bool,
};

TableRow.defaultProps = {
  isActive: false,
};

export default memo(TableRow);
