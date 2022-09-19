import isFunction from 'lodash/isFunction';

import { client } from '@client';
import { getErrorTextFromFetchError } from '@utils';

export const TABLE_KEY = 'tableData';

export const getTableState = ({ key = TABLE_KEY, params = {} } = {}) => ({
  [key]: {
    initialized: false,
    loading: true,
    error: null,

    data: { results: [], count: null },

    params: {
      offset: 0,
      ordering: null,
      search: '',
      ...params,
    },
  },
});

export const makeFetchTableData = (operationId, tableDataKey = TABLE_KEY) => {
  return function (newParams = {}) {
    const tableData = this.state[tableDataKey];

    const params = {
      ...tableData.params,
      ...newParams,
    };

    return new Promise((resolve) => {
      client
        .execute({
          operationId: operationId,
          parameters: {
            ...params,
            search: params.search ? params.search : null,
          },
        })
        .then((response) => {
          resolve({
            params: params,
            data: response.obj,
            loading: false,
            error: null,
          });
        })
        .catch((error) => {
          resolve({
            params: params,
            loading: false,
            error: getErrorTextFromFetchError(error),
          });
        });
    });
  };
};

export const makeSetTableData = (tableDataKey = TABLE_KEY) => {
  return function (newState, callback) {
    this.setState(
      (state) => ({
        [tableDataKey]: {
          ...state[tableDataKey],
          ...(isFunction(newState) ? newState(state[tableDataKey]) : newState),
        },
      }),
      callback
    );
  };
};

export const makeRefreshTableData = (fetchTableData, setTableState) => async () => {
  const newState = await fetchTableData();
  setTableState(newState);
};
