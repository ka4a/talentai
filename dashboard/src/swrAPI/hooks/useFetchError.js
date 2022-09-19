import { useEffect, useRef } from 'react';

import { fetchErrorHandler } from '@utils';

let wasError = false;

const useFetchError = (error) => {
  const timeoutId = useRef(null);

  useEffect(() => {
    if (error && !wasError) {
      wasError = true;

      timeoutId.current = setTimeout(() => {
        wasError = false;
      }, 10000);

      fetchErrorHandler(error);
    }
  }, [error]);

  useEffect(() => {
    return () => {
      clearTimeout(timeoutId.current);
    };
  }, []);
};

export default useFetchError;
