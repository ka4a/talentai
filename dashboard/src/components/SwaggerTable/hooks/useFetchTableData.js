import { useCallback } from 'react';

import { t } from '@lingui/macro';

import { client } from '@client';

const useFetchTableData = (operationId) => {
  return useCallback(
    async (newParams) => {
      const parameters = newParams?.search ? newParams : { ...newParams, search: null };

      const tableUpdate = {
        params: parameters,
        loading: false,
      };

      try {
        const { obj } = await client.execute({
          operationId,
          parameters,
        });

        tableUpdate.data = obj;
      } catch (error) {
        tableUpdate.error = t`An error occurred.`;
      }

      return tableUpdate;
    },
    [operationId]
  );
};

export default useFetchTableData;
