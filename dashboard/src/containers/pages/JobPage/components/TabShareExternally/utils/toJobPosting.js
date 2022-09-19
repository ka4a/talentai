import cleanUpJobPosting from './cleanUpJobPosting';

export default function toJobPosting(job, baseJobPosting) {
  return cleanUpJobPosting({
    // if we use this function to generate reset data
    // we need to preserve posting fields which dont have job equivalent
    // like 'isEnabled' field
    ...baseJobPosting,
    ...job,
    function: job.function?.id ?? null,
    jobId: job.id,
  });
}
