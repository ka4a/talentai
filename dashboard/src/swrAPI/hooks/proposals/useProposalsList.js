import useSWR from 'swr';

import { useGetJob } from '@swrAPI';
import fetcher from '@swrAPI/fetcher';

const useProposalsList = () => {
  const { data: job } = useGetJob();

  const { data, mutate } = useSWR(
    job.id ? ['/proposals/', job.id] : null,
    (url, jobId) => fetcher(url, { params: { job: jobId } }),
    {
      fallbackData: { results: [] },
      refreshInterval: 60_000,
    }
  );

  return { data, mutate };
};

export default useProposalsList;
