import { useParams } from 'react-router-dom';

import { useProposalsRead, useCandidatesRead } from '@swrAPI';

const useGetCandidate = () => {
  /**
   * candidateId is available on Candidate page
   * proposalId is available on Job page
   */
  const { candidateId, proposalId } = useParams();

  const useGetData = candidateId ? useCandidatesRead : useProposalsRead;

  const { data, mutate } = useGetData();

  if (proposalId) return { data: data.candidate ?? {}, mutate };
  if (candidateId) return { data, mutate };
  return {};
};

export default useGetCandidate;
