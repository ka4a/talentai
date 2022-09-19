import { useCallback, useState } from 'react';

import { isFunction, merge } from 'lodash';

import { getTableState } from '../helpers';

const getNewState = (migration, state) =>
  isFunction(migration) ? migration(state) : migration;

const useSwaggerTableState = (initialState) => {
  const [state, replaceState] = useState({
    ...merge({ ...getTableState({ key: 'state' }).state }, { ...initialState }),
  });

  const setState = useCallback(
    (migration) => {
      replaceState((currentState) => ({
        ...currentState,
        ...getNewState(migration, currentState),
      }));
    },
    [replaceState]
  );

  return [state, setState];
};

export default useSwaggerTableState;
