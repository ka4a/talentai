import useSWR from 'swr';

import useFetchError from './useFetchError';

const useManagersList = () => {
  const { data, error } = useSWR('/managers/', {
    shouldRetryOnError: false,
    revalidateOnFocus: false,
    fallbackData: { results: [] },
  });

  useFetchError(error);

  return data.results.map((user) => ({
    value: user.id,
    name: `${user.firstName} ${user.lastName}`,
  }));
};

export default useManagersList;
