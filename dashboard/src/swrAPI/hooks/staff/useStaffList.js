import useSWR from 'swr';

import fetcher from '@swrAPI/fetcher';

import useFetchError from '../useFetchError';

const useStaffList = (params = null) => {
  const fetcherArgs = params
    ? [STAFF_URL, params.search, params.ordering, params.limit, params.offset]
    : [STAFF_URL];

  const { data, error, mutate } = useSWR(fetcherArgs, staffFetcher, {
    shouldRetryOnError: false,
    revalidateOnFocus: false,
  });

  useFetchError(error);

  return {
    data,
    error,
    mutate,
    loading: !data && !error,
  };
};

const staffFetcher = (url, search, ordering, limit, offset) =>
  fetcher(url, { params: { search, ordering, limit, offset } });

const STAFF_URL = '/staff/';

export default useStaffList;
