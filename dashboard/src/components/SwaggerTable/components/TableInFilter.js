import React from 'react';

import classnames from 'classnames';
import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import MultiselectMenu from '../../MultiselectMenu';

export default function TableInFilter({
  state,
  setState,
  filter,
  options,
  direction,
  title,
}) {
  const selectedOptions = state?.params[filter] || [];

  function setFilter(newValue) {
    setState({
      params: {
        ...state.params,
        [filter]: newValue.length ? newValue : null,
      },
    });
  }

  return (
    <div
      className={classnames(
        { 'table-filter': selectedOptions.length === 0 },
        { 'table-filter active': selectedOptions.length > 0 }
      )}
    >
      <MultiselectMenu
        onSelectionChange={setFilter}
        options={options}
        selected={selectedOptions}
        direction={direction}
      >
        <div className='label'>
          <Trans>{title}</Trans>
          {/* <MdFilterList size='1.5em' /> */}
        </div>
      </MultiselectMenu>
    </div>
  );
}

TableInFilter.propTypes = {
  filter: PropTypes.string.isRequired,
  options: PropTypes.array.isRequired,
  state: PropTypes.object.isRequired,
  setState: PropTypes.func.isRequired,
  title: PropTypes.string,
};
