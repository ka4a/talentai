import { useParams } from 'react-router-dom';

import useSWR from 'swr';

const useCareerSitePostingsList = () => {
  const { slug } = useParams();

  const { data, error, mutate } = useSWR(
    slug ? `/career_site/${slug}/job_postings/` : null
  );

  return {
    data,
    loading: !data && !error,
    error,
    mutate,
  };
};

export default useCareerSitePostingsList;
