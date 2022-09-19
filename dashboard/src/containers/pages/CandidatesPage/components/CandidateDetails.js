import React, { memo } from 'react';

import { useCandidatesRead } from '@swrAPI';
import { DetailsContainer } from '@components';

import Candidate from './Candidate';

const CandidateDetails = () => {
  const { data: candidate, error, loading } = useCandidatesRead();

  return (
    <DetailsContainer
      data={candidate}
      error={error}
      isLoading={loading}
      renderDetails={() => <Candidate />}
    />
  );
};

export default memo(CandidateDetails);
