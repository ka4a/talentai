import React, { memo } from 'react';

import { useGetJob } from '@swrAPI';
import { ReqStatus } from '@components';
import { useScrollToTop } from '@hooks';

import JobPageContent from './components/JobPageContent';

import styles from './JobPage.module.scss';

const JobPage = () => {
  const { data: job, error, loading } = useGetJob();

  useScrollToTop();

  if (!job || error) {
    return (
      <div className={styles.loading}>
        <ReqStatus loading={loading} error={error} />
      </div>
    );
  }

  return (
    <div className='job-page'>
      <JobPageContent />
    </div>
  );
};

export default memo(JobPage);
