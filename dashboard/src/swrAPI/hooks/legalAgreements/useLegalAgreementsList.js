import useSWR from 'swr';

const useLegalAgreementsList = () => {
  const { data } = useSWR('/legal_agreements/', {
    shouldRetryOnError: false,
    revalidateOnFocus: false,
    fallbackData: { results: [] },
  });

  const getFileLink = (type) =>
    data.results.find((el) => el.documentType === type)?.file;

  return {
    privacyPolicyLink: getFileLink('pp'),
    termsAndConditionsLink: getFileLink('tandc'),
  };
};

export default useLegalAgreementsList;
