import { useParams } from 'react-router-dom';

import useSWR from 'swr';

import fetcher from '@swrAPI/fetcher';

const jobsFetcher = (url) => fetcher(url, { params: { show_pipeline: true } });

const useJobsRead = () => {
  const { jobId } = useParams();

  const { data, error, mutate } = useSWR(jobId ? `/jobs/${jobId}/` : null, jobsFetcher);

  return {
    data,
    loading: !data && !error,
    error,
    mutate,
  };
};

export default useJobsRead;
