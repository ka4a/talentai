import { useParams } from 'react-router-dom';

import useSWR from 'swr';

import fetcher from '@swrAPI/fetcher';

const useProposalsRead = () => {
  const { proposalId } = useParams();

  const { data, error, mutate } = useSWR(
    proposalId ? `/proposals/${proposalId}/` : null,
    (url) =>
      fetcher(url, {
        params: {
          extra_fields: 'placement_id,placement_status,placement_approved_at',
        },
      }),
    { refreshInterval: 60_000 }
  );

  return {
    data: data ?? {},
    error,
    loading: !data && !error,
    mutate,
  };
};

export default useProposalsRead;
