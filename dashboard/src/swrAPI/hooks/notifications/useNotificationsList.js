import useSWR from 'swr';

import fetcher from '@swrAPI/fetcher';

const customFetcher = (url, search, ordering, limit, offset) =>
  fetcher(url, {
    params: {
      search,
      ordering,
      limit,
      offset,
    },
  });

const useNotificationsList = ({ search, ordering, limit, offset } = {}) => {
  const { data, mutate, error } = useSWR(
    ['/notifications/', search, ordering, limit, offset],
    customFetcher,
    { shouldRetryOnError: false }
  );

  return {
    data,
    mutate,
    loading: !data && !error,
    error,
  };
};

export default useNotificationsList;
