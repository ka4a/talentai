import { useMemo } from 'react';

import { cleanUpJobPosting, toJobPosting } from '../utils';

export default function useInitialJobPostingFormState(job, jobPosting) {
  return useMemo(
    () => (jobPosting ? cleanUpJobPosting(jobPosting) : toJobPosting(job)),
    [job, jobPosting]
  );
}
