import React, { memo } from 'react';

import { Trans } from '@lingui/macro';

import { Typography } from '@components';
import useGetCandidate from '@swrAPI/hooks/candidates/useGetCandidate';

import Education from './Education';

import styles from '../../CandidateDetailsSection.module.scss';

const EducationDetailsSection = () => {
  const { data: candidate } = useGetCandidate();

  if (!candidate.educationDetails?.length) {
    return null;
  }

  return (
    <div className={styles.wrapper}>
      <div className='d-flex justify-content-between align-items-center'>
        <Typography variant='subheading'>
          <Trans>Education Details</Trans>
        </Typography>
      </div>

      <div className={styles.detailList}>
        {candidate.educationDetails?.map((education, index) => (
          <Education
            key={index}
            title={education.degree}
            company={education.institute}
            endAt={education.dateEnd}
            currentlyPursuing={education.currentlyPursuing}
            department={education.department}
          />
        ))}
      </div>
    </div>
  );
};

export default memo(EducationDetailsSection);
