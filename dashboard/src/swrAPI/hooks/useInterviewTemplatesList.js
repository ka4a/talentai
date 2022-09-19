import useSWR from 'swr';

const useInterviewTemplatesList = (shouldFetch) => {
  const { data } = useSWR(shouldFetch ? '/interview_templates/' : null, {
    shouldRetryOnError: false,
    revalidateOnFocus: false,
    fallbackData: {
      results: [],
    },
  });

  return data.results;
};

export default useInterviewTemplatesList;
