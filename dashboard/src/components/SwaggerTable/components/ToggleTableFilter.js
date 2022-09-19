import React, { useCallback } from 'react';
import { Button, ButtonGroup } from 'reactstrap';

import PropTypes from 'prop-types';
import _ from 'lodash';

export default function ToggleTableFilter(props) {
  const { filter, state, setState, options, className } = props;

  const setFilter = useCallback(
    (value) => {
      setState((state) => ({
        params: {
          ...state.params,
          [filter]: value,
        },
      }));
    },
    [setState, filter]
  );

  return (
    <ButtonGroup className={className}>
      {_.map(options, (option) => (
        <Button
          key={option.value || option.label}
          color={state.params[filter] === option.value ? 'primary' : 'secondary'}
          onClick={() => setFilter(option.value)}
        >
          {option.label}
        </Button>
      ))}
    </ButtonGroup>
  );
}

ToggleTableFilter.propTypes = {
  filter: PropTypes.string.isRequired,
  options: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      value: PropTypes.string.isRequired,
    }).isRequired
  ).isRequired,
  state: PropTypes.object.isRequired,
  setState: PropTypes.func.isRequired,
};
