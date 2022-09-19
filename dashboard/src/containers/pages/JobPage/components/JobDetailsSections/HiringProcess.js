import React, { memo } from 'react';

import classnames from 'classnames';
import { t, Trans } from '@lingui/macro';
import PropTypes from 'prop-types';

import { LabeledItem, Typography, FormSection, Badge } from '@components';

import ProposalInterview from '../ProposalInterview';

import styles from './JobDetailsSections.module.scss';

const HiringProcess = ({ job }) => {
  return (
    <FormSection
      id='job-hiring-process'
      titleVariant='subheading'
      title={t`Hiring Process`}
    >
      <div className={styles.rowWrapper}>
        <LabeledItem
          label={t`Hiring Manager`}
          value={job.managers
            ?.map((manager) => `${manager.firstName} ${manager.lastName}`)
            .join(', ')}
        />

        <LabeledItem label={t`Number of Openings`} value={job.openingsCount} />
      </div>

      <hr className={styles.topGap} />

      <div className={classnames([styles.rowWrapper, styles.listNoSpacing])}>
        <div>
          <Typography variant='caption' className={styles.label}>
            Internal Recruiters
          </Typography>

          <ul>
            {job.recruiters.map((el) => (
              <li key={el.id}>
                <Typography>{`${el.firstName} ${el.lastName}`}</Typography>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <Typography variant='caption' className={styles.label}>
            <Trans>Agencies</Trans>
          </Typography>

          <ul>
            {job.agencies.map((agency) => (
              <li key={agency.id}>
                <Typography>{agency.name}</Typography>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <hr />

      <Typography variant='caption' className={styles.skillTitle}>
        <Trans>Hiring Criteria</Trans>
      </Typography>

      <div className={styles.skillsWrapper}>
        {job.hiringCriteria.map((criteria) => (
          <Badge key={criteria.id} text={criteria.name} className={styles.skillBadge} />
        ))}
      </div>

      <hr />

      <div className={styles.listNoSpacing}>
        <Typography
          variant='caption'
          className={classnames([styles.label, styles.topGap])}
        >
          <Trans>Screening Questions</Trans>
        </Typography>

        <ul className={styles.topGap}>
          {job.questions.map((item) => (
            <li key={item.id}>
              <Typography>{item.text}</Typography>
            </li>
          ))}
        </ul>
      </div>

      <hr />

      {job.interviewTemplates.length > 0 && (
        <>
          <Typography variant='subheading'>
            <Trans>Interviews</Trans>
          </Typography>

          {job.interviewTemplates.map((interview) => (
            <ProposalInterview key={interview.id} interview={interview} shortMode />
          ))}
        </>
      )}
    </FormSection>
  );
};

HiringProcess.propTypes = {
  job: PropTypes.object.isRequired,
};

export default memo(HiringProcess);
