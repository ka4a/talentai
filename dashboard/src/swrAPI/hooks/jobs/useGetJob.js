import { useParams } from 'react-router-dom';

import {
  usePrivateJobPostingRead,
  useJobsRead,
  useCareerSitePostingsRead,
} from '@swrAPI';

const useGetJob = () => {
  // TODO: Refactor SWR hooks to not use params and remove this hook
  const { uuid, jobSlug } = useParams();

  let useJobs = useJobsRead;
  if (uuid) {
    useJobs = usePrivateJobPostingRead;
  } else if (jobSlug) {
    useJobs = useCareerSitePostingsRead;
  }

  return useJobs();
};

export default useGetJob;
