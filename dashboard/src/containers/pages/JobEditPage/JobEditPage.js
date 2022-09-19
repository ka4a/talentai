import React, { memo } from 'react';
import { Redirect, useParams } from 'react-router-dom';

import { t } from '@lingui/macro';

import { DefaultPageContainer } from '@components';
import { useIsAllowedToOpenJobForm } from '@hooks';

import JobForm from './components/JobForm';

const JobEditPage = () => {
  const { jobId } = useParams();

  const isAllowedToOpenJobForm = useIsAllowedToOpenJobForm();

  const title = jobId ? t`Edit Job Details` : t`Create a Job`;

  return isAllowedToOpenJobForm ? (
    <DefaultPageContainer title={title}>
      <JobForm title={title} />
    </DefaultPageContainer>
  ) : (
    <Redirect to='/' />
  );
};

export default memo(JobEditPage);
