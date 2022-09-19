import useSWR from 'swr';

import fetcher from '@swrAPI/fetcher';

export default function useStaffRead(userId) {
  const { data, error, mutate } = useSWR(userId ? `/staff/${userId}` : null, fetcher);

  return {
    data,
    error,
    mutate,
    loading: !data && !error,
  };
}
