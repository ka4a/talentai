import useSWR from 'swr';

const useLegalAgreementsRead = (documentType) =>
  useSWR(documentType ? `/legal_agreements/${documentType}` : null, {
    shouldRetryOnError: false,
    revalidateOnFocus: false,
  });

export default useLegalAgreementsRead;
