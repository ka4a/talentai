import { useCallback, useEffect, useState } from 'react';

import { getErrorTextFromFetchError } from '@utils';

import { client } from '../client';
import { useDeepCompareMemoize } from './index';

export default function useSwagger(operationId, parameters, processObj) {
  const [obj, setObj] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [errorObj, setErrorObj] = useState(null);

  // it's outside of useEffect, to be able to cancel refresh call
  let didCancel = false;

  const memoizedParameters = useDeepCompareMemoize(parameters);
  const refresh = useCallback(
    async () => {
      setLoading(true);
      try {
        const response = await client.execute({
          operationId,
          parameters: memoizedParameters,
        });

        if (didCancel) return;
        setObj(processObj ? processObj(response.obj) : response.obj);
        setError(false);
      } catch (error) {
        if (didCancel) return;
        setObj(null);
        setError(getErrorTextFromFetchError(error));
        setErrorObj(error);
      }
      if (didCancel) return;
      setLoading(false);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [operationId, memoizedParameters]
  );

  useEffect(() => {
    refresh();
    return () => {
      // eslint-disable-next-line react-hooks/exhaustive-deps
      didCancel = true;
    };
  }, [refresh]);

  return { obj, setObj, refresh, loading, error, errorObj };
}
