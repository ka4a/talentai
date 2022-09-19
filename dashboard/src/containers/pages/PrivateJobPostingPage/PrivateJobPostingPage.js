import React, { memo } from 'react';
import { useParams } from 'react-router-dom';

import { ReqStatus, DefaultPageContainer, PublicOrgTopBar } from '@components';
import { usePrivateJobPostingRead } from '@swrAPI';

import JobPostingPageContent, { POSTING_TYPES } from '../JobPostingPageContent';

const PrivateJobPostingPage = () => {
  const { uuid } = useParams();

  const { data: jobPosting, loading, error } = usePrivateJobPostingRead(uuid);

  if (!jobPosting || error) return <ReqStatus loading={loading} error={error} />;

  const { organization } = jobPosting;

  return (
    <DefaultPageContainer title={jobPosting.title}>
      <PublicOrgTopBar title={organization.name} logo={organization.logo} />
      <JobPostingPageContent
        postingType={POSTING_TYPES.private}
        jobPosting={jobPosting}
      />
    </DefaultPageContainer>
  );
};

export default memo(PrivateJobPostingPage);
