import React, { memo, useContext } from 'react';

import PropTypes from 'prop-types';

import Typography from '@components/UI/Typography';

import TableContext from '../../tableContext';
import SortButton from '../SortButton';

const TableRowHeader = ({ col }) => {
  const { text, hideInSidebar, align, dataField, sort } = col;

  const { isOpenColumn } = useContext(TableContext);

  const typographyLabel = text && <Typography variant='caption'>{text}</Typography>;

  if (isOpenColumn && hideInSidebar) return null;

  return (
    <th className={align ? `text-${align}` : ''}>
      {sort && typographyLabel ? (
        <SortButton dataField={dataField}>{typographyLabel}</SortButton>
      ) : (
        typographyLabel
      )}
    </th>
  );
};

TableRowHeader.propTypes = {
  col: PropTypes.shape({}).isRequired,
};

export default memo(TableRowHeader);
