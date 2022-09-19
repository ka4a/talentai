import useSWR from 'swr';

import fetcher from '@swrAPI/fetcher';

const groupByStage = (statuses) => {
  return statuses.reduce((acc, { group, id, stage, status }) => {
    if (!acc[stage]) acc[stage] = [];

    acc[stage].push({
      value: id,
      label: status,
      group,
    });

    return acc;
  }, {});
};

const fetcherWithOrg = (url, org_id, org_type) =>
  fetcher(url, { params: { org_id, org_type } });

const useOrgProposalStatuses = (orgId, orgType) => {
  const { data } = useSWR(
    ['/data/get_org_proposal_statuses/', orgId, orgType],
    fetcherWithOrg,
    { shouldRetryOnError: false, revalidateOnFocus: false, fallbackData: [] }
  );

  return groupByStage(data);
};

export default useOrgProposalStatuses;
