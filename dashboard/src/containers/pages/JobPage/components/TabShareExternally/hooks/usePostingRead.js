import { useParams } from 'react-router-dom';

import useSWR from 'swr';

const POSTING_SWR_SETTINGS = { shouldRetryOnError: false };

export default function usePostingRead(type) {
  // using params to not wait until job is loaded
  const { jobId } = useParams();

  return useSWR(jobId ? `/job_postings/${type}/${jobId}/` : null, POSTING_SWR_SETTINGS);
}
