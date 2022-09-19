import useSWR from 'swr';

import useFetchError from '@swrAPI/hooks/useFetchError';
import fetcher from '@swrAPI/fetcher';

const jobsFetcher = (
  url,
  search,
  limit = 30,
  offset,
  ordering,
  status,
  show_pipeline,
  is_belong_to_user_org,
  check_candidate_proposed
) =>
  fetcher(url, {
    params: {
      search,
      limit,
      offset,
      ordering,
      status,
      show_pipeline,
      is_belong_to_user_org,
      check_candidate_proposed,
    },
  });

const useJobsList = ({
  search,
  limit,
  offset,
  ordering,
  status,
  show_pipeline,
  is_belong_to_user_org,
  checkCandidateProposed,
}) => {
  const { data, error, mutate } = useSWR(
    [
      '/jobs/',
      search,
      limit,
      offset,
      ordering,
      status,
      show_pipeline,
      is_belong_to_user_org,
      checkCandidateProposed,
    ],
    jobsFetcher
  );

  useFetchError(error);

  return {
    data,
    loading: !data && !error,
    error,
    mutate,
  };
};

export default useJobsList;
