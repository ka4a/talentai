import React, { memo } from 'react';

import PropTypes from 'prop-types';

import Typography from '@components/UI/Typography';

import SortButton from '../SortButton';

const TableRowHeader = (props) => {
  const { col, defaultSort, state, setState, isOpenColumn } = props;

  const colText = col.headerFormatter ? col.headerFormatter(col) : col.text;

  const typographyLabel = colText && (
    <Typography variant='caption'>{colText}</Typography>
  );

  if (isOpenColumn && col?.hideInSidebar) return null;

  return (
    <th className={col.align ? `text-${col.align}` : ''}>
      {col.sort && typographyLabel ? (
        <SortButton
          state={state}
          setState={setState}
          dataField={col.dataField}
          defaultSort={defaultSort}
        >
          {typographyLabel}
        </SortButton>
      ) : (
        typographyLabel
      )}

      {col.filter && (
        <span className='ml-4 d-inline-block'>{col.filter({ state, setState })}</span>
      )}
    </th>
  );
};

TableRowHeader.propTypes = {
  col: PropTypes.shape({}).isRequired,
  state: PropTypes.shape({}).isRequired,
  setState: PropTypes.func.isRequired,
  defaultSort: PropTypes.string.isRequired,
  isOpenColumn: PropTypes.bool.isRequired,
};

export default memo(TableRowHeader);
