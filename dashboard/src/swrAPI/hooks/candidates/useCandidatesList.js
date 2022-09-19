import useSWR from 'swr';

import fetcher from '@swrAPI/fetcher';

const customFetcher = (url, search, ordering, limit, offset, checkProposedTo) =>
  fetcher(url, {
    params: { search, ordering, limit, offset, check_proposed_to: checkProposedTo },
  });

const useCandidatesList = ({ search, ordering, limit, offset, checkProposedTo }) => {
  const { data, mutate, error } = useSWR(
    [`/candidates/`, search, ordering, limit, offset, checkProposedTo],
    customFetcher
  );

  return {
    data,
    loading: !data && !error,
    error,
    mutate,
  };
};

export default useCandidatesList;
