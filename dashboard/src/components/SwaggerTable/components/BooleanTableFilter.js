import React, { useCallback } from 'react';

import PropTypes from 'prop-types';

import Checkbox from '../../UI/Checkbox';

export default function BooleanTableFilter(props) {
  const { state, setState, filter, label } = props;

  const setFilter = useCallback(() => {
    setState((state) => ({
      params: {
        ...state.params,
        [filter]: !state.params[filter],
      },
    }));
  }, [setState, filter]);

  return (
    <label className='m-0'>
      <Checkbox onChange={setFilter} checked={state.params[filter]} />
      <span>{label}</span>
    </label>
  );
}

BooleanTableFilter.propTypes = {
  state: PropTypes.object.isRequired,
  setState: PropTypes.func.isRequired,
  filter: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
};
