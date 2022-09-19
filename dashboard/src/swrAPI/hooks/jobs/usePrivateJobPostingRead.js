import useSWR from 'swr';

const usePrivateJobPostingRead = (uuid) => {
  const { data, error, mutate } = useSWR(
    uuid ? `/job_postings/private_public/${uuid}/` : null
  );

  return {
    data,
    loading: !data && !error,
    error,
    mutate,
  };
};

export default usePrivateJobPostingRead;
