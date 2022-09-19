import useSWR from 'swr';

const useProposalInterviewPublicRead = (publicUuid) => {
  const { data, error, mutate } = useSWR(
    publicUuid ? `/proposal_interviews/public/${publicUuid}/` : null,
    {
      fallbackData: {},
    }
  );

  return {
    data,
    loading: !data && !error,
    mutate,
  };
};

export default useProposalInterviewPublicRead;
