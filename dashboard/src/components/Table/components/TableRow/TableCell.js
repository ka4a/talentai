import React, { memo, useContext, useMemo } from 'react';

import classNames from 'classnames';
import PropTypes from 'prop-types';
import get from 'lodash/get';

import TableContext from '../../tableContext';

import styles from './TableRow.module.scss';

const TableCell = ({ row, col, isActive }) => {
  const { classes, align, dataField, formatter, width } = col;

  const { withBorder, isOpenColumn } = useContext(TableContext);

  const content = useMemo(() => {
    const data = get(row, dataField);

    if (!formatter) return data;

    return formatter(data, row, { isActive });
  }, [row, dataField, formatter, isActive]);

  return (
    <td
      className={classNames([
        classes,
        styles.cell,
        { [styles.withBorder]: withBorder && !isOpenColumn },
      ])}
      style={{ width }}
      align={align}
    >
      {content}
    </td>
  );
};

TableCell.propTypes = {
  col: PropTypes.shape({
    align: PropTypes.string,
    classes: PropTypes.string,
    formatter: PropTypes.func,
    dataField: PropTypes.string,
  }),
  isActive: PropTypes.bool,
  row: PropTypes.object,
};

export default memo(TableCell);
