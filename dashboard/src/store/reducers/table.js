import { RESET_TABLE_PARAMS, UPDATE_TABLE_PARAM } from '@actions';

import createReducer from '../createReducer';

const defaultTableState = {
  limit: null,
  offset: null,
  search: null,
  ordering: null,
  defaultSort: null,
  paginationKey: null,
};

const actionHandlers = {
  [UPDATE_TABLE_PARAM]: (state, payload) => ({
    ...state,
    [payload.tableKey]: {
      ...state[payload.tableKey],
      [payload.key]: payload.value,
    },
  }),
  [RESET_TABLE_PARAMS]: (state, payload) => ({
    ...state,
    [payload.tableKey]: { ...defaultTableState },
  }),
};

export default createReducer({}, actionHandlers);
