import React, { memo } from 'react';

import {
  ApplicationCandidates,
  ApplicationInterviews,
  ApplicationJob,
  ApplicationQuestions,
} from '../ProposalApplicationSections';
import StagesPipeline from '../StagesPipeline';
import ApplicationStatusBar from '../ApplicationStatusBar';

import styles from './ProposalApplication.module.scss';

const ProposalApplication = () => (
  <>
    <StagesPipeline />

    <ApplicationStatusBar />

    <div className={styles.wrapper}>
      <ApplicationJob />
      <ApplicationCandidates />
    </div>

    <div className={styles.wrapper}>
      <ApplicationQuestions />
    </div>

    <div className={styles.wrapper}>
      <ApplicationInterviews />
    </div>
  </>
);

export default memo(ProposalApplication);
