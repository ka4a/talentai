export const UPDATE_TABLE_PARAM = 'UPDATE_TABLE_PARAM';
export const RESET_TABLE_PARAMS = 'RESET_TABLE_PARAMS';

export const updateTableParam = (tableKey, key, value) => ({
  type: UPDATE_TABLE_PARAM,
  payload: { tableKey, key, value },
});

export const resetTableParams = (tableKey) => ({
  type: RESET_TABLE_PARAMS,
  payload: { tableKey },
});
