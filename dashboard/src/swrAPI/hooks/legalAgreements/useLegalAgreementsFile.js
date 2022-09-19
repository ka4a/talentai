import { useSelector } from 'react-redux';

import useSWR from 'swr';

import fetcher from '@swrAPI/fetcher';

const useLegalAgreementsFile = (documentType) => {
  const isAuthenticated = useSelector((state) => state.user.isAuthenticated);

  const { data } = useSWR(
    isAuthenticated ? `/legal_agreements/${documentType}/file` : null,
    (url) => fetcher(url, { responseType: 'blob' }),
    {
      shouldRetryOnError: false,
      revalidateOnFocus: false,
    }
  );

  return { data };
};

export default useLegalAgreementsFile;
