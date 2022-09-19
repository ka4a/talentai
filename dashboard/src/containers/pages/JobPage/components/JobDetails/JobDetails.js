import React, { memo } from 'react';

import PropTypes from 'prop-types';

import { WindowBackground, SectionsMenu } from '@components';
import styles from '@styles/form.module.scss';

import {
  Details,
  HiringProcess,
  JobConditions,
  Metadata,
  Requirements,
  Attachments,
} from '../JobDetailsSections';
import { SECTIONS } from './constants';
import PrivateDetails from './components/PrivateDetails';
import PrivateRequirements from './components/PrivateRequirements';

const JobDetails = ({ job, refreshJob }) => (
  <div className={styles.wrapper}>
    <WindowBackground className={styles.formContainerWidePadded}>
      <Details job={job} privatePart={<PrivateDetails job={job} />} />
      <Requirements job={job} privatePart={<PrivateRequirements job={job} />} />
      <JobConditions job={job} />
      <HiringProcess job={job} />
      <Attachments job={job} refreshJob={refreshJob} />
      <Metadata job={job} />
    </WindowBackground>

    <SectionsMenu sections={SECTIONS} />
  </div>
);

JobDetails.propTypes = {
  job: PropTypes.object.isRequired,
  refreshJob: PropTypes.func.isRequired,
};

export default memo(JobDetails);
