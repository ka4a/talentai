import useSWR from 'swr';

function useInterviewRead(interviewId) {
  const { data, error, mutate } = useSWR(
    interviewId ? `/proposal_interviews/${interviewId}/` : null
  );

  return {
    data: data ?? {},
    error,
    loading: !data && !error,
    mutate,
  };
}

export default useInterviewRead;
