import { useParams } from 'react-router-dom';

import useSWR from 'swr';

const useCandidatesRead = () => {
  const { candidateId } = useParams();

  const { data, error, mutate } = useSWR(
    candidateId ? `/candidates/${candidateId}/` : null
  );

  return {
    data: data ?? {},
    error,
    loading: !data && !error,
    mutate,
  };
};

export default useCandidatesRead;
