import useSWR from 'swr';

import fetcher from '@swrAPI/fetcher';

const customFetcher = (url, type) => fetcher(url, { params: { type } });

const useTagsList = (type) => {
  const { data } = useSWR(['/tags/', type], customFetcher, {
    shouldRetryOnError: false,
    revalidateOnFocus: false,
    fallbackData: [],
  });

  return { data };
};

export default useTagsList;
