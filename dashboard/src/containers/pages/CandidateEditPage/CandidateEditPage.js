import React, { memo } from 'react';
import { useParams } from 'react-router-dom';

import { t } from '@lingui/macro';

import { DefaultPageContainer } from '@components';

import CandidateForm from './components/CandidateForm';

const CandidateEditPage = () => {
  const { candidateId } = useParams();

  const title = candidateId ? t`Edit Candidate Details` : t`Create a Candidate`;

  return (
    <DefaultPageContainer title={title}>
      <CandidateForm title={title} />
    </DefaultPageContainer>
  );
};

export default memo(CandidateEditPage);
