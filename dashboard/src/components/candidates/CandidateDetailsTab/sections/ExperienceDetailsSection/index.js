import React, { memo } from 'react';

import { Trans } from '@lingui/macro';

import { Typography } from '@components';
import useGetCandidate from '@swrAPI/hooks/candidates/useGetCandidate';

import Experience from './Experience';

import styles from '../../CandidateDetailsSection.module.scss';

const ExperienceDetailsSection = () => {
  const { data: candidate } = useGetCandidate();

  if (!candidate.experienceDetails?.length) {
    return null;
  }

  return (
    <div className={styles.wrapper}>
      <div className='d-flex justify-content-between align-items-center'>
        <Typography variant='subheading'>
          <Trans>Experience Details</Trans>
        </Typography>
      </div>

      <div className={styles.detailList}>
        {candidate.experienceDetails?.map((experience, index) => (
          <Experience
            key={index}
            title={experience.occupation}
            company={experience.company}
            startAt={experience.dateStart}
            endAt={experience.dateEnd}
            description={experience.summary}
            location={experience.location}
            currentlyPursuing={experience.currentlyPursuing}
          />
        ))}
      </div>
    </div>
  );
};

export default memo(ExperienceDetailsSection);
