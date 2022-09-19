import React, { memo, useMemo } from 'react';

import PropTypes from 'prop-types';
import classNames from 'classnames';

import EventIsolator from '../EventIsolator';

import styles from './TableRow.module.scss';

const TableCell = ({ link, row, col }) => {
  const { classes, align, dataField, formatter, preventRowMouseEvents, width } = col;

  let content = useMemo(() => {
    const data = row?.[dataField];

    if (!formatter) return data;

    let result = formatter(data, row, link);

    if (!preventRowMouseEvents) return result;

    return (
      <EventIsolator click mouseOut mouseOver>
        {result}
      </EventIsolator>
    );
  }, [row, dataField, formatter, link, preventRowMouseEvents]);

  return (
    <td className={classNames([classes, styles.cell])} style={{ width }} align={align}>
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
  row: PropTypes.object,
  link: PropTypes.shape({
    pathname: PropTypes.string.isRequired,
    state: PropTypes.object,
  }),
};

export default memo(TableCell);
