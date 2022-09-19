import useSWR from 'swr';

const useFunctionList = () => {
  const { data } = useSWR('/function/', {
    shouldRetryOnError: false,
    revalidateOnFocus: false,
    fallbackData: [],
  });

  return data.map((func) => ({ value: func.id, name: func.title }));
};

export default useFunctionList;
