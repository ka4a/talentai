import useSWR from 'swr';

const useCareerSitePostingsRead = (orgSlug, jobSlug) => {
  const { data, error, mutate } = useSWR(
    orgSlug && jobSlug ? `/public/career_site/${orgSlug}/job_postings/${jobSlug}` : null
  );

  return {
    data,
    loading: !data && !error,
    error,
    mutate,
  };
};

export default useCareerSitePostingsRead;
