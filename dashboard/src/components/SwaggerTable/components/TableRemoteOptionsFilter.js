import React, { useCallback } from 'react';
import { Badge } from 'reactstrap';

import PropTypes from 'prop-types';

import ButtonTableMenu from '../../ButtonTableMenu';
import MultiselectMenu from '../../MultiselectMenu';

export default function TableRemoteOptionsFilter({
  state,
  setState,
  filter,
  options,
  name,
  searchable,
}) {
  const setFilter = useCallback(
    (newValue) => {
      setState((state) => ({
        params: {
          ...state.params,
          [filter]: newValue.length ? newValue : null,
        },
      }));
    },
    [setState, filter]
  );

  const selectedOptions = state.params[filter] || [];

  return (
    <MultiselectMenu
      onSelectionChange={setFilter}
      options={options}
      selected={selectedOptions}
      searchable={searchable}
    >
      <ButtonTableMenu>
        {name}
        {selectedOptions.length ? (
          <Badge color='primary' className='ml-2 mb-n2' pill>
            {selectedOptions.length}
          </Badge>
        ) : null}
      </ButtonTableMenu>
    </MultiselectMenu>
  );
}

TableRemoteOptionsFilter.propTypes = {
  filter: PropTypes.string.isRequired,
  options: PropTypes.array.isRequired,
  state: PropTypes.object.isRequired,
  setState: PropTypes.func.isRequired,

  searchable: PropTypes.bool,
  name: PropTypes.string,
  listSize: PropTypes.number,
};

TableRemoteOptionsFilter.defaultProps = {
  searchable: false,
};
